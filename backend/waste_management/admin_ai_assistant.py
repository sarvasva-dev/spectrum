"""
CleanLoop Admin AI Dispatch Assistant
======================================
Conversational assistant powering the /admin-portal/ai/ Municipal Control Room.

Architecture & Security:
  - Restricted strictly to staff/admin users.
  - Django ORM is the sole authority for DB reads/updates.
  - Admin users can view city analytics, inspect hotspots, list pending issues,
    assign crews/vehicles, and update complaint/pickup statuses conversationally.

Public API:
    run_admin_ai_chat(request, message, state) -> dict
    provider_available() -> bool
"""

import os
import json
import logging
import re
from datetime import timedelta
import requests

from django.db.models import Count, Q
from django.utils import timezone

from .models import Complaint, ComplaintUpdate, PickupRequest, UserProfile

logger = logging.getLogger(__name__)

SARVAM_API_URL = "https://api.sarvam.ai/v1/chat/completions"
SARVAM_MODEL = "sarvam-105b"
LLM_TIMEOUT_SECONDS = 25

ADMIN_MENU_ACTIONS = [
    "📊 City Overview",
    "🚨 Active Hotspots",
    "⚠️ Pending Complaints",
    "🚛 Pickup Requests",
    "👥 Available Crews",
    "📈 Ward EHI Score",
]

AVAILABLE_CREWS = [
    "Crew Alpha (Zone 1 - Ward 12)",
    "Crew Beta (Zone 2 - Ward 05)",
    "Crew Gamma (Zone 3 - Ward 18)",
    "Sanitation Rapid Unit #4",
]

AVAILABLE_VEHICLES = [
    "Eco-Van #02 (Driver: Rajesh)",
    "Recyclables Truck #05 (Driver: Sunil)",
    "Compactor Truck #01 (Driver: Amit)",
    "Electric Mini Collector #03 (Driver: Vikram)",
]

SYSTEM_PROMPT = (
    "You are the intent router inside CleanLoop Municipal Control Room, an Indian smart waste management "
    "administrator console. Municipal officers interact with you to manage city waste operations.\n"
    "Classify the officer's message into exactly one intent and reply with ONLY minified JSON:\n"
    '{"intent":"CITY_SUMMARY|HOTSPOTS|PENDING_COMPLAINTS|PENDING_PICKUPS|CREW_LIST|'
    'DISPATCH_CREW|DISPATCH_PICKUP|UPDATE_STATUS|HELP|CANCEL|UNKNOWN"}\n'
    "Examples:\n"
    'city status kya hai -> {"intent":"CITY_SUMMARY"}\n'
    'active hotspots dikhao -> {"intent":"HOTSPOTS"}\n'
    'pending complaints dikhao -> {"intent":"PENDING_COMPLAINTS"}\n'
    'pending pickups dikhao -> {"intent":"PENDING_PICKUPS"}\n'
    'crews list karo -> {"intent":"CREW_LIST"}\n'
    'WM-2026-0022 ko crew assign karo -> {"intent":"DISPATCH_CREW"}\n'
    'PK-2026-0017 ko vehicle assign karo -> {"intent":"DISPATCH_PICKUP"}\n'
    'WM-2026-0022 resolve ho gaya -> {"intent":"UPDATE_STATUS"}\n'
    'help -> {"intent":"HELP"}'
)


def provider_available():
    return bool(os.environ.get("SARVAM_API_KEY"))


def _clamp_text(value, max_len=2000):
    if value is None:
        return ""
    return str(value).strip()[:max_len]


def _fmt_date(dt):
    if not dt:
        return "-"
    return dt.strftime("%d %b %Y")


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


def _is_admin(user):
    if not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    try:
        return bool(user.profile.is_admin_staff)
    except Exception:
        return False


def llm_classify_intent(message):
    api_key = os.environ.get("SARVAM_API_KEY")
    if not api_key:
        return None
    try:
        resp = requests.post(
            SARVAM_API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": SARVAM_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": message},
                ],
                "temperature": 0.1,
            },
            timeout=LLM_TIMEOUT_SECONDS,
        )
        if resp.status_code != 200:
            return None
        content = resp.json()["choices"][0]["message"]["content"]
        match = re.search(r"\{[^}]*\}", content, re.DOTALL)
        if not match:
            return None
        intent = json.loads(match.group(0)).get("intent", "UNKNOWN")
        allowed = {
            "CITY_SUMMARY", "HOTSPOTS", "PENDING_COMPLAINTS", "PENDING_PICKUPS",
            "CREW_LIST", "DISPATCH_CREW", "DISPATCH_PICKUP", "UPDATE_STATUS",
            "HELP", "CANCEL", "UNKNOWN",
        }
        return intent if intent in allowed else None
    except Exception:
        return None


def run_admin_ai_chat(request, message, state):
    if not _is_admin(request.user):
        return {
            "ok": False,
            "error": "Unauthorized access. Municipal administrator credentials required.",
        }

    message = _clamp_text(message, 2000)
    low = message.lower().strip()

    if not isinstance(state, dict):
        state = {}

    intent = state.get("intent", "")
    step = state.get("step", "START")

    # Global cancel
    if low in ("cancel", "❌ cancel", "stop", "exit"):
        return _reply("Operation cancelled. What would you like to inspect next?",
                      "ADMIN_MAIN", "START", actions=ADMIN_MENU_ACTIONS, state={})

    # Flow priority
    if intent == "DISPATCH_CREW" and step == "SELECT_CREW":
        return _handle_dispatch_crew_selection(request, message, state)
    if intent == "DISPATCH_PICKUP" and step == "SELECT_VEHICLE":
        return _handle_dispatch_vehicle_selection(request, message, state)
    if intent == "UPDATE_STATUS" and step == "SELECT_STATUS":
        return _handle_status_update(request, message, state)

    # Quick Action Route
    if low in ("📊 city overview", "city overview", "city status"):
        return _city_summary()
    if low in ("🚨 active hotspots", "active hotspots", "hotspots"):
        return _active_hotspots()
    if low in ("⚠️ pending complaints", "pending complaints"):
        return _pending_complaints()
    if low in ("🚛 pickup requests", "pickup requests"):
        return _pending_pickups()
    if low in ("👥 available crews", "available crews", "crews"):
        return _crew_list()
    if low in ("📈 ward ehi score", "ward ehi score", "ehi"):
        return _ehi_score()

    # Rule-based intent detection
    if re.search(r"(city|overview|summary|stats|total|metrics)", low):
        return _city_summary()
    if re.search(r"(hotspot|cluster|high density)", low):
        return _active_hotspots()
    if re.search(r"(pending complaint|open complaint|unresolved complaint)", low):
        return _pending_complaints()
    if re.search(r"(pickup|doorstep|request list)", low):
        return _pending_pickups()
    if re.search(r"(crew|team|staff|worker|driver)", low):
        return _crew_list()
    if re.search(r"(wm-\d{4}-\d{3,})", low):
        return _start_dispatch_complaint(message)
    if re.search(r"(pk-\d{4}-\d{3,})", low):
        return _start_dispatch_pickup(message)

    # LLM Classifier fallback
    classified = llm_classify_intent(message)
    if classified == "CITY_SUMMARY":
        return _city_summary()
    if classified == "HOTSPOTS":
        return _active_hotspots()
    if classified == "PENDING_COMPLAINTS":
        return _pending_complaints()
    if classified == "PENDING_PICKUPS":
        return _pending_pickups()
    if classified == "CREW_LIST":
        return _crew_list()
    if classified == "HELP":
        return _reply_help(request)

    ai_resp = _freeform_ai_response(request, message)
    if ai_resp:
        return _reply(f"🤖 <b>CleanLoop Municipal AI</b>:<br>{ai_resp}", "ADMIN_MAIN", "START", actions=ADMIN_MENU_ACTIONS, state={})

    return _greeting(request)


def _freeform_ai_response(request, message):
    """Answers freeform municipal administration or waste management questions using Sarvam AI."""
    api_key = os.environ.get("SARVAM_API_KEY")
    if not api_key:
        return None
    grounding = (
        "You are CleanLoop Municipal Control AI Assistant for city sanitation officers in India.\n"
        "Provide professional, concise, municipal operations & waste management guidance in English or Hinglish.\n"
        "Help officers with waste management policies, vehicle dispatching advice, hotspot mitigation, and public safety.\n"
        "Keep responses under 90 words, plain text (no markdown format), polite and authoritative."
    )
    try:
        resp = requests.post(
            SARVAM_API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": SARVAM_MODEL,
                "messages": [
                    {"role": "system", "content": grounding},
                    {"role": "user", "content": _clamp_text(message, 500)},
                ],
                "temperature": 0.3,
            },
            timeout=LLM_TIMEOUT_SECONDS,
        )
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            if content:
                return _clamp_text(content, 900)
        else:
            logger.error("Sarvam Admin API call failed: HTTP %s - %s", resp.status_code, resp.text)
    except Exception as exc:
        logger.error("Sarvam admin freeform AI exception: %s", exc, exc_info=True)
    return None


def _greeting(request):
    name = request.user.first_name or request.user.username
    return _reply(
        f"CleanLoop Municipal Control AI Active 🛡️<br>"
        f"Welcome back, Officer {name}. Select an administrative action below or type any command.",
        "ADMIN_MAIN", "START", actions=ADMIN_MENU_ACTIONS, state={})


def _reply_help(request):
    return _reply(
        "<b>Municipal Control AI Capabilities</b> 🛠️<br>"
        "• 📊 <b>City Overview</b> — Live metrics, pending counts, resolution rates<br>"
        "• 🚨 <b>Active Hotspots</b> — Unresolved waste cluster analysis<br>"
        "• ⚠️ <b>Pending Complaints</b> — Inspect open tickets and dispatch crews<br>"
        "• 🚛 <b>Pickup Requests</b> — Schedule vehicles for doorstep collections<br>"
        "• 👥 <b>Sanitation Crews</b> — View active field units<br>"
        "• ⚡ <b>Direct Command</b> — Type e.g. <i>WM-2026-0022</i> or <i>PK-2026-0017</i> to update status.",
        "ADMIN_MAIN", "START", actions=ADMIN_MENU_ACTIONS, state={})


def _city_summary():
    total_citizens = UserProfile.objects.filter(is_admin_staff=False).count()
    total_complaints = Complaint.objects.count()
    pending_complaints = Complaint.objects.exclude(status='RESOLVED').count()
    resolved_complaints = Complaint.objects.filter(status='RESOLVED').count()

    total_pickups = PickupRequest.objects.count()
    completed_pickups = PickupRequest.objects.filter(status='COMPLETED').count()

    # Smart EHI score simulation logic based on unresolved complaints
    ehi_score = max(15, 100 - (pending_complaints * 6))
    ehi_status = "CRITICAL SANITATION ALERT" if ehi_score < 40 else ("MODERATE RISK" if ehi_score < 70 else "OPTIMAL")

    card = {
        "kind": "admin_summary",
        "title": "Municipal Operations Summary",
        "stats": [
            ("Total Citizens Registered", total_citizens),
            ("Total Complaints Filed", total_complaints),
            ("Pending / Active Complaints", pending_complaints),
            ("Resolved Complaints", resolved_complaints),
            ("Total Pickup Requests", total_pickups),
            ("Completed Pickups", completed_pickups),
            ("City Ward EHI Score", f"{ehi_score} / 100 ({ehi_status})"),
        ]
    }
    return _reply(
        f"📊 <b>Citywide Municipal Operations Snapshot</b><br>"
        f"• Pending Issues: <b>{pending_complaints}</b> | Resolved: <b>{resolved_complaints}</b><br>"
        f"• Ward EHI Sanitation Score: <b>{ehi_score}/100</b> ({ehi_status})",
        "ADMIN_MAIN", "START", actions=ADMIN_MENU_ACTIONS, state={}, cards=[card])


def _active_hotspots():
    hotspots = Complaint.objects.exclude(status='RESOLVED') \
        .values('location') \
        .annotate(total=Count('id')) \
        .order_by('-total')[:5]

    if not hotspots:
        return _reply("✅ No active waste hotspots detected. All reported zones are clean.",
                      "ADMIN_MAIN", "START", actions=ADMIN_MENU_ACTIONS, state={})

    lines = []
    for idx, h in enumerate(hotspots, 1):
        loc = h['location'] or "Unknown Zone"
        cnt = h['total']
        severity = "🔴 CRITICAL" if cnt >= 3 else ("🟡 ELEVATED" if cnt == 2 else "🔵 MONITORING")
        lines.append(f"{idx}. <b>{loc}</b> — {cnt} active complaint(s) [{severity}]")

    return _reply(
        f"🚨 <b>Active Garbage Hotspots & Cluster Alert</b><br>" + "<br>".join(lines),
        "ADMIN_MAIN", "START", actions=ADMIN_MENU_ACTIONS, state={})


def _pending_complaints():
    qs = Complaint.objects.exclude(status='RESOLVED').order_by('-created_at')[:5]
    if not qs:
        return _reply("🎉 Great news! There are zero pending complaints at this time.",
                      "ADMIN_MAIN", "START", actions=ADMIN_MENU_ACTIONS, state={})

    cards = []
    lines = []
    for c in qs:
        lines.append(f"• <b>{c.complaint_id}</b> — {c.get_issue_type_display()} ({c.get_priority_display()} Priority)")
        cards.append({
            "kind": "complaint",
            "id": c.complaint_id,
            "title": c.get_issue_type_display(),
            "status": c.get_status_display(),
            "priority": c.get_priority_display(),
            "date": _fmt_date(timezone.localtime(c.created_at)),
            "location": (c.location or c.address or "")[:80],
        })

    return _reply(
        f"⚠️ <b>Top Pending Complaints ({Complaint.objects.exclude(status='RESOLVED').count()} total)</b><br>" + "<br>".join(lines) + "<br><br>Type or tap a Complaint ID to assign crew.",
        "ADMIN_MAIN", "START", actions=[c.complaint_id for c in qs] + ["Cancel"], state={}, cards=cards)


def _pending_pickups():
    qs = PickupRequest.objects.exclude(status='COMPLETED').order_by('-created_at')[:5]
    if not qs:
        return _reply("📦 All pickup requests have been completed!",
                      "ADMIN_MAIN", "START", actions=ADMIN_MENU_ACTIONS, state={})

    cards = []
    lines = []
    for p in qs:
        lines.append(f"• <b>{p.pickup_id}</b> — {p.get_waste_category_display()} ({p.get_status_display()})")
        cards.append({
            "kind": "pickup",
            "id": p.pickup_id,
            "title": p.get_waste_category_display(),
            "status": p.get_status_display(),
            "date": _fmt_date(p.preferred_date),
            "location": (p.pickup_address or "").split("\n")[0][:80],
        })

    return _reply(
        f"🚛 <b>Pending Doorstep Pickup Requests ({PickupRequest.objects.exclude(status='COMPLETED').count()} total)</b><br>" + "<br>".join(lines) + "<br><br>Tap a Pickup ID to dispatch vehicle.",
        "ADMIN_MAIN", "START", actions=[p.pickup_id for p in qs] + ["Cancel"], state={}, cards=cards)


def _crew_list():
    lines = [f"• {crew}" for crew in AVAILABLE_CREWS]
    return _reply(
        "👥 <b>Active Municipal Sanitation Field Units</b><br>" + "<br>".join(lines),
        "ADMIN_MAIN", "START", actions=ADMIN_MENU_ACTIONS, state={})


def _ehi_score():
    pending = Complaint.objects.exclude(status='RESOLVED').count()
    score = max(15, 100 - (pending * 6))
    return _reply(
        f"📈 <b>Ward Environmental Health Index (EHI) Score</b><br>"
        f"Current Index: <b>{score} / 100</b><br>"
        f"Status: " + ("🚨 High Sanitation Risk — Immediate Crew Dispatch Recommended" if score < 40 else "✅ Good Operational Standing"),
        "ADMIN_MAIN", "START", actions=ADMIN_MENU_ACTIONS, state={})


def _start_dispatch_complaint(message):
    m = re.search(r"(wm-\d{4}-\d{3,})", message.lower())
    if not m:
        return _reply("Complaint ID not recognized. Format should be WM-YYYY-NNNN.", "ADMIN_MAIN", "START", actions=ADMIN_MENU_ACTIONS)
    cid = m.group(1).upper()
    complaint = Complaint.objects.filter(complaint_id=cid).first()
    if not complaint:
        return _reply(f"Complaint <b>{cid}</b> was not found.", "ADMIN_MAIN", "START", actions=ADMIN_MENU_ACTIONS)

    state = {
        "intent": "DISPATCH_CREW",
        "step": "SELECT_CREW",
        "target_id": cid,
    }
    return _reply(
        f"📋 <b>Dispatch Unit for {cid}</b> ({complaint.get_issue_type_display()})<br>"
        f"Current Status: <b>{complaint.get_status_display()}</b> | Assigned Crew: <b>{complaint.assigned_crew or 'None'}</b><br><br>"
        f"Select a crew to assign or update status:",
        "DISPATCH_CREW", "SELECT_CREW",
        actions=AVAILABLE_CREWS + ["Mark Resolved", "Cancel"], state=state)


def _handle_dispatch_crew_selection(request, message, state):
    cid = state.get("target_id")
    complaint = Complaint.objects.filter(complaint_id=cid).first()
    if not complaint:
        return _reply("Target complaint not found.", "ADMIN_MAIN", "START", actions=ADMIN_MENU_ACTIONS)

    if message.lower() in ("mark resolved", "resolve", "resolved"):
        complaint.status = "RESOLVED"
        complaint.save()
        ComplaintUpdate.objects.create(
            complaint=complaint,
            status="RESOLVED",
            note="Status updated to RESOLVED via CleanLoop Admin AI Assistant.",
            updated_by=request.user,
        )
        return _reply(f"✅ Complaint <b>{cid}</b> marked as <b>RESOLVED</b> 🎉",
                      "ADMIN_MAIN", "START", actions=ADMIN_MENU_ACTIONS, state={})

    complaint.assigned_crew = message
    complaint.status = "IN_PROGRESS"
    complaint.save()
    ComplaintUpdate.objects.create(
        complaint=complaint,
        status="IN_PROGRESS",
        note=f"Assigned to field unit: {message} via CleanLoop Admin AI Assistant.",
        updated_by=request.user,
    )
    return _reply(f"🚛 Field unit <b>{message}</b> assigned to <b>{cid}</b> ✓<br>Status updated to <b>IN_PROGRESS</b>.",
                  "ADMIN_MAIN", "START", actions=ADMIN_MENU_ACTIONS, state={})


def _start_dispatch_pickup(message):
    m = re.search(r"(pk-\d{4}-\d{3,})", message.lower())
    if not m:
        return _reply("Pickup ID not recognized. Format should be PK-YYYY-NNNN.", "ADMIN_MAIN", "START", actions=ADMIN_MENU_ACTIONS)
    pid = m.group(1).upper()
    pickup = PickupRequest.objects.filter(pickup_id=pid).first()
    if not pickup:
        return _reply(f"Pickup request <b>{pid}</b> was not found.", "ADMIN_MAIN", "START", actions=ADMIN_MENU_ACTIONS)

    state = {
        "intent": "DISPATCH_PICKUP",
        "step": "SELECT_VEHICLE",
        "target_id": pid,
    }
    return _reply(
        f"📦 <b>Vehicle Dispatch for {pid}</b> ({pickup.get_waste_category_display()})<br>"
        f"Current Status: <b>{pickup.get_status_display()}</b> | Vehicle: <b>{pickup.assigned_vehicle or 'None'}</b><br><br>"
        f"Select a vehicle to assign or mark completed:",
        "DISPATCH_PICKUP", "SELECT_VEHICLE",
        actions=AVAILABLE_VEHICLES + ["Mark Completed", "Cancel"], state=state)


def _handle_dispatch_vehicle_selection(request, message, state):
    pid = state.get("target_id")
    pickup = PickupRequest.objects.filter(pickup_id=pid).first()
    if not pickup:
        return _reply("Target pickup request not found.", "ADMIN_MAIN", "START", actions=ADMIN_MENU_ACTIONS)

    if message.lower() in ("mark completed", "completed", "complete"):
        pickup.status = "COMPLETED"
        pickup.save()
        return _reply(f"✅ Pickup <b>{pid}</b> marked as <b>COMPLETED</b> 🎉",
                      "ADMIN_MAIN", "START", actions=ADMIN_MENU_ACTIONS, state={})

    pickup.assigned_vehicle = message
    pickup.status = "ASSIGNED"
    pickup.save()
    return _reply(f"🚛 Vehicle <b>{message}</b> assigned to <b>{pid}</b> ✓<br>Status updated to <b>ASSIGNED</b>.",
                  "ADMIN_MAIN", "START", actions=ADMIN_MENU_ACTIONS, state={})
