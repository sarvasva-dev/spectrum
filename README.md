# Smart Waste Management System
**Spectrum Hackathon 2026**

[![Python 3.14](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![Django 6.1](https://img.shields.io/badge/Django-6.1-green.svg)](https://www.djangoproject.com/)
[![Nginx](https://img.shields.io/badge/Nginx-Reverse%20Proxy-brightgreen.svg)](https://nginx.org/)
[![Gunicorn](https://img.shields.io/badge/Gunicorn-WSGI-orange.svg)](https://gunicorn.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> A centralized waste management and segregation platform for cities, colleges, residential societies, and public spaces.

---

## 🌐 Live Deployment
- **Live Website**: [http://16.171.238.127/](http://16.171.238.127/)
- **Municipal Admin Portal**: [http://16.171.238.127/admin-portal/](http://16.171.238.127/admin-portal/)
- **Django Superuser Admin**: [http://16.171.238.127/admin/](http://16.171.238.127/admin/)

---

## 🔑 Demo Credentials

| Role | Username / Email | Password |
|---|---|---|
| **Municipal Admin** | `admin@smartwaste.org` | `admin1234` |
| **Demo Citizen 1** | `citizen@smartwaste.org` | `demo1234` |
| **Demo Citizen 2** | `arun@smartwaste.org` | `demo1234` |

---

## ✨ Core Features

1. **Citizen Portal**:
   - Simple account registration and login (email or username).
   - Citizen dashboard with active complaint counters and quick action cards.
   - Report waste issues (Overflowing bins, Road litter, Illegal dumping, Missed collection, Improper segregation).
   - Smart priority calculation based on issue severity and location history.
   - Doorstep pickup requests for segregated recyclables (Plastic, Paper, E-waste, Glass, Metal, Organic, General).
   - Real-time complaint tracking with step-by-step progress timeline.

2. **Municipal Administrator Portal**:
   - Centralized operational statistics (Total complaints, Pending, Resolved, Total pickups).
   - Interactive complaint management: assign sanitation crews, update lifecycle status, and add dispatch notes.
   - Doorstep pickup management: assign collection vehicles and mark completed.
   - **Waste Hotspots Analytics**: Automated location-based aggregation highlighting chronic dumping zones.
   - Issue category breakdown with visual metric bars.

3. **Waste Awareness & Education**:
   - Color-coded bin segregation guidelines (Green = Wet/Organic, Blue = Dry/Recyclable, Red/Black = Hazardous/E-Waste).
   - Practical Do's and Don'ts for community members.
   - Interactive search lookup for household waste items.

---

## 🛠️ Tech Stack & Constraints
- **Backend**: Python 3.14, Django 6.1, SQLite3
- **Frontend**: HTML5, Modern Light Theme CSS3 (CSS Variables, No Bootstrap/Tailwind), Vanilla JavaScript (No Node.js/React/Vue)
- **Deployment**: Nginx 1.28 reverse proxy, Gunicorn 26.2 WSGI server, systemd process daemon (`smartwaste.service`), AWS EC2 Ubuntu 24.04 LTS

---

## 🚀 Quick Start (Local Setup)

```bash
# 1. Clone repository
git clone https://github.com/sarvasva-dev/spectrum.git
cd spectrum

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install django gunicorn pillow sqlparse asgiref

# 4. Apply migrations
python manage.py migrate

# 5. Seed demo data (creates admin and sample records)
python seed_data.py

# 6. Run local server
python manage.py runserver 0.0.0.0:8000
```

---

## 🧪 Testing Suite

Run the full automated test suite covering authentication, permissions, workflows, and edge cases:
```bash
python manage.py test
```

---

## 📖 Additional Documentation
- [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md): Complete architecture, database schema, user/admin workflows, and security design.
- [HACKATHON_QA.md](HACKATHON_QA.md): 20 comprehensive questions and answers tailored for hackathon judges.
