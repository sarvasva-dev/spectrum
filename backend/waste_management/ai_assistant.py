"""
CleanLoop AI Citizen Assistant
==============================
Conversational assistant powering the /ai/ page.

Architecture (security-first):
  - The LLM (Sarvam AI, free tier key in .env) NEVER talks to the database,
    never executes code, and NEVER sees passwords or API keys.
  - Django is the sole authority: every read/write below uses deterministic
    ORM queries scoped to request.user (citizens can only see their own data).
  - Conversation state is a small whitelisted JSON dict held by the browser
    and echoed back on each turn; it never contains passwords or raw history.

Public API:
    run_ai_chat(request, message, state) -> dict
    provider_available() -> bool
"""

import os
import json
import logging
import re
from datetime import date, timedelta

import requests

from django.db.models import Q
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils import timezone

from .models import Complaint, ComplaintUpdate, PickupRequest, UserProfile
from .forms import CitizenRegistrationForm

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Provider configuration (Sarvam AI - free tier, server-side only)
# ---------------------------------------------------------------------------

SARVAM_API_URL = "https://api.sarvam.ai/v1/chat/completions"
SARVAM_MODEL = "sarvam-105b"   # 'sarvam-m' is deprecated upstream
LLM_TIMEOUT_SECONDS = 12

MAIN_MENU_ACTIONS = [
    "🗑 Report Waste",
    "🚛 Request Pickup",
    "📍 Track Complaint",
    "📦 Track Pickup",
    "📋 My Complaints",
    "📋 My Pickups",
    "♻ Waste Guide",
]

ISSUE_TYPES = [
    "Overflowing Bin",
    "Garbage on Road",
    "Illegal Dumping",
    "Missed Collection",
    "Improper Segregation",
    "Other",
]

ISSUE_TYPE_MAP = {
    "overflowing bin": "OVERFLOWING_BIN",
    "garbage on road": "GARBAGE_ON_ROAD",
    "illegal dumping": "ILLEGAL_DUMPING",
    "missed collection": "MISSED_COLLECTION",
    "improper segregation": "IMPROPER_SEGREGATION",
    "other": "OTHER",
}

PICKUP_CATEGORIES = [
    "Organic", "Plastic", "Paper", "Glass", "Metal", "E-Waste", "General", "Other",
]

PICKUP_CATEGORY_MAP = {
    "organic": "ORGANIC", "plastic": "PLASTIC", "paper": "PAPER", "glass": "GLASS",
    "metal": "METAL", "e-waste": "E_WASTE", "ewaste": "E_WASTE",
    "general": "GENERAL", "other": "OTHER",
}

PICKUP_TIME_SLOTS = [
    "Morning (08:00 AM - 11:00 AM)",
    "Midday (11:00 AM - 02:00 PM)",
    "Afternoon (02:00 PM - 05:00 PM)",
    "Evening (05:00 PM - 07:00 PM)",
]

MAX_STATE_BYTES = 4096  # refuse runaway state payloads


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _sanitize_state(state):
    """Whitelist + cap the client-echoed conversation state."""
    if not isinstance(state, dict):
        return {}
    allowed = {
        "intent", "step", "prev",
        "issue_type", "description", "latitude", "longitude", "landmark",
        "location", "photo_attached",
        "pickup_category", "quantity", "pickup_date", "pickup_time",
        "pickup_address", "notes",
        "auth_username", "auth_name", "auth_email", "auth_phone", "auth_address",
    }
    clean = {}
    for key in allowed:
        if key in state:
            value = state[key]
            if isinstance(value, (str, int, float, bool)) or value is None:
                clean[key] = value
    # Hard safety: a password must never ride along in state.
    clean.pop("password", None)
    clean.pop("auth_password", None)
    return clean


def _sanitize_recent(recent):
    """Cap the optional recent-message context used for NLU."""
    if not isinstance(recent, list):
        return []
    out = []
    for item in recent[-4:]:
        if isinstance(item, str):
            text = item.strip()[:120]
            if text:
                out.append(text)
    return out


def _clamp_text(value, max_len=2000):
    if value is None:
        return ""
    return str(value).strip()[:max_len]


def _fmt_date(value):
    return value.strftime("%d %b %Y") if value else "-"


def _complaint_card(c):
    return {
        "kind": "complaint",
        "id": c.complaint_id,
        "title": c.get_issue_type_display(),
        "status": c.get_status_display(),
        "priority": c.get_priority_display(),
        "date": _fmt_date(timezone.localtime(c.created_at)) if c.created_at else "",
        "location": (c.location or c.address or "")[:80],
    }


def _pickup_card(p):
    return {
        "kind": "pickup",
        "id": p.pickup_id,
        "title": p.get_waste_category_display(),
        "status": p.get_status_display(),
        "date": _fmt_date(p.preferred_date),
        "location": (p.pickup_address or "").split("\n")[0][:80],
    }


def _issue_label_to_code(label):
    return ISSUE_TYPE_MAP.get(_clamp_text(label, 60).lower())


def _pickup_label_to_code(label):
    return PICKUP_CATEGORY_MAP.get(_clamp_text(label, 60).lower())


def _match_issue_code_freeform(text):
    low = text.lower()
    table = [("overflow", "OVERFLOWING_BIN"), ("bin", "OVERFLOWING_BIN"),
             ("garbage", "GARBAGE_ON_ROAD"), ("kachra", "GARBAGE_ON_ROAD"),
             ("road", "GARBAGE_ON_ROAD"), ("dump", "ILLEGAL_DUMPING"),
             ("illegal", "ILLEGAL_DUMPING"), ("missed", "MISSED_COLLECTION"),
             ("segregat", "IMPROPER_SEGREGATION")]
    for word, code in table:
        if word in low:
            return code
    return None


def _norm_date_str(raw):
    """Accept 'today', 'tomorrow', 'Tomorrow (01 Oct)', 'YYYY-MM-DD', 'DD-MM-YYYY' or '01 Oct'."""
    raw = _clamp_text(raw, 40).lower().strip()
    if not raw:
        return None
    today = timezone.localdate()
    if "today" in raw or "aaj" in raw:
        return today.isoformat()
    if "tomorrow" in raw or "kal" in raw:
        return (today + timedelta(days=1)).isoformat()

    m = re.search(r"\b(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})\b", raw)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
        except ValueError:
            pass

    m = re.search(r"\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})\b", raw)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat()
        except ValueError:
            pass

    months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    pattern = r"\b(\d{1,2})\s+(" + "|".join(months) + r")(?:\s+(\d{4}))?\b"
    m = re.search(pattern, raw)
    if m:
        try:
            day = int(m.group(1))
            month_str = m.group(2)
            month_num = months.index(month_str) + 1
            year = int(m.group(3)) if m.group(3) else today.year
            return date(year, month_num, day).isoformat()
        except ValueError:
            pass

    return None


def _parse_latlng(message):
    """Parse 'lat,lng' from GPS/map callbacks. Returns (lat, lng) or None."""
    parts = _clamp_text(message, 60).split(",")
    if len(parts) != 2:
        return None
    try:
        lat = float(parts[0].strip())
        lng = float(parts[1].strip())
    except (ValueError, TypeError):
        return None
    if not (-90 <= lat <= 90 and -180 <= lng <= 180) or (lat == 0 and lng == 0):
        return None
    return lat, lng


def _resolve_user_complaint(user, query):
    """Deterministic lookup of one of the user's complaints by ID or keyword."""
    qs = Complaint.objects.filter(user=user)
    query = _clamp_text(query, 60)
    if not query:
        return qs.order_by("-created_at").first()
    exact = qs.filter(complaint_id__iexact=query).first()
    if exact:
        return exact
    low = query.lower()
    if low in ("last", "latest", "recent", "recent one", "last one", "latest one"):
        return qs.order_by("-created_at").first()
    if low in ("yesterday", "yesterday's complaint", "kal ki", "kal wali", "kal wali complaint"):
        yesterday = timezone.localdate() - timedelta(days=1)
        return qs.filter(created_at__date=yesterday).order_by("-created_at").first()
    if low in ("unresolved", "open", "pending", "active"):
        return qs.exclude(status="RESOLVED").order_by("-created_at").first()
    if low in ("resolved", "resolved complaints"):
        return qs.filter(status="RESOLVED").order_by("-created_at").first()
    return qs.filter(
        Q(complaint_id__icontains=query) | Q(location__icontains=query)
        | Q(description__icontains=query) | Q(issue_type__icontains=query)
    ).first()


def _resolve_user_pickup(user, query):
    qs = PickupRequest.objects.filter(user=user)
    query = _clamp_text(query, 60)
    if not query:
        return qs.order_by("-created_at").first()
    exact = qs.filter(pickup_id__iexact=query).first()
    if exact:
        return exact
    low = query.lower()
    if low in ("last", "latest", "recent", "last one", "last pickup"):
        return qs.order_by("-created_at").first()
    code = _pickup_label_to_code(low)
    if code:
        by_cat = qs.filter(waste_category=code).order_by("-created_at").first()
        if by_cat:
            return by_cat
    return qs.filter(
        Q(pickup_id__icontains=query) | Q(pickup_address__icontains=query)
        | Q(waste_category__icontains=query)
    ).first()


def _reverse_geocode(lat, lng):
    """Best-effort Nominatim reverse geocode; never blocks the flow."""
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"format": "json", "lat": lat, "lon": lng},
            headers={"User-Agent": "CleanLoop/1.0 (citizen assistant)"},
            timeout=5,
        )
        data = resp.json()
        a = data.get("address", {})
        parts = []
        for key in ("road", "suburb", "city_district", "city", "town", "village", "state"):
            if a.get(key):
                parts.append(a[key])
        return ", ".join(parts[:3]) or data.get("display_name", "")[:120]
    except (requests.RequestException, ValueError, KeyError):
        return None


# ---------------------------------------------------------------------------
# Reply builder
# ---------------------------------------------------------------------------

def _reply(message, intent, step, actions=None, state=None, **extra):
    payload = {
        "ok": True,
        "message": message,
        "intent": intent,
        "step": step,
        "actions": actions or [],
        "state": state or {},
        "provider_available": provider_available(),
    }
    payload.update(extra)
    return payload


def _provider_down():
    """Friendly provider-outage fallback; CleanLoop self-service still works."""
    return _reply(
        "AI assistance is temporarily unavailable, but CleanLoop's self-service actions still work.",
        "MAIN_MENU", "START", actions=MAIN_MENU_ACTIONS)


# ---------------------------------------------------------------------------
# LLM provider layer (server-side only; no DB access, no secrets in prompt)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are the intent router inside CleanLoop, an Indian smart waste management "
    "citizen app. Citizens write in English, Hindi, Hinglish or Roman Hindi.\n"
    "Classify the citizen's LAST message into exactly one intent and reply with ONLY "
    "minified JSON, no markdown, no explanation:\n"
    '{"intent":"GREETING|REPORT_COMPLAINT|REQUEST_PICKUP|TRACK_COMPLAINT|TRACK_PICKUP|'
    'MY_COMPLAINTS|MY_PICKUPS|AWARENESS|HELP|CANCEL|UNKNOWN"}\n'
    "Meanings: REPORT_COMPLAINT = reporting a garbage/waste problem somewhere; "
    "REQUEST_PICKUP = wants waste collected from home; TRACK_COMPLAINT = asks status of a "
    "complaint (may include an ID like WM-2026-0025); TRACK_PICKUP = asks status of a pickup "
    "(may include an ID like PK-2026-0012); MY_COMPLAINTS = list my past complaints; "
    "MY_PICKUPS = list my past pickups; AWARENESS = how to dispose/segregate something, "
    "waste knowledge; HELP = what can you do; CANCEL = stop/abort current flow.\n"
    "If the message is only small talk or unclear, use UNKNOWN.\n"
    "Examples:\n"
    'mujhe complaint karni hai -> {"intent":"REPORT_COMPLAINT"}\n'
    'road pe kachra pada hai -> {"intent":"REPORT_COMPLAINT"}\n'
    'overflowing dustbin hai -> {"intent":"REPORT_COMPLAINT"}\n'
    'pickup chahiye -> {"intent":"REQUEST_PICKUP"}\n'
    'mera pickup kab aayega -> {"intent":"TRACK_PICKUP"}\n'
    'WM-2026-0025 ka status batao -> {"intent":"TRACK_COMPLAINT"}\n'
    'meri last complaint ka status -> {"intent":"TRACK_COMPLAINT"}\n'
    'meri complaints dikhao -> {"intent":"MY_COMPLAINTS"}\n'
    'mere pickups dikhao -> {"intent":"MY_PICKUPS"}\n'
    'plastic waste ka kya karun -> {"intent":"AWARENESS"}\n'
    'kal wali complaint dikhao -> {"intent":"TRACK_COMPLAINT"}\n'
    'cancel kar do -> {"intent":"CANCEL"}'
)


def provider_available():
    return bool(os.environ.get("SARVAM_API_KEY"))


def llm_classify_intent(message, recent):
    """Ask Sarvam to classify the message. Returns intent string or None on failure."""
    api_key = os.environ.get("SARVAM_API_KEY")
    if not api_key:
        return None
    context = "\n".join(recent[-4:])
    user_content = (
        f"Earlier messages:\n{context}\n\nLast message: {message}" if context else message
    )
    try:
        resp = requests.post(
            SARVAM_API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": SARVAM_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                "temperature": 0.1,
            },
            timeout=LLM_TIMEOUT_SECONDS,
        )
        if resp.status_code != 200:
            logger.warning("Sarvam classify failed: HTTP %s", resp.status_code)
            return None
        content = resp.json()["choices"][0]["message"]["content"]
        match = re.search(r"\{[^}]*\}", content, re.DOTALL)
        if not match:
            return None
        intent = json.loads(match.group(0)).get("intent", "UNKNOWN")
        allowed = {
            "GREETING", "REPORT_COMPLAINT", "REQUEST_PICKUP", "TRACK_COMPLAINT",
            "TRACK_PICKUP", "MY_COMPLAINTS", "MY_PICKUPS", "AWARENESS", "HELP",
            "CANCEL", "UNKNOWN",
        }
        return intent if intent in allowed else None
    except (requests.RequestException, KeyError, ValueError, json.JSONDecodeError) as exc:
        logger.warning("Sarvam classify error: %s", exc)
        return None


def llm_answer_awareness(question):
    """Awareness answers grounded in CleanLoop's segregation rules."""
    api_key = os.environ.get("SARVAM_API_KEY")
    if not api_key:
        return None
    grounding = (
        "Answer as CleanLoop's waste assistant using ONLY these CleanLoop rules:\n"
        "- GREEN BIN: organic / wet waste (food scraps, peels, garden waste).\n"
        "- BLUE BIN: clean & dry recyclables (plastic bottles, paper, cardboard, metal, glass).\n"
        "- YELLOW/TEAL stream: wrappers, multilayer plastics, sanitary waste where segregated "
        "collection exists.\n"
        "- RED/BLACK: hazardous & e-waste (batteries, electronics, bulbs, medicines) - hand to "
        "special collection; CleanLoop supports doorstep E-Waste pickup via Request Pickup.\n"
        "- Rinse recyclables, keep them dry, flatten cardboard. Never mix wet and dry waste.\n"
        "- Citizens can request doorstep pickup from CleanLoop for bulk or segregated waste.\n"
        "Keep the answer under 90 words, friendly, plain text (no markdown)."
    )
    try:
        resp = requests.post(
            SARVAM_API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": SARVAM_MODEL,
                "messages": [
                    {"role": "system", "content": grounding},
                    {"role": "user", "content": _clamp_text(question, 500)},
                ],
                "temperature": 0.4,
            },
            timeout=LLM_TIMEOUT_SECONDS,
        )
        if resp.status_code != 200:
            return None
        return _clamp_text(resp.json()["choices"][0]["message"]["content"], 900)
    except (requests.RequestException, KeyError, ValueError) as exc:
        logger.warning("Sarvam awareness error: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_ai_chat(request, message, state):
    """Main router. Called by waste_management.views.api_ai_chat_view."""
    message = _clamp_text(message, 2000)
    state = _sanitize_state(state)
    if len(json.dumps(state)) > MAX_STATE_BYTES:
        state = {}
    recent = _sanitize_recent(state.pop("recent", None) or [])
    state.pop("recent", None)

    intent = state.get("intent", "")
    step = state.get("step", "START")

    # --- Unauthenticated citizens: auth flows only ---
    if not request.user.is_authenticated:
        return _handle_auth(request, message, state)

    # --- Authenticated: global cancel ---
    if _is_cancel(message):
        return _reply("No problem — I've cancelled that. Nothing was saved.",
                      "MAIN_MENU", "START", actions=MAIN_MENU_ACTIONS, state={})

    # Browser sentinel events (GPS result / map selection / photo done)
    if message.startswith("__GPS_COORDS__:"):
        coords = _parse_latlng(message.split(":", 1)[1])
        if coords is None:
            state["step"] = "GPS_RETRY" if intent == "REPORT_COMPLAINT" else "PICK_GPS_RETRY"
            return _reply("I couldn't access your location.", intent or "MAIN_MENU",
                          state["step"],
                          actions=["📍 Try Again", "🗺 Choose on Map", "✏ Enter Address", "Cancel"],
                          state=state)
        state["latitude"], state["longitude"] = coords
        return _gps_coords_received(request, state, coords)
    if message == "__GPS_FAIL__":
        state["step"] = "GPS_RETRY" if intent == "REPORT_COMPLAINT" else "PICK_GPS_RETRY"
        return _reply("I couldn't access your location.", intent or "MAIN_MENU", state["step"],
                      actions=["📍 Try Again", "🗺 Choose on Map", "✏ Enter Address", "Cancel"],
                      state=state)
    if message.startswith("__MAP_COORDS__:"):
        coords = _parse_latlng(message.split(":", 1)[1])
        if coords is None:
            state["step"] = "MAP_RETRY" if intent == "REPORT_COMPLAINT" else "PICK_MAP_RETRY"
            return _reply("That map selection didn't come through. Want to try again?",
                          intent or "MAIN_MENU", state["step"],
                          actions=["🗺 Choose on Map", "📍 Use Current Location", "✏ Enter Address", "Cancel"],
                          state=state, map_request=True)
        state["latitude"], state["longitude"] = coords
        return _map_coords_received(request, state, coords)
    if message == "__PHOTO_DONE__":
        state["photo_attached"] = True
        return _complaint_review(state)

    # In-progress multi-step flows take priority over quick actions & NLU
    if intent == "REPORT_COMPLAINT" and step not in ("START", ""):
        return _complaint_flow(request, message, state)
    if intent == "REQUEST_PICKUP" and step not in ("START", ""):
        return _pickup_flow(request, message, state)
    if intent == "TRACK_COMPLAINT" and step == "AWAIT_ID":
        if _clamp_text(message, 30).lower() in ("my complaints", "📋 my complaints"):
            return _list_complaints(request)
        return _track_complaint_by_id(request, message)
    if intent == "TRACK_PICKUP" and step == "AWAIT_ID":
        if _clamp_text(message, 30).lower() in ("my pickups", "📋 my pickups"):
            return _list_pickups(request)
        return _track_pickup_by_id(request, message)

    # Quick-button chip presses short-circuit NLU
    routed = _route_quick_action(request, message)
    if routed is not None:
        return routed

    # Natural-language routing: deterministic rules first, LLM second
    rule_intent = _rule_based_intent(message)
    chosen = rule_intent
    if not chosen and message:
        chosen = llm_classify_intent(message, recent)

    # Ambiguous free text during a flow? The LLM may classify short answers
    # like 'E-Waste' or 'Morning' as UNKNOWN; fall back to the active flow.
    if chosen in (None, "UNKNOWN", ""):
        if not message:
            return _greeting(request)
        if intent == "REPORT_COMPLAINT" and step not in ("START", ""):
            return _complaint_flow(request, message, state)
        if intent == "REQUEST_PICKUP" and step not in ("START", ""):
            return _pickup_flow(request, message, state)
        return _fallback_message()

    return _dispatch_intent(request, chosen, message)


def _gps_coords_received(request, state, coords):
    """Shared handler when the browser delivers GPS coordinates."""
    addr = _reverse_geocode(coords[0], coords[1])
    in_pickup = state.get("intent") == "REQUEST_PICKUP"
    if in_pickup:
        state["pickup_address"] = addr or _profile_address(request) \
            or f"GPS ({coords[0]:.5f}, {coords[1]:.5f})"
        state["step"] = "PICK_DATE"
        return _pickup_date_question(state, detected=True)
    state["location"] = addr or f"GPS ({coords[0]:.5f}, {coords[1]:.5f})"
    state["step"] = "LANDMARK"
    return _reply(f"Location detected ✓ <i>{state['location']}</i><br>Any nearby landmark?",
                  "REPORT_COMPLAINT", "LANDMARK",
                  actions=["Add Landmark", "Skip", "Cancel"], state=state)


def _map_coords_received(request, state, coords):
    """Shared handler when the citizen pins a spot on the map."""
    addr = _reverse_geocode(coords[0], coords[1])
    in_pickup = state.get("intent") == "REQUEST_PICKUP"
    if in_pickup:
        state["pickup_address"] = addr or _profile_address(request) \
            or f"Pinned ({coords[0]:.5f}, {coords[1]:.5f})"
        state["step"] = "PICK_DATE"
        return _pickup_date_question(state, detected=True)
    state["location"] = addr or f"Pinned ({coords[0]:.5f}, {coords[1]:.5f})"
    state["step"] = "LANDMARK"
    return _reply(f"Got it — I've marked your location: <i>{state['location']}</i>.<br>Any nearby landmark?",
                  "REPORT_COMPLAINT", "LANDMARK",
                  actions=["Add Landmark", "Skip", "Cancel"], state=state)


def _greeting(request):
    name = request.user.first_name or request.user.username
    return _reply(
        f"Hi {name} 👋<br>What would you like to do today?",
        "MAIN_MENU", "START", actions=MAIN_MENU_ACTIONS, state={})


def _is_cancel(message):
    return _clamp_text(message, 20).strip().upper() in ("CANCEL", "❌ CANCEL", "STOP", "EXIT", "QUIT")


# ---------------------------------------------------------------------------
# Quick actions & intents
# ---------------------------------------------------------------------------

_QUICK_ACTION_MAP = {
    "🗑 report waste": "REPORT_COMPLAINT",
    "report waste": "REPORT_COMPLAINT",
    "report another": "REPORT_COMPLAINT",
    "🚛 request pickup": "REQUEST_PICKUP",
    "request pickup": "REQUEST_PICKUP",
    "request another": "REQUEST_PICKUP",
    "📍 track complaint": "TRACK_COMPLAINT",
    "track complaint": "TRACK_COMPLAINT",
    "📦 track pickup": "TRACK_PICKUP",
    "track pickup": "TRACK_PICKUP",
    "📋 my complaints": "MY_COMPLAINTS",
    "my complaints": "MY_COMPLAINTS",
    "📋 my pickups": "MY_PICKUPS",
    "my pickups": "MY_PICKUPS",
    "♻ waste guide": "AWARENESS",
    "waste guide": "AWARENESS",
    "wet vs dry waste": "AWARENESS",
    "plastic disposal": "AWARENESS",
    "e-waste": "AWARENESS",
    "❓ help": "HELP",
    "help": "HELP",
}


def _route_quick_action(request, message):
    low = _clamp_text(message, 60).lower().strip()
    code = _QUICK_ACTION_MAP.get(low)
    if code is None:
        return None
    return _dispatch_intent(request, code, message)


def _start_complaint():
    return _reply(
        "What type of waste issue are you reporting?",
        "REPORT_COMPLAINT", "ISSUE_TYPE",
        actions=ISSUE_TYPES + ["Cancel"],
        state={"intent": "REPORT_COMPLAINT", "step": "ISSUE_TYPE"})


def _start_pickup():
    return _reply(
        "Which category of waste needs to be picked up?",
        "REQUEST_PICKUP", "PICK_CATEGORY",
        actions=PICKUP_CATEGORIES + ["Cancel"],
        state={"intent": "REQUEST_PICKUP", "step": "PICK_CATEGORY"})


def _start_track_complaint():
    return _reply(
        "Sure — what's the complaint ID? (e.g. WM-2026-0025)<br>"
        "You can also say <i>my last complaint</i>.",
        "TRACK_COMPLAINT", "AWAIT_ID",
        actions=["My Complaints", "Cancel"],
        state={"intent": "TRACK_COMPLAINT", "step": "AWAIT_ID"})


def _start_track_pickup():
    return _reply(
        "Sure — what's the pickup ID? (e.g. PK-2026-0012)<br>"
        "You can also say <i>my last pickup</i>.",
        "TRACK_PICKUP", "AWAIT_ID",
        actions=["My Pickups", "Cancel"],
        state={"intent": "TRACK_PICKUP", "step": "AWAIT_ID"})


def _reply_help():
    return _reply(
        "I'm CleanLoop's citizen assistant. I can help you:<br>"
        "• 🗑 Report a waste issue (with GPS / map / photo)<br>"
        "• 🚛 Request a doorstep pickup<br>"
        "• 📍 Track any complaint's live status<br>"
        "• 📦 Track a pickup<br>"
        "• 📋 Show your complaints & pickups<br>"
        "• ♻ Answer waste-disposal questions<br><br>"
        "Try: <i>mujhe complaint karni hai</i> or <i>meri last complaint ka status?</i>",
        "MAIN_MENU", "START", actions=MAIN_MENU_ACTIONS, state={})


def _dispatch_intent(request, intent, message):
    low = _clamp_text(message, 60).lower().strip()
    if intent == "GREETING":
        return _greeting(request)
    if intent == "REPORT_COMPLAINT":
        return _start_complaint()
    if intent == "REQUEST_PICKUP":
        return _start_pickup()
    if intent == "TRACK_COMPLAINT":
        if low in ("track complaint", "📍 track complaint"):
            return _start_track_complaint()
        return _complaint_status_lookup(request, message)
    if intent == "TRACK_PICKUP":
        if low in ("track pickup", "📦 track pickup"):
            return _start_track_pickup()
        return _pickup_status_lookup(request, message)
    if intent == "MY_COMPLAINTS":
        return _list_complaints(request)
    if intent == "MY_PICKUPS":
        return _list_pickups(request)
    if intent == "AWARENESS":
        return _awareness_answer(message)
    if intent == "HELP":
        return _reply_help()
    if intent == "CANCEL":
        return _reply("No problem. What would you like to do?", "MAIN_MENU", "START",
                      actions=MAIN_MENU_ACTIONS, state={})
    return _fallback_message()


def _fallback_message():
    if not provider_available():
        return _provider_down()
    return _reply(
        "I didn't quite catch that. I can help you report waste, request a pickup, "
        "track complaints or pickups, or answer waste-disposal questions.",
        "MAIN_MENU", "START", actions=MAIN_MENU_ACTIONS, state={})


# ---------------------------------------------------------------------------
# Rule-based fast intent detection (works even if provider is down)
# ---------------------------------------------------------------------------

_RULE_PATTERNS = [
    (r"^(hi+|hello+|hey+|namaste|namaskar|salam|good (morning|afternoon|evening))\b", "GREETING"),
    (r"(complaint karni|complaint karna|complaint darj|kachra report|report (waste|garbage|a complaint)|shikayat)", "REPORT_COMPLAINT"),
    (r"(kachra pada|garbage (on|is|lies)|overflowing|dustbin (is |hai |full)|trash on|safai nahi)", "REPORT_COMPLAINT"),
    (r"(pickup chahiye|pickup karna|pickup request hai|request (a |the )?pickup|pickup karwana)", "REQUEST_PICKUP"),
    (r"(pk-\d{4}-\d{3,})", "TRACK_PICKUP"),
    (r"(wm-\d{4}-\d{3,})", "TRACK_COMPLAINT"),
    (r"(mera pickup|mere pickup).*(kab|status|kahan)|pickup (ka |kab |status)", "TRACK_PICKUP"),
    (r"(complaints? dikhao|meri complaints|my complaints|complaint list|saari complaints|kitne complaints.*(hue|resolve))", "MY_COMPLAINTS"),
    (r"(pickups? dikhao|mere pickups|my pickups|pickup list|pickup requests dikhao)", "MY_PICKUPS"),
    (r"(last complaint|latest complaint|complaint ka status|complaint ka kya hua|ka status|kya hua)", "TRACK_COMPLAINT"),
    (r"(kaise dispose|kya karun|kaise phenk|kahan (dun|dale|dalun)|disposal|segregat|recycl|waste guide|wet (vs|and) dry|plastic|e-?waste|awareness)", "AWARENESS"),
    (r"^(help|madad|what can you do|kya kar sakte)\b", "HELP"),
    (r"^(cancel|band karo|ruk jao|chhodo|exit|quit)\b", "CANCEL"),
]


def _rule_based_intent(message):
    low = _clamp_text(message, 300).lower()
    if not low:
        return None
    for pattern, intent in _RULE_PATTERNS:
        if re.search(pattern, low):
            return intent
    return None


# ---------------------------------------------------------------------------
# Tracking / history (deterministic DB reads, always request.user-scoped)
# ---------------------------------------------------------------------------

STATUS_STEPS_COMPLAINT = ["Pending", "Assigned", "In Progress", "Resolved"]
STATUS_STEPS_PICKUP = ["Requested", "Assigned", "Picked Up", "Completed"]


def _complaint_status_payload(complaint):
    if complaint is None:
        return _reply(
            "I couldn't find that complaint in your records. Double-check the ID "
            "(format <b>WM-YYYY-NNNN</b>) or browse your complaints below.",
            "MAIN_MENU", "START",
            actions=["My Complaints", "Report Waste", "Cancel"], state={})

    status_display = complaint.get_status_display()
    timeline = [
        {"status": u.status.replace("_", " ").title(), "note": u.note[:140],
         "date": _fmt_date(timezone.localtime(u.created_at))}
        for u in complaint.timeline_updates.all()[:6]
    ]
    latest_note = timeline[-1]["note"] if timeline else ""
    card = _complaint_card(complaint)
    card["status_step"] = STATUS_STEPS_COMPLAINT.index(status_display) \
        if status_display in STATUS_STEPS_COMPLAINT else 0
    card["status_steps"] = STATUS_STEPS_COMPLAINT
    card["timeline"] = timeline
    card["latest_note"] = latest_note
    card["description"] = complaint.description[:200]
    card["assigned_crew"] = complaint.assigned_crew or ""
    return _reply(
        f"📍 <b>{complaint.complaint_id}</b> — {complaint.get_issue_type_display()}<br>"
        f"Status: <b>{status_display}</b> • Priority: {complaint.get_priority_display()}<br>"
        f"Filed: {_fmt_date(timezone.localtime(complaint.created_at))}"
        + (f"<br>Latest update: {latest_note}" if latest_note else ""),
        "MAIN_MENU", "START",
        actions=["My Complaints", "Report Waste", "Cancel"], state={},
        cards=[card])


def _pickup_status_payload(pickup):
    if pickup is None:
        return _reply(
            "I couldn't find that pickup request in your records. Check the ID "
            "(format <b>PK-YYYY-NNNN</b>) or view your pickups below.",
            "MAIN_MENU", "START",
            actions=["My Pickups", "Request Pickup", "Cancel"], state={})
    status_display = pickup.get_status_display()
    card = _pickup_card(pickup)
    card["status_step"] = STATUS_STEPS_PICKUP.index(status_display) \
        if status_display in STATUS_STEPS_PICKUP else 0
    card["status_steps"] = STATUS_STEPS_PICKUP
    card["quantity"] = pickup.quantity
    card["time"] = pickup.preferred_time
    card["notes"] = (pickup.notes or "")[:140]
    card["assigned_vehicle"] = pickup.assigned_vehicle or ""
    return _reply(
        f"📦 <b>{pickup.pickup_id}</b> — {pickup.get_waste_category_display()}<br>"
        f"Status: <b>{status_display}</b><br>"
        f"Preferred: {_fmt_date(pickup.preferred_date)} • {pickup.preferred_time}",
        "MAIN_MENU", "START",
        actions=["My Pickups", "Request Pickup", "Cancel"], state={},
        cards=[card])


def _track_complaint_by_id(request, message):
    complaint = _resolve_user_complaint(request.user, message)
    return _complaint_status_payload(complaint)


def _track_pickup_by_id(request, message):
    pickup = _resolve_user_pickup(request.user, message)
    return _pickup_status_payload(pickup)


def _complaint_status_lookup(request, message):
    """'WM-2026-0025 ka status batao' / 'meri last complaint ka status?' / 'kal wali'"""
    low = _clamp_text(message, 200).lower()
    m = re.search(r"(wm-\d{4}-\d{3,})", low)
    if m:
        complaint = Complaint.objects.filter(user=request.user, complaint_id__iexact=m.group(1)).first()
        return _complaint_status_payload(complaint)
    if "kal" in low or "yesterday" in low:
        yesterday = timezone.localdate() - timedelta(days=1)
        complaint = Complaint.objects.filter(user=request.user, created_at__date=yesterday) \
            .order_by("-created_at").first()
        if complaint:
            return _complaint_status_payload(complaint)
    complaint = _resolve_user_complaint(request.user, message)
    if complaint is None:
        complaint = Complaint.objects.filter(user=request.user).order_by("-created_at").first()
    return _complaint_status_payload(complaint)


def _pickup_status_lookup(request, message):
    low = _clamp_text(message, 200).lower()
    m = re.search(r"(pk-\d{4}-\d{3,})", low)
    if m:
        pickup = PickupRequest.objects.filter(user=request.user, pickup_id__iexact=m.group(1)).first()
        return _pickup_status_payload(pickup)
    pickup = _resolve_user_pickup(request.user, message)
    return _pickup_status_payload(pickup)


def _list_complaints(request):
    qs = Complaint.objects.filter(user=request.user)[:8]
    if not qs:
        return _reply(
            "You haven't filed any complaints yet. 🗑<br>Want to report a waste issue now?",
            "MAIN_MENU", "START",
            actions=["Report Waste", "Waste Guide", "Cancel"], state={})
    cards = [_complaint_card(c) for c in qs]
    total = Complaint.objects.filter(user=request.user).count()
    resolved = Complaint.objects.filter(user=request.user, status="RESOLVED").count()
    lines = "<br>".join(
        f"• <b>{c.complaint_id}</b> — {c.get_issue_type_display()} • <b>{c.get_status_display()}</b>"
        f" • {_fmt_date(timezone.localtime(c.created_at))}"
        for c in qs
    )
    return _reply(
        f"📋 <b>Your recent complaints</b> ({total} total, {resolved} resolved)<br>{lines}",
        "MAIN_MENU", "START",
        actions=["Report Waste", "Track Complaint", "My Pickups", "Cancel"], state={},
        cards=cards)


def _list_pickups(request):
    qs = PickupRequest.objects.filter(user=request.user)[:8]
    if not qs:
        return _reply(
            "You have no pickup requests yet. 🚛<br>Want to schedule one now?",
            "MAIN_MENU", "START",
            actions=["Request Pickup", "Report Waste", "Cancel"], state={})
    cards = [_pickup_card(p) for p in qs]
    lines = "<br>".join(
        f"• <b>{p.pickup_id}</b> — {p.get_waste_category_display()} • <b>{p.get_status_display()}</b>"
        f" • {_fmt_date(p.preferred_date)}"
        for p in qs
    )
    return _reply(
        f"📦 <b>Your pickup requests</b><br>{lines}",
        "MAIN_MENU", "START",
        actions=["Request Pickup", "Track Pickup", "My Complaints", "Cancel"], state={},
        cards=cards)


# ---------------------------------------------------------------------------
# Awareness
# ---------------------------------------------------------------------------

AWARENESS_SNIPPETS = [
    (("wet", "dry"), "🌱 <b>Wet vs Dry segregation</b><br>"
     "• Wet/organic waste (food scraps, peels) → <b>green bin</b>.<br>"
     "• Dry recyclables (plastic bottles, paper, metal, glass) → <b>blue bin</b>, rinsed and dry.<br>"
     "• Never mix them — mixed waste is almost impossible to recycle."),
    (("plastic",), "🥤 <b>Plastic waste</b><br>"
     "• Rinse bottles/containers, put them in the <b>blue bin</b> (dry).<br>"
     "• Wrappers and multilayer plastics go to the segregated dry-waste stream.<br>"
     "• Bulk plastic? CleanLoop can pick it up — tap <b>Request Pickup</b>."),
    (("e-waste",), "🔋 <b>E-Waste</b><br>"
     "• Batteries, bulbs, chargers and electronics are hazardous — never in regular bins.<br>"
     "• CleanLoop supports doorstep <b>E-Waste pickup</b> — tap <b>Request Pickup</b> and choose E-Waste."),
    (("ewaste",), "🔋 <b>E-Waste</b><br>"
     "• Batteries, bulbs, chargers and electronics are hazardous — never in regular bins.<br>"
     "• CleanLoop supports doorstep <b>E-Waste pickup</b> — tap <b>Request Pickup</b> and choose E-Waste."),
]


def _awareness_answer(message):
    low = _clamp_text(message, 300).lower()
    for keywords, snippet in AWARENESS_SNIPPETS:
        if all(word in low for word in keywords):
            return _reply(snippet, "MAIN_MENU", "START", actions=MAIN_MENU_ACTIONS, state={})
    answer = llm_answer_awareness(message)
    if answer:
        return _reply(answer, "MAIN_MENU", "START", actions=MAIN_MENU_ACTIONS, state={})
    return _reply(
        "♻ Here's the CleanLoop rule of thumb:<br>"
        "• Wet/organic waste → <b>green bin</b><br>"
        "• Clean & dry recyclables (plastic, paper, metal, glass) → <b>blue bin</b><br>"
        "• Hazardous & e-waste → special collection (<b>Request Pickup → E-Waste</b>)<br><br>"
        "Ask me about a specific item, e.g. <i>plastic kaise dispose karu?</i>",
        "MAIN_MENU", "START", actions=MAIN_MENU_ACTIONS, state={})


# ---------------------------------------------------------------------------
# Complaint creation flow
# ---------------------------------------------------------------------------

def _complaint_flow(request, message, state):
    step = state.get("step")
    text = _clamp_text(message, 2000)
    low = text.lower()

    if _is_cancel(text):
        return _reply("No problem — complaint cancelled. Nothing was saved.",
                      "MAIN_MENU", "START", actions=MAIN_MENU_ACTIONS, state={})

    if step == "ISSUE_TYPE":
        code = _issue_label_to_code(text) or _match_issue_code_freeform(text) or "OTHER"
        state["issue_type"] = code
        state["step"] = "DESCRIPTION"
        return _reply(
            "Got it. Please describe the issue in a line or two "
            "(what's wrong, since when, how bad is it?).",
            "REPORT_COMPLAINT", "DESCRIPTION", actions=["Cancel"], state=state)

    if step == "DESCRIPTION":
        state["description"] = text
        state["step"] = "LOCATION"
        return _reply(
            "Where did this happen?",
            "REPORT_COMPLAINT", "LOCATION",
            actions=["📍 Use Current Location", "🗺 Choose on Map", "✏ Enter Address", "Cancel"],
            state=state)

    if step in ("LOCATION", "LOCATION_RETRY"):
        if "current location" in low:
            state["step"] = "GPS_WAIT"
            return _reply("Locating… allow location access in your browser.",
                          "REPORT_COMPLAINT", "GPS_WAIT", actions=["Cancel"], state=state,
                          gps_request=True)
        if "choose on map" in low:
            state["step"] = "MAP_WAIT"
            return _reply("🗺 Pick the spot on the map, then press <b>Confirm location</b>.",
                          "REPORT_COMPLAINT", "MAP_WAIT", actions=["Cancel"], state=state,
                          map_request=True)
        if "enter address" in low:
            state["step"] = "ADDRESS_TEXT"
            return _reply("Type the address or area (e.g. <i>Sector 4 Market</i>):",
                          "REPORT_COMPLAINT", "ADDRESS_TEXT", actions=["Cancel"], state=state)
        # Free-typed address
        state["location"] = text
        state["step"] = "LANDMARK"
        return _reply(f"Noted: <i>{state['location']}</i>. Any nearby landmark?",
                      "REPORT_COMPLAINT", "LANDMARK",
                      actions=["Add Landmark", "Skip", "Cancel"], state=state)

    if step == "ADDRESS_TEXT":
        if not text:
            return _reply("Please type an address or area:",
                          "REPORT_COMPLAINT", "ADDRESS_TEXT", actions=["Cancel"], state=state)
        state["location"] = text
        state["step"] = "LANDMARK"
        return _reply(f"Noted: <i>{text}</i>. Any nearby landmark?",
                      "REPORT_COMPLAINT", "LANDMARK",
                      actions=["Add Landmark", "Skip", "Cancel"], state=state)

    if step in ("GPS_WAIT", "GPS_RETRY"):
        coords = _parse_latlng(text)
        if coords is None:
            state["step"] = "GPS_RETRY"
            return _reply("I couldn't access your location.",
                          "REPORT_COMPLAINT", "GPS_RETRY",
                          actions=["📍 Try Again", "🗺 Choose on Map", "✏ Enter Address", "Cancel"],
                          state=state)
        state["latitude"], state["longitude"] = coords
        addr = _reverse_geocode(coords[0], coords[1])
        state["location"] = addr or f"GPS ({coords[0]:.5f}, {coords[1]:.5f})"
        state["step"] = "LANDMARK"
        return _reply(f"Location detected ✓ <i>{state['location']}</i><br>Any nearby landmark?",
                      "REPORT_COMPLAINT", "LANDMARK",
                      actions=["Add Landmark", "Skip", "Cancel"], state=state)

    if step in ("MAP_WAIT", "MAP_RETRY"):
        coords = _parse_latlng(text)
        if coords is None:
            state["step"] = "MAP_RETRY"
            return _reply("That map selection didn't come through. Want to try again?",
                          "REPORT_COMPLAINT", "MAP_RETRY",
                          actions=["🗺 Choose on Map", "📍 Use Current Location", "✏ Enter Address", "Cancel"],
                          state=state, map_request=True)
        state["latitude"], state["longitude"] = coords
        addr = _reverse_geocode(coords[0], coords[1])
        state["location"] = addr or f"Pinned ({coords[0]:.5f}, {coords[1]:.5f})"
        state["step"] = "LANDMARK"
        return _reply(f"Got it — I've marked your location: <i>{state['location']}</i>.<br>Any nearby landmark?",
                      "REPORT_COMPLAINT", "LANDMARK",
                      actions=["Add Landmark", "Skip", "Cancel"], state=state)

    if step == "LANDMARK":
        if low in ("skip", "no", "nahi", "nope"):
            state["landmark"] = ""
        elif low in ("add landmark", "landmark"):
            state["step"] = "LANDMARK_TEXT"
            return _reply("Type the landmark (e.g. <i>opposite water tank</i>):",
                          "REPORT_COMPLAINT", "LANDMARK_TEXT", actions=["Skip", "Cancel"], state=state)
        else:
            state["landmark"] = text
        state["step"] = "PHOTO"
        return _reply("Would you like to attach a photo as evidence?",
                      "REPORT_COMPLAINT", "PHOTO",
                      actions=["📷 Attach Photo", "Skip", "Cancel"], state=state)

    if step == "LANDMARK_TEXT":
        state["landmark"] = "" if low in ("skip", "no", "nahi") else text
        state["step"] = "PHOTO"
        return _reply("Would you like to attach a photo as evidence?",
                      "REPORT_COMPLAINT", "PHOTO",
                      actions=["📷 Attach Photo", "Skip", "Cancel"], state=state)

    if step == "PHOTO":
        if "attach" in low or ("photo" in low and "skip" not in low):
            state["step"] = "PHOTO_WAIT"
            return _reply("📷 Choose an image (JPG/PNG/WebP, max 5 MB).",
                          "REPORT_COMPLAINT", "PHOTO_WAIT", actions=["Skip", "Cancel"],
                          state=state, photo_request=True)
        state["photo_attached"] = False
        return _complaint_review(state)

    if step == "PHOTO_DONE":
        state["photo_attached"] = True
        return _complaint_review(state)

    if step == "REVIEW":
        if "submit" in low:
            return _complaint_submit(request, state)
        if "edit" in low:
            state["step"] = "EDIT_MENU"
            return _reply("Which part would you like to change?",
                          "REPORT_COMPLAINT", "EDIT_MENU",
                          actions=["Issue", "Description", "Location", "Landmark", "Cancel"], state=state)
        return _complaint_review(state)

    if step == "EDIT_MENU":
        targets = [("issue", "ISSUE_TYPE"), ("description", "DESCRIPTION"),
                   ("location", "LOCATION"), ("landmark", "LANDMARK_TEXT")]
        for word, new_step in targets:
            if word in low:
                state["step"] = new_step
                prompts = {
                    "ISSUE_TYPE": ("What type of issue is it?", ISSUE_TYPES),
                    "DESCRIPTION": ("Describe the issue again:", None),
                    "LOCATION": ("Where did it happen?",
                                 ["📍 Use Current Location", "🗺 Choose on Map", "✏ Enter Address"]),
                    "LANDMARK_TEXT": ("Type the landmark (or Skip):", ["Skip"]),
                }
                prompt_text, acts = prompts[new_step]
                return _reply(prompt_text, "REPORT_COMPLAINT", new_step,
                              actions=(acts or []) + ["Cancel"], state=state)
        return _complaint_review(state)

    return _start_complaint()


def _complaint_review(state):
    state["step"] = "REVIEW"
    loc = state.get("location") or "Not set"
    latlng = ""
    if state.get("latitude") is not None and state.get("longitude") is not None:
        latlng = f" ({float(state['latitude']):.5f}, {float(state['longitude']):.5f})"
    issue_code = state.get("issue_type") or "OTHER"
    issue_label = dict(Complaint.ISSUE_CHOICES).get(issue_code, "Other Waste Issue")
    card = {
        "kind": "review",
        "review_type": "complaint",
        "fields": [
            ("Issue", issue_label),
            ("Description", state.get("description") or "—"),
            ("Location", f"{loc}{latlng}"),
            ("Landmark", state.get("landmark") or "—"),
            ("Photo", "Attached 📷" if state.get("photo_attached") else "Not attached"),
            ("Priority", "Will be calculated by CleanLoop"),
        ],
    }
    return _reply(
        "📋 <b>Report review</b> — please confirm everything looks right.",
        "REPORT_COMPLAINT", "REVIEW",
        actions=["✅ Submit Complaint", "✏ Edit", "❌ Cancel"], state=state,
        cards=[card])


def _complaint_submit(request, state):
    issue_code = state.get("issue_type") or "OTHER"
    if issue_code not in [c[0] for c in Complaint.ISSUE_CHOICES]:
        issue_code = "OTHER"
    location = _clamp_text(state.get("location"), 255) or "Not specified"
    try:
        latitude = float(state.get("latitude") or 28.6139)
        longitude = float(state.get("longitude") or 77.2090)
    except (TypeError, ValueError):
        latitude, longitude = 28.6139, 77.2090

    complaint = Complaint(
        user=request.user,
        issue_type=issue_code,
        description=_clamp_text(state.get("description"), 2000) or "Reported via CleanLoop AI assistant.",
        location=location,
        address=location,
        landmark=_clamp_text(state.get("landmark"), 255),
        latitude=latitude,
        longitude=longitude,
        status="PENDING",
    )
    # Reuse the platform's own smart-priority business logic
    complaint.priority = Complaint.calculate_smart_priority(issue_code, location, latitude, longitude)

    # Attach the photo captured earlier in the chat (held in session, not DB)
    import base64
    from django.core.files.base import ContentFile
    image_b64 = request.session.get("ai_pending_image_b64")
    image_meta = request.session.get("ai_pending_image")
    if image_b64 and image_meta:
        try:
            ext = "jpg" if "jpeg" in image_meta.get("content_type", "") else \
                image_meta.get("content_type", "image/jpeg").split("/")[1].split("+")[0]
            complaint.image.save(
                f"ai_{request.user.id}_{complaint.complaint_id or 'pending'}.{ext}",
                ContentFile(base64.b64decode(image_b64)), save=False)
        except Exception:
            logger.warning("AI photo attach failed", exc_info=True)

    complaint.save()
    # Photo is now on the Complaint row — clear session copies
    request.session.pop("ai_pending_image", None)
    request.session.pop("ai_pending_image_b64", None)

    ComplaintUpdate.objects.create(
        complaint=complaint,
        status="PENDING",
        note="Complaint registered via CleanLoop AI assistant. Pending dispatch review.",
        updated_by=request.user,
    )

    card = {
        "kind": "success",
        "title": "Complaint submitted successfully 🎉",
        "id": complaint.complaint_id,
        "rows": [("Status", complaint.get_status_display()),
                 ("Priority", complaint.get_priority_display()),
                 ("Location", complaint.location)],
        "track_url": f"/complaint/{complaint.complaint_id}/",
    }
    return _reply(
        f"✅ Complaint submitted successfully 🎉<br>"
        f"ID: <b>{complaint.complaint_id}</b><br>"
        f"Status: <b>PENDING</b> • Priority: <b>{complaint.get_priority_display()}</b>",
        "MAIN_MENU", "START",
        actions=["📍 Track Complaint", "📋 My Complaints", "🗑 Report Another", "Cancel"],
        state={}, cards=[card])


# ---------------------------------------------------------------------------
# Pickup creation flow
# ---------------------------------------------------------------------------

def _pickup_flow(request, message, state):
    step = state.get("step")
    text = _clamp_text(message, 2000)
    low = text.lower()

    if _is_cancel(text):
        return _reply("No problem — pickup request cancelled. Nothing was saved.",
                      "MAIN_MENU", "START", actions=MAIN_MENU_ACTIONS, state={})

    if step == "PICK_CATEGORY":
        code = _pickup_label_to_code(text)
        if not code:
            low2 = low
            for word, c in [("organ", "ORGANIC"), ("wet", "ORGANIC"), ("plastic", "PLASTIC"),
                            ("paper", "PAPER"), ("cardboard", "PAPER"), ("glass", "GLASS"),
                            ("metal", "METAL"), ("scrap", "METAL"), ("electronic", "E_WASTE"),
                            ("battery", "E_WASTE"), ("general", "GENERAL")]:
                if word in low2:
                    code = c
                    break
        state["pickup_category"] = code or "GENERAL"
        state["step"] = "QUANTITY"
        return _reply("Roughly how much waste is it? (e.g. <i>2 bags</i>, <i>1 carton box</i>, <i>~10 kg</i>)",
                      "REQUEST_PICKUP", "QUANTITY", actions=["Cancel"], state=state)

    if step == "QUANTITY":
        state["quantity"] = text
        state["step"] = "PICK_LOCATION"
        return _reply("Where should we collect it from?",
                      "REQUEST_PICKUP", "PICK_LOCATION",
                      actions=["📍 Use Current Location", "🗺 Choose on Map", "✏ Enter Address", "Cancel"],
                      state=state)

    if step in ("PICK_LOCATION", "PICK_LOCATION_RETRY"):
        if "current location" in low:
            state["step"] = "PICK_GPS_WAIT"
            return _reply("Locating… allow location access in your browser.",
                          "REQUEST_PICKUP", "PICK_GPS_WAIT", actions=["Cancel"], state=state,
                          gps_request=True)
        if "choose on map" in low:
            state["step"] = "PICK_MAP_WAIT"
            return _reply("🗺 Pick the spot on the map, then press <b>Confirm location</b>.",
                          "REQUEST_PICKUP", "PICK_MAP_WAIT", actions=["Cancel"], state=state,
                          map_request=True)
        if "enter address" in low:
            state["step"] = "PICK_ADDRESS_TEXT"
            profile_addr = _profile_address(request)
            hint = f"<br>Hint from your profile: <i>{profile_addr}</i>" if profile_addr else ""
            return _reply(f"Type the full pickup address:{hint}",
                          "REQUEST_PICKUP", "PICK_ADDRESS_TEXT", actions=["Cancel"], state=state)
        state["pickup_address"] = text
        state["step"] = "PICK_DATE"
        return _pickup_date_question(state)

    if step == "PICK_ADDRESS_TEXT":
        if not text:
            return _reply("Please type the pickup address:",
                          "REQUEST_PICKUP", "PICK_ADDRESS_TEXT", actions=["Cancel"], state=state)
        state["pickup_address"] = text
        state["step"] = "PICK_DATE"
        return _pickup_date_question(state)

    if step in ("PICK_GPS_WAIT", "PICK_GPS_RETRY"):
        coords = _parse_latlng(text)
        if coords is None:
            state["step"] = "PICK_GPS_RETRY"
            return _reply("I couldn't access your location.",
                          "REQUEST_PICKUP", "PICK_GPS_RETRY",
                          actions=["📍 Try Again", "🗺 Choose on Map", "✏ Enter Address", "Cancel"],
                          state=state)
        state["latitude"], state["longitude"] = coords
        addr = _reverse_geocode(coords[0], coords[1])
        state["pickup_address"] = addr or _profile_address(request) \
            or f"GPS ({coords[0]:.5f}, {coords[1]:.5f})"
        state["step"] = "PICK_DATE"
        return _pickup_date_question(state, detected=True)

    if step in ("PICK_MAP_WAIT", "PICK_MAP_RETRY"):
        coords = _parse_latlng(text)
        if coords is None:
            state["step"] = "PICK_MAP_RETRY"
            return _reply("That map selection didn't come through. Want to try again?",
                          "REQUEST_PICKUP", "PICK_MAP_RETRY",
                          actions=["🗺 Choose on Map", "📍 Use Current Location", "✏ Enter Address", "Cancel"],
                          state=state, map_request=True)
        state["latitude"], state["longitude"] = coords
        addr = _reverse_geocode(coords[0], coords[1])
        state["pickup_address"] = addr or _profile_address(request) \
            or f"Pinned ({coords[0]:.5f}, {coords[1]:.5f})"
        state["step"] = "PICK_DATE"
        return _pickup_date_question(state, detected=True)

    if step == "PICK_DATE":
        iso = _norm_date_str(text)
        if not iso:
            return _reply("I couldn't read that date. Try <b>today</b>, <b>tomorrow</b> or <b>YYYY-MM-DD</b>.",
                          "REQUEST_PICKUP", "PICK_DATE", actions=["Cancel"], state=state)
        state["pickup_date"] = iso
        state["step"] = "PICK_TIME"
        return _reply("Which time window works for you?",
                      "REQUEST_PICKUP", "PICK_TIME", actions=PICKUP_TIME_SLOTS + ["Cancel"], state=state)

    if step == "PICK_TIME":
        matched = next(
            (s for s in PICKUP_TIME_SLOTS if s.split(" (")[0].lower() in low or text.strip() == s),
            None)
        if not matched:
            if "morning" in low:
                matched = PICKUP_TIME_SLOTS[0]
            elif "midday" in low or "noon" in low:
                matched = PICKUP_TIME_SLOTS[1]
            elif "afternoon" in low:
                matched = PICKUP_TIME_SLOTS[2]
            elif "evening" in low:
                matched = PICKUP_TIME_SLOTS[3]
        if not matched:
            return _reply("Please pick one of the time windows below.",
                          "REQUEST_PICKUP", "PICK_TIME", actions=PICKUP_TIME_SLOTS + ["Cancel"], state=state)
        state["pickup_time"] = matched
        state["step"] = "PICK_NOTES"
        return _reply("Any notes for the collection team? (gate code, access, handling…)",
                      "REQUEST_PICKUP", "PICK_NOTES", actions=["Skip", "Cancel"], state=state)

    if step == "PICK_NOTES":
        state["notes"] = "" if low in ("skip", "no", "nahi", "nope") else text
        return _pickup_review(state)

    if step == "PICK_REVIEW":
        if "confirm" in low or "submit" in low:
            return _pickup_submit(request, state)
        if "edit" in low:
            state["step"] = "PICK_EDIT_MENU"
            return _reply("Which part would you like to change?",
                          "REQUEST_PICKUP", "PICK_EDIT_MENU",
                          actions=["Category", "Quantity", "Address", "Date", "Time", "Notes", "Cancel"],
                          state=state)
        return _pickup_review(state)

    if step == "PICK_EDIT_MENU":
        targets = [("categor", "PICK_CATEGORY"), ("quantit", "QUANTITY"), ("address", "PICK_LOCATION"),
                   ("date", "PICK_DATE"), ("time", "PICK_TIME"), ("note", "PICK_NOTES")]
        for word, new_step in targets:
            if word in low:
                state["step"] = new_step
                prompts = {
                    "PICK_CATEGORY": ("Which waste category?", PICKUP_CATEGORIES),
                    "QUANTITY": ("Roughly how much waste is it?", None),
                    "PICK_LOCATION": ("Where should we collect it from?",
                                      ["📍 Use Current Location", "🗺 Choose on Map", "✏ Enter Address"]),
                    "PICK_DATE": ("Which date? (today / tomorrow / YYYY-MM-DD)", ["Today", "Tomorrow"]),
                    "PICK_TIME": ("Which time window?", PICKUP_TIME_SLOTS),
                    "PICK_NOTES": ("Any notes for the team?", ["Skip"]),
                }
                prompt_text, acts = prompts[new_step]
                return _reply(prompt_text, "REQUEST_PICKUP", new_step,
                              actions=(acts or []) + ["Cancel"], state=state)
        return _pickup_review(state)

    return _start_pickup()


def _profile_address(request):
    try:
        return request.user.profile.address or ""
    except (UserProfile.DoesNotExist, AttributeError):
        return ""


def _pickup_date_question(state, detected=False):
    today = timezone.localdate()
    tomorrow = today + timedelta(days=1)
    options = [f"Today ({today.strftime('%d %b')})", f"Tomorrow ({tomorrow.strftime('%d %b')})"]
    prefix = "Location detected ✓<br>" if detected else ""
    return _reply(
        f"{prefix}Which date should we come? (you can also type <i>YYYY-MM-DD</i>)",
        "REQUEST_PICKUP", "PICK_DATE", actions=options + ["Cancel"], state=state)


def _pickup_review(state):
    state["step"] = "PICK_REVIEW"
    cat = state.get("pickup_category") or "GENERAL"
    cat_label = dict(PickupRequest.WASTE_CATEGORIES).get(cat, cat)
    card = {
        "kind": "review",
        "review_type": "pickup",
        "fields": [
            ("Category", cat_label),
            ("Quantity", state.get("quantity") or "—"),
            ("Address", state.get("pickup_address") or "—"),
            ("Date", state.get("pickup_date") or "—"),
            ("Time", state.get("pickup_time") or "—"),
            ("Notes", state.get("notes") or "—"),
        ],
    }
    return _reply("📋 <b>Pickup review</b> — please confirm the details.",
                  "REQUEST_PICKUP", "PICK_REVIEW",
                  actions=["✅ Confirm Pickup", "✏ Edit", "❌ Cancel"], state=state,
                  cards=[card])


def _pickup_submit(request, state):
    cat = state.get("pickup_category") or "GENERAL"
    if cat not in [c[0] for c in PickupRequest.WASTE_CATEGORIES]:
        cat = "GENERAL"

    iso_date = state.get("pickup_date")
    if not iso_date:
        return _reply("The pickup date went missing — which day should we come?",
                      "REQUEST_PICKUP", "PICK_DATE",
                      actions=["Today", "Tomorrow", "Cancel"], state=state)
    try:
        y, m, d = (int(x) for x in iso_date.split("-"))
        preferred_date = date(y, m, d)
    except (ValueError, TypeError):
        return _reply("That date didn't parse — let's pick it again.",
                      "REQUEST_PICKUP", "PICK_DATE",
                      actions=["Today", "Tomorrow", "Cancel"], state=state)
    if preferred_date < timezone.localdate():
        return _reply("That date is in the past — please choose today or a future date.",
                      "REQUEST_PICKUP", "PICK_DATE",
                      actions=["Today", "Tomorrow", "Cancel"], state=state)

    try:
        latitude = float(state.get("latitude") or 28.6139)
        longitude = float(state.get("longitude") or 77.2090)
    except (TypeError, ValueError):
        latitude, longitude = 28.6139, 77.2090

    pickup = PickupRequest(
        user=request.user,
        waste_category=cat,
        quantity=_clamp_text(state.get("quantity"), 100) or "1 bag",
        pickup_address=_clamp_text(state.get("pickup_address"), 1000) or "Not specified",
        latitude=latitude,
        longitude=longitude,
        preferred_date=preferred_date,
        preferred_time=_clamp_text(state.get("pickup_time"), 50) or PICKUP_TIME_SLOTS[0],
        notes=_clamp_text(state.get("notes"), 500),
        status="REQUESTED",
    )
    pickup.save()

    card = {
        "kind": "success",
        "title": "Pickup requested successfully",
        "id": pickup.pickup_id,
        "rows": [("Status", pickup.get_status_display()),
                 ("Category", pickup.get_waste_category_display()),
                 ("When", f"{_fmt_date(pickup.preferred_date)} • {pickup.preferred_time}")],
        "track_url": "/pickup/list/",
    }
    return _reply(
        f"✅ Pickup requested successfully.<br>ID: <b>{pickup.pickup_id}</b><br>"
        f"Status: <b>REQUESTED</b>",
        "MAIN_MENU", "START",
        actions=["📦 Track Pickup", "📋 My Pickups", "🚛 Request Another", "Cancel"],
        state={}, cards=[card])


# ---------------------------------------------------------------------------
# Authentication flow (unauthenticated citizens) — passwords never hit the LLM
# ---------------------------------------------------------------------------

def _handle_auth(request, message, state):
    step = state.get("step", "START")
    intent = state.get("intent", "")
    text = _clamp_text(message, 2000)
    low = text.lower().strip()

    if _is_cancel(text) or low in ("cancel",):
        return _reply("No problem. How would you like to continue?",
                      "AUTH", "CHOOSE", actions=["Sign In", "Create Account"], state={})

    # Entry / menu
    if intent not in ("AUTH_SIGNIN", "AUTH_SIGNUP"):
        if not text:
            return _reply(
                "Welcome to CleanLoop 👋<br>Please sign in or create a citizen account to report "
                "waste, request pickups and track your services.",
                "AUTH", "CHOOSE", actions=["Sign In", "Create Account"], state={})
        if low in ("sign in", "signin", "login", "try again"):
            return _reply("Let's get you signed in.<br>What's your <b>username or email</b>?",
                          "AUTH_SIGNIN", "ASK_USERNAME", actions=["Cancel"],
                          state={"intent": "AUTH_SIGNIN", "step": "ASK_USERNAME"})
        if low in ("create account", "sign up", "signup", "register"):
            return _reply("Let's create your citizen account.<br>What's your <b>full name</b>?",
                          "AUTH_SIGNUP", "ASK_NAME", actions=["Cancel"],
                          state={"intent": "AUTH_SIGNUP", "step": "ASK_NAME"})
        return _reply(
            "Welcome to CleanLoop 👋<br>Please sign in or create a citizen account to get started.",
            "AUTH", "CHOOSE", actions=["Sign In", "Create Account"], state={})

    # ---- Sign in ----
    if intent == "AUTH_SIGNIN":
        if step == "ASK_USERNAME":
            if not text:
                return _reply("Please enter your username or email:",
                              "AUTH_SIGNIN", "ASK_USERNAME", actions=["Cancel"], state=state)
            state["auth_username"] = _clamp_text(text, 150)
            state["step"] = "ASK_PASSWORD"
            return _reply("Thanks. Now enter your password — it stays between you and CleanLoop.",
                          "AUTH_SIGNIN", "ASK_PASSWORD", actions=["Cancel"], state=state,
                          secure_input=True)
        if step == "ASK_PASSWORD":
            # `message` is the password: used once, never stored, never logged.
            user = authenticate(request, username=state.get("auth_username", ""), password=message)
            if user is not None:
                login(request, user)
                name = user.first_name or user.username
                return _reply(f"Welcome back, {name}! 👋<br>What would you like to do today?",
                              "MAIN_MENU", "START", actions=MAIN_MENU_ACTIONS, state={})
            return _reply("That didn't match our records. Want to try again?",
                          "AUTH_SIGNIN", "ASK_USERNAME",
                          actions=["Try Again", "Cancel"],
                          state={"intent": "AUTH_SIGNIN", "step": "ASK_USERNAME"})

    # ---- Sign up ----
    if intent == "AUTH_SIGNUP":
        if step == "ASK_NAME":
            if len(text) < 2:
                return _reply("Please enter your full name:", "AUTH_SIGNUP", "ASK_NAME",
                              actions=["Cancel"], state=state)
            state["auth_name"] = _clamp_text(text, 150)
            state["step"] = "ASK_EMAIL"
            return _reply("Nice to meet you! What's your <b>email</b>? (it becomes your username)",
                          "AUTH_SIGNUP", "ASK_EMAIL", actions=["Cancel"], state=state)
        if step == "ASK_EMAIL":
            email = _clamp_text(text, 254).lower()
            try:
                validate_email(email)
            except ValidationError:
                return _reply("That email doesn't look right — try again?",
                              "AUTH_SIGNUP", "ASK_EMAIL", actions=["Cancel"], state=state)
            if User.objects.filter(email__iexact=email).exists() \
                    or User.objects.filter(username__iexact=email).exists():
                return _reply("An account with this email already exists. Try signing in instead?",
                              "AUTH_SIGNUP", "ASK_EMAIL", actions=["Sign In", "Cancel"], state=state)
            state["auth_email"] = email
            state["step"] = "ASK_PHONE"
            return _reply("Got it. What's your <b>phone number</b>?",
                          "AUTH_SIGNUP", "ASK_PHONE", actions=["Cancel"], state=state)
        if step == "ASK_PHONE":
            phone = _clamp_text(text, 20)
            if not re.fullmatch(r"[0-9+\-\s()]{6,20}", phone):
                return _reply("That phone number doesn't look valid — try again?",
                              "AUTH_SIGNUP", "ASK_PHONE", actions=["Cancel"], state=state)
            state["auth_phone"] = phone
            state["step"] = "ASK_ADDRESS"
            return _reply("Your <b>address</b> (optional — helps with pickups):",
                          "AUTH_SIGNUP", "ASK_ADDRESS", actions=["Skip", "Cancel"], state=state)
        if step == "ASK_ADDRESS":
            state["auth_address"] = "" if low in ("skip", "no", "nahi") else _clamp_text(text, 255)
            state["step"] = "ASK_PASSWORD"
            return _reply(
                "Almost done. Choose a <b>password</b> (min 6 characters) — it's never shared with "
                "the AI or stored in this chat.",
                "AUTH_SIGNUP", "ASK_PASSWORD", actions=["Cancel"], state=state,
                secure_input=True)
        if step == "ASK_PASSWORD":
            if len(message) < 6:
                return _reply("Passwords need at least 6 characters. Try a longer one:",
                              "AUTH_SIGNUP", "ASK_PASSWORD", actions=["Cancel"], state=state,
                              secure_input=True)
            # Reuse the platform's own registration form + save() (User + UserProfile)
            form = CitizenRegistrationForm(data={
                "full_name": state.get("auth_name", ""),
                "email": state.get("auth_email", ""),
                "phone": state.get("auth_phone", ""),
                "address": state.get("auth_address", ""),
                "password": message,
                "confirm_password": message,
            })
            if not form.is_valid():
                first_error = "; ".join(e for errs in form.errors.values() for e in errs)[:160]
                return _reply(f"Couldn't create the account: {first_error}<br>Please choose another password:",
                              "AUTH_SIGNUP", "ASK_PASSWORD", actions=["Cancel"], state=state,
                              secure_input=True)
            user = form.save()  # creates User + UserProfile, password properly hashed
            login(request, user)
            return _reply(
                f"Account created — welcome to CleanLoop, {user.first_name or user.username}! 🎉<br>"
                f"What would you like to do today?",
                "MAIN_MENU", "START", actions=MAIN_MENU_ACTIONS, state={})

    # Fallback
    return _reply(
        "Welcome to CleanLoop 👋<br>Please sign in or create a citizen account to get started.",
        "AUTH", "CHOOSE", actions=["Sign In", "Create Account"], state={})
