# CleanLoop Project Documentation

## Project Overview
CleanLoop is a localized, intelligent waste management platform built with Django, targeting cities, residential societies, and public spaces to solve manual waste management challenges. It connects citizens, sanitation crews, and municipal administrators through a centralized platform.

**Tagline:** "Smarter Waste Management for Cleaner Communities"
**Team:** Bug Busters (Spectrum Hackathon 2026)

## Architecture & Design
This project implements a modular monolithic web architecture with standalone frontend pages, REST APIs, WebSockets, and AI assistant capabilities.

- **Backend:** Python 3.14 + Django 6.1 framework handling routing, ORM abstractions, security, authentication, and REST APIs.
- **AI Assistant Integration:** Server-side Sarvam AI SDK (`sarvam-105b`) powering conversational intent classification and natural language queries at `/ai/`.
- **Frontend:** Standalone HTML5 pages with embedded Light Blue & White CSS design system tokens and Vanilla JavaScript.
- **Database:** SQLite3 for lightweight, zero-configuration local development and deterministic ORM reads/writes.
- **Map Integration:** Leafmap (Python) with Folium/Leaflet rendering backend for GPS coordinates and map pin selection.
- **Real-Time Visualizer:** Django Channels + Daphne WebSocket server broadcasting live system events.

### Structure
1. `backend/`: Django project (`smartwaste_project/`), app (`waste_management/`), business logic (`views.py`, `models.py`, `ai_assistant.py`), architecture guide (`BACKEND_ARCHITECTURE.md`), and `manage.py`.
2. `frontend/pages/`:
   - `citizen/`: `dashboard.html`, `report_waste.html`, `pickup_request.html`, `complaint_tracking.html`, `complaint_detail.html`, `pickup_list.html`, `login.html`, `register.html`
   - `admin/`: `dashboard.html`, `complaint_update.html`, `pickup_update.html`
   - `misc/`: `ai.html`, `guide.html`, `awareness.html`, `man_of_the_month.html`, `403.html`, `404.html`, `500.html`
   - Root pages: `landing.html`, `visual.html`
3. `media/`: Persistent storage directory for user-uploaded waste complaint photos (`MEDIA_ROOT`).
4. `staticfiles/`: Target production directory where `collectstatic` compiles assets served directly by Nginx on EC2 (`STATIC_ROOT`). See `docs/STORAGE_AND_ASSETS_GUIDE.md`.

## Key Features

### 1. Citizen AI Assistant (`/ai/`)
- Natural-language conversational interface supporting English, Hindi, and Hinglish.
- Quick action chips: Report Waste, Request Pickup, Track Complaint, Track Pickup, My Complaints, My Pickups, Waste Guide.
- Live database queries for complaint status ("WM-2026-0025 ka status?", "meri complaints dikhao").
- Conversational complaint and pickup creation with GPS/map pin selection and photo attachment.
- Graceful fallbacks if AI service is temporarily unavailable.

### 2. Citizen Portal & CleanCoins Rewards
- Account registration, login (username/email), and profile management.
- Report waste issues with GPS coordinates, landmark, address, and photo.
- Automatic rule-based priority calculator (HIGH for illegal dumping/overflowing bins, CRITICAL for chronic hotspots).
- Doorstep waste pickup booking with preferred date/time slots and categories.
- **CleanCoins Incentive System**: Citizens earn +50 CleanCoins whenever a verified report is marked RESOLVED by municipal staff.

### 3. Municipal Admin Operations Console (`/admin-portal/`)
- Aggregate operational metrics: Total Users, Total Complaints, Pending/Resolved, Pickup Requests.
- **Ward Environmental Health Index (EHI Score 0-100)**: Dynamic sanitation status score.
- **Waste Hotspots & Predictive AI Route Dispatch**: Automated geographic clustering (0.5km radius) drawing Nearest-Neighbor AI Driver Route polyline across active stops.
- Sanitation crew assignment, vehicle dispatching, and resolution report notes.

### 4. System Visualizer (`/visual/`)
- Dark-themed developer playground displaying real-time REST API requests, status codes, latencies, and WebSocket backend event graph.

### 5. Platform Knowledge Hub (`/guide/`) & Waste Awareness (`/awareness/`)
- Comprehensive platform guide with sticky TOC, reading progress indicator, and instant search.
- Color-coded waste segregation rules (Green = Wet/Organic, Blue = Dry/Recyclable, Red/Black = E-Waste/Hazardous).

## Security & Data Privacy
- **Role Isolation:** Citizens can only view and manage their own complaints/pickups; administrators have separate protected routes.
- **Credential Protection:** Passwords and API keys are never passed to the LLM or exposed in client state.
- **CSRF & File Validation:** CSRF token enforcement on all POST/PATCH forms and 5MB image upload size validation.
