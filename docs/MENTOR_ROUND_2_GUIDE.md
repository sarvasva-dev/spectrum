# CleanLoop — Mentor Round 2 Evaluation & Technical Dossier

> **Team Bug Busters | Spectrum Hackathon 2026**
> **Project:** CleanLoop — Smart Waste Management & Community Incentive Platform

---

## 🎯 Executive Summary for Mentors

CleanLoop solves urban waste management challenges by closing the loop between **Citizens**, **AI**, and **Municipal Administrators**.

```
  [Citizen Reports Waste + Photo/GPS] 
               │
               ▼
   [Sarvam AI Assistant / Auto Priority]
               │
               ▼
 [Admin Panel: Hotspot Detection + Predictive Dispatch]
               │
               ▼
    [Sanitation Crew Resolves Issue] ──► [Citizen Receives CleanCoins]
```

---

## 🚀 Key Innovations

1. **AI Assistant (`/ai/`):**
   * Powered by Sarvam AI (`sarvam-105b`), supporting natural language queries in English, Hindi, and Hinglish.
   * Provides localized waste disposal guidance and real-time status lookup ("WM-2026-0025 ka status?").

2. **Community Gamification (CleanCoins):**
   * Citizens earn +50 CleanCoins upon verification and resolution of reported waste issues.
   * Community Leaderboard & "Man of the Month" (`/man-of-the-month/`) drive active public participation.

3. **Predictive Municipal Operations (`/admin-portal/`):**
   * **Ward Environmental Health Index (EHI 0-100):** Real-time score based on resolution rates and pending complaints.
   * **Automated Geographic Hotspot Clustering:** Uses Haversine distance matrix (0.5km radius) to detect chronic waste build-ups.
   * **Predictive Route polyline:** Nearest-Neighbor algorithm plots optimal collection routes for dispatch teams.

4. **Real-Time Visualizer (`/visual/`):**
   * Django Channels + WebSocket event graph broadcasting backend events live without page reloads.

---

## 🏗️ Technical Architecture & Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.14 + Django 6.1 | Modular Monolith, REST APIs, ORM, Auth |
| **AI LLM Engine** | Sarvam AI API (`sarvam-105b`) | Intent classification, localized guidelines |
| **Geospatial & Mapping** | Leafmap + Folium (Leaflet rendering) | Server-side map generation & GPS marker handling |
| **Real-time Engine** | Django Channels + Daphne | WebSocket event streaming for visualizer |
| **Frontend UI** | HTML5, Light Blue Vanilla CSS, Vanilla JS | Standalone template design, zero NPM build overhead |
| **Database** | SQLite3 | Local development DB with deterministic reads/writes |

---

## 📜 Presentation & Demo Flow (4-Phase Script)

For full speaking script and controller cues, see [PRESENTATION_SCRIPT.md](file:///c:/Users/Admin/OneDrive/Desktop/spectrum/docs/PRESENTATION_SCRIPT.md).

1. **Phase 1: Greetings & Vision** — Problem statement and overview on Landing Page.
2. **Phase 2: Platform & Gamification** — Metrics summary and Citizen Leaderboard / CleanCoins.
3. **Phase 3: Citizen Workflow & AI** — Citizen login, AI queries, GPS auto-location, and photo upload.
4. **Phase 4: Municipal Admin Resolution** — Live hotspot view, sanitation team dispatch, single-click 'Resolve', and CleanCoins issuance.

---

## 🧠 Mentor Technical Q&A Defense

#### Q1: Why SQLite3 instead of PostgreSQL / PostGIS?
> **Answer:** For the hackathon scope, SQLite3 allows instant zero-config startup (`python manage.py runserver`) without external database dependencies. The backend ORM abstractions and Haversine distance algorithms are structured so transitioning to PostgreSQL + PostGIS in production requires changing only `settings.py` (`DATABASES`).

#### Q2: How does the Hotspot Clustering algorithm work?
> **Answer:** Active, unresolved complaints are evaluated on backend load. We run pairwise Haversine calculations (radius = 0.5km). Clusters with $\ge 3$ reports suggest "Deploy Extra Bin", while $\ge 2$ suggest "Schedule Daily Clearance", rendered dynamically via `folium.Circle()` markers on the Admin Map.

#### Q3: What happens if the AI service (Sarvam AI) is unreachable?
> **Answer:** The AI module implements a strict try/except fallback block. If the API times out or fails, the interface gracefully degrades to structured rule-based intent parsing and displays standard waste disposal guidelines without breaking the user experience.

---

## 📌 Repository Documentation Index

* 📜 [PRESENTATION_SCRIPT.md](file:///c:/Users/Admin/OneDrive/Desktop/spectrum/docs/PRESENTATION_SCRIPT.md) — Live demo script for speakers & screen controller
* 📖 [PROJECT_DOCUMENTATION.md](file:///c:/Users/Admin/OneDrive/Desktop/spectrum/docs/PROJECT_DOCUMENTATION.md) — System architecture & feature breakdown
* ❓ [HACKATHON_QA.md](file:///c:/Users/Admin/OneDrive/Desktop/spectrum/docs/HACKATHON_QA.md) — Detailed technical Q&A for judges & mentors
* ⚙️ [CRUD_ARCHITECTURE_GUIDE.md](file:///c:/Users/Admin/OneDrive/Desktop/spectrum/docs/CRUD_ARCHITECTURE_GUIDE.md) — Backend models, routes & REST APIs
* 🛠️ [COMPLETE_FEATURES_SPECIFICATION.md](file:///c:/Users/Admin/OneDrive/Desktop/spectrum/docs/COMPLETE_FEATURES_SPECIFICATION.md) — Full functional spec
