# CleanLoop — Smart Waste Management
**Spectrum Hackathon 2026** • Team Bug Busters

[![Python 3.14](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![Django 6.1](https://img.shields.io/badge/Django-6.1-green.svg)](https://www.djangoproject.com/)
[![Sarvam AI](https://img.shields.io/badge/AI-Sarvam--105B-purple.svg)](https://sarvam.ai/)
[![Nginx](https://img.shields.io/badge/Nginx-Reverse%20Proxy-brightgreen.svg)](https://nginx.org/)
[![Gunicorn](https://img.shields.io/badge/Gunicorn-WSGI-orange.svg)](https://gunicorn.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> A centralized waste management, pickup logistics and citizen engagement platform for cleaner cities and communities.

---

## 🌐 Live Production Domain & Links
- **Canonical Production Site**: [https://cleanloop.sarthakml.in/](https://cleanloop.sarthakml.in/)
- **AI Citizen Assistant**: [https://cleanloop.sarthakml.in/ai/](https://cleanloop.sarthakml.in/ai/)
- **Platform Knowledge Hub / Guide**: [https://cleanloop.sarthakml.in/guide/](https://cleanloop.sarthakml.in/guide/)
- **Municipal Admin Portal**: [https://cleanloop.sarthakml.in/admin-portal/](https://cleanloop.sarthakml.in/admin-portal/)
- **System Visualizer & REST API**: [https://cleanloop.sarthakml.in/visual/](https://cleanloop.sarthakml.in/visual/)

---

## 🔑 Demo Credentials

| Role | Username / Email | Password |
|---|---|---|
| **Municipal Admin** | `admin@cleanloop.sarthakml.in` | `admin1234` |
| **Demo Citizen 1** | `citizen@cleanloop.sarthakml.in` | `demo1234` |
| **Demo Citizen 2** | `arun@cleanloop.sarthakml.in` | `demo1234` |

---

## ✨ Core Features & Platform Modules

1. **CleanLoop AI Citizen Assistant (`/ai/`)**:
   - Conversational assistant powered by Sarvam AI (`sarvam-105b`).
   - Enables natural-language reporting ("kachra pada hai", "pickup chahiye"), status queries ("WM-2026-0025 ka status?"), and complaint/pickup history.
   - Built with deterministic security: Django handles all DB actions and authentication.

2. **Citizen Portal & Gamified Rewards**:
   - Account registration, login, and personalized citizen dashboard.
   - Report waste issues with browser GPS coordinates, Leafmap pin selection, address, landmark, and photo.
   - Smart priority calculation algorithm based on issue severity and geographic complaint density.
   - Doorstep pickup requests for bulk or segregated waste (Organic, Plastic, Paper, Glass, Metal, E-Waste).
   - **CleanCoins Incentive System**: Earn +50 CleanCoins for every verified report resolved by sanitation crews.

3. **Municipal Administrator Operations Console (`/admin-portal/`)**:
   - Executive metrics: Total Users, Total Complaints, Pending/Resolved Breakdown, Pickup Requests.
   - **Ward Environmental Health Index (EHI 0-100)**: Real-time municipal sanitation score.
   - **Waste Hotspots & Predictive AI Route Dispatch**: Geographic clustering drawing Nearest-Neighbor AI Driver Route polyline across active stops.
   - Sanitation crew assignment, vehicle dispatching, and resolution report notes.

4. **Guide / Knowledge Hub (`/guide/`) & Waste Awareness (`/awareness/`)**:
   - Interactive search lookup for 3-color bin segregation rules (Green = Wet, Blue = Dry, Red/Black = E-Waste/Hazardous).
   - Detailed platform guide with sticky TOC and reading progress indicator.

5. **Community Champion Recognition (`/man-of-the-month/`)**:
   - Recognizes citizen champions with highest verified reports in the current month while strictly maintaining data privacy.

6. **System Visualizer & REST API Playground (`/visual/`)**:
   - Dark developer console with interactive REST API tester (`/api/health/`, `/api/complaints/`).
   - Live WebSocket event stream animating backend events through Django Channels.

---

## 🛠️ Tech Stack & Constraints
- **Backend**: Python 3.14, Django 6.1, SQLite3, Django Channels, Sarvam AI SDK (`sarvamai`)
- **Frontend**: Standalone HTML5 pages, Scoped CSS Variables (Light Blue + Navy Theme), Vanilla JavaScript, Leafmap / Folium / Leaflet maps
- **Deployment Compatibility**: Nginx reverse proxy, Gunicorn WSGI, Daphne ASGI, systemd, AWS EC2 Ubuntu 24.04 LTS

---

## 🚀 Quick Start (Local Setup)

```bash
# 1. Clone repository
git clone https://github.com/sarvasva-dev/spectrum.git
cd spectrum

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Or venv\Scripts\activate on Windows

# 3. Install dependencies
pip install django gunicorn pillow leafmap folium channels daphne sarvamai python-dotenv

# 4. Apply migrations
python backend/manage.py migrate

# 5. Run local development server
python backend/manage.py runserver 0.0.0.0:8000
```

---

## 🧪 Automated Testing Suite

```bash
python backend/manage.py test waste_management
```

---

## 📖 Additional Documentation
- [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md): Complete architecture, schema, user/admin workflows, and security design.
- [HACKATHON_QA.md](HACKATHON_QA.md): Comprehensive questions and answers for hackathon evaluation.
