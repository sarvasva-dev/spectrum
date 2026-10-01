# 🚀 CleanLoop Platform — Comprehensive Deep Feature Specification & Testing Protocol

This document provides a deep, exhaustive specification of every feature built into the CleanLoop Smart Waste Management Platform, detailing the exact user experience, backend architecture, algorithms, and step-by-step testing verification protocols.

---

## 📋 Table of Contents
1. [Module 1: Sarvam-105B AI Citizen Assistant (`/ai/`)](#module-1-sarvam-105b-ai-citizen-assistant-ai)
2. [Module 2: Sarvam-105B AI Municipal Control Room Assistant (`/admin-ai/`)](#module-2-sarvam-105b-ai-municipal-control-room-assistant-admin-ai)
3. [Module 3: Citizen Waste Issue Reporting & AI Image Classification (`/citizen/`)](#module-3-citizen-waste-issue-reporting--ai-image-classification-citizen)
4. [Module 4: Doorstep Waste Pickup Logistics & Scheduling (`/pickup/`)](#module-4-doorstep-waste-pickup-logistics--scheduling-pickup)
5. [Module 5: Real-Time Complaint & Pickup Tracking System (`/track/`)](#module-5-real-time-complaint--pickup-tracking-system-track)
6. [Module 6: Municipal Operations Console & Hotspot Analytics Map (`/admin-dashboard/`)](#module-6-municipal-operations-console--hotspot-analytics-map-admin-dashboard)
7. [Module 7: CleanCoins Rewards System & Community Leaderboard (`/man-of-the-month/`)](#module-7-cleancoins-rewards-system--community-leaderboard-man-of-the-month)
8. [Module 8: Zero-Touch Presentation Script Flow Automations (`/democitizenai/` & `/demoadmin/`)](#module-8-zero-touch-presentation-script-flow-automations-democitizenai--demoadmin)
9. [Module 9: System Visualizer & Live REST/WebSocket API Inspector (`/visual/`)](#module-9-system-visualizer--live-restwebsocket-api-inspector-visual)
10. [Module 10: Platform Knowledge Hub, Waste Awareness & SEO Suite (`/guide/` & `/awareness/`)](#module-10-platform-knowledge-hub-waste-awareness--seo-suite-guide--awareness)

---

## Module 1: Sarvam-105B AI Citizen Assistant (`/ai/`)

### 1.1 Deep Specification
* **URL Route**: `/ai/` (View: `api_ai_chat_view` in `views.py` / Core Logic: `ai_assistant.py`)
* **Primary Purpose**: Provides a 24/7 conversational natural-language assistant for citizens in English, Hindi, and Hinglish.
* **Core Capabilities**:
  1. **Quick Action Chips**: Provides instant action chips ("🗑 Report Waste", "🚛 Request Pickup", "📍 Track Complaint", "📦 Track Pickup", "📋 My Complaints", "📋 My Pickups", "♻ Waste Guide").
  2. **Multi-Turn State Machine**: Handles multi-step complaint creation and pickup scheduling inside the chat window.
  3. **Direct Database Queries**: Citizens can query status by typing e.g. `"WM-2026-0025 ka status?"` or `"meri last complaint ka status"`.
  4. **Sarvam AI Freeform Integration**: Connects to Sarvam AI (`sarvam-105b` model via `https://api.sarvam.ai/v1/chat/completions`) for conversational small talk ("kaise ho", "aur batao") and waste segregation advice ("plastic waste ka kya karein?").
  5. **Deterministic Security**: AI model NEVER accesses database directly; Django ORM handles all authenticated reads/writes scoped to `request.user`.

### 1.2 Testing Verification Protocol
* **Test Step 1**: Open `/ai/` and click "🗑 Report Waste".  
  * *Expected Result*: Chat responds asking for issue type with options (Overflowing Bin, Garbage on Road, etc.).
* **Test Step 2**: Type freeform text `"WM-2026-0001 ka status batao"`.  
  * *Expected Result*: Chat returns card with Complaint WM-2026-0001 details & live status.
* **Test Step 3**: Type casual Hindi/Hinglish `"plastic recycling kaise hoti hai?"`.  
  * *Expected Result*: Sarvam AI responds with concise, friendly waste segregation advice under 80 words.

---

## Module 2: Sarvam-105B AI Municipal Control Room Assistant (`/admin-ai/`)

### 2.1 Deep Specification
* **URL Route**: `/admin-ai/` (View: `api_admin_ai_chat_view` / Core Logic: `admin_ai_assistant.py`)
* **Primary Purpose**: Conversational control terminal for city sanitation officers to inspect city status and dispatch crews.
* **Core Capabilities**:
  1. **City Snapshot Query**: Typing `"city summary"` computes total registered citizens, active complaints, resolved complaints, total pickups, and city Ward EHI score.
  2. **Active Hotspots Query**: Typing `"active hotspots"` aggregates unresolved complaints by location and tags severity (🔴 Critical for >=3 complaints, 🟡 Elevated for 2, 🔵 Monitoring for 1).
  3. **Conversational Crew Dispatch**: Typing `"WM-2026-0022"` opens crew dispatch options (Alpha Crew, Bravo Team, Charlie Unit) to assign field workers and update status to `IN_PROGRESS`.
  4. **Conversational Vehicle Dispatch**: Typing `"PK-2026-0017"` enables vehicle selection (Truck A-101, Van B-202) for doorstep pickups.

### 2.2 Testing Verification Protocol
* **Test Step 1**: Log in as admin (`admin@cleanloop.sarthakml.in`) and visit `/admin-ai/`.
* **Test Step 2**: Click "📊 City Overview".  
  * *Expected Result*: Assistant returns Municipal Operations Summary card with EHI score and complaint breakdown.
* **Test Step 3**: Click "🚨 Active Hotspots".  
  * *Expected Result*: Assistant lists active waste clusters sorted by complaint count.
* **Test Step 4**: Type a complaint ID e.g. `"WM-2026-0001"`.  
  * *Expected Result*: Assistant prompts for crew assignment choices.

---

## Module 3: Citizen Waste Issue Reporting & AI Image Classification (`/citizen/`)

### 3.1 Deep Specification
* **URL Route**: `/citizen/` (View: `report_waste_view` in `views.py` / Form: `ComplaintForm` in `forms.py`)
* **Primary Purpose**: Allows citizens to report overflowing bins, road garbage, or illegal dumping with GPS geolocation, Leafmap pin, and photos.
* **Core Capabilities**:
  1. **AI Image Auto-Classifier**: JS client-side TensorFlow/heuristics pre-analyzes uploaded photos to pre-select waste category and issue severity.
  2. **Browser High-Accuracy GPS Geolocation**: 1-click button fetches latitude & longitude from device GPS and reverse geocodes address via Nominatim OpenStreetMap API.
  3. **Interactive Map Selection**: Embedded Leafmap/Leaflet map allows pinning exact location.
  4. **Automatic Priority Engine**: Sets priority to `HIGH` for illegal dumping or `CRITICAL` if complaint falls within a known 0.5km chronic hotspot.

### 3.2 Testing Verification Protocol
* **Test Step 1**: Visit `/citizen/` while logged in.
* **Test Step 2**: Click "📍 Detect Current Location".  
  * *Expected Result*: GPS coordinates fill latitude/longitude fields and reverse-geocoded address appears in address box.
* **Test Step 3**: Select Issue Type "Overflowing Bin", fill landmark, attach image, and click "Submit Report".  
  * *Expected Result*: Redirects to Complaint Tracking (`/track/`) displaying new Complaint ID (`WM-2026-XXXX`) with status `PENDING`.

---

## Module 4: Doorstep Waste Pickup Logistics & Scheduling (`/pickup/`)

### 4.1 Deep Specification
* **URL Route**: `/pickup/` (View: `pickup_request_view` / Form: `PickupRequestForm`)
* **Primary Purpose**: Enables households, societies, and commercial users to schedule doorstep collection of segregated waste.
* **Core Capabilities**:
  1. **Waste Category Selection**: Organic, Plastic, Paper, Glass, Metal, E-Waste, General Waste.
  2. **Quantity & Weight Estimation**: Input estimated weight in kg.
  3. **Date & Time Slot Scheduling**: Date picker + 4 predefined time slots (Morning 08-11 AM, Midday 11-02 PM, Afternoon 02-05 PM, Evening 05-07 PM).
  4. **My Pickups List View (`/pickup/list/`)**: Shows active and completed doorstep pickup orders with assigned vehicle info.

### 4.2 Testing Verification Protocol
* **Test Step 1**: Visit `/pickup/`.
* **Test Step 2**: Select Category "E-Waste", Weight "5", Preferred Date tomorrow, Time Slot "Morning (08:00 AM - 11:00 AM)", and click "Schedule Pickup".  
  * *Expected Result*: Redirects to `/pickup/list/` displaying new Pickup ID (`PK-2026-XXXX`) with status `PENDING`.

---

## Module 5: Real-Time Complaint & Pickup Tracking System (`/track/`)

### 5.1 Deep Specification
* **URL Route**: `/track/` and `/complaints/<id>/` (View: `complaint_tracking_view` & `complaint_detail_view`)
* **Primary Purpose**: Transparent status tracking for citizens and administrators.
* **Core Capabilities**:
  1. **Instant ID Search**: Accepts complaint ID `WM-2026-XXXX` or pickup ID `PK-2026-XXXX`.
  2. **Visual Status Progress Bar**: Visual timeline highlighting progress: `Submitted ➔ Assigned to Crew ➔ In Progress ➔ Resolved`.
  3. **Audit Trail History**: Displays `ComplaintUpdate` audit trail showing crew assignment notes and timestamps.

### 5.2 Testing Verification Protocol
* **Test Step 1**: Visit `/track/` and enter a valid ID e.g. `"WM-2026-0001"`.  
  * *Expected Result*: Renders complaint details, GPS coordinates map, priority pill, and progress timeline.

---

## Module 6: Municipal Operations Console & Hotspot Analytics Map (`/admin-dashboard/`)

### 6.1 Deep Specification
* **URL Route**: `/admin-dashboard/` (View: `admin_dashboard_view` in `views.py`)
* **Primary Purpose**: Comprehensive command dashboard for city sanitation management.
* **Core Capabilities**:
  1. **Municipal Metric Cards**: Live counters for Citizens, Total Complaints, Pending vs Resolved, and Ward EHI Score.
  2. **Environmental Health Index (EHI Score)**: Dynamic score ($100 - (\text{pending\_complaints} \times 6)$) representing city sanitation grade.
  3. **Geographic Hotspot Clustering Map**: Leaflet map grouping unresolved complaints into 0.5km cluster circles with color coding:
     - 🔴 **CRITICAL**: >= 3 active complaints in cluster
     - 🟡 **ELEVATED**: 2 active complaints
     - 🔵 **MONITORING**: 1 active complaint
  4. **Predictive AI Driver Route Dispatch**: Computes Nearest-Neighbor routing polyline connecting all active stops on map.
  5. **Bulk Status & Crew Assignment Controls**: Update complaint status (`PENDING` ➔ `IN_PROGRESS` ➔ `RESOLVED`) and assign sanitation crews directly.

### 6.2 Testing Verification Protocol
* **Test Step 1**: Log in as admin and visit `/admin-dashboard/`.  
  * *Expected Result*: Hotspot analytics map loads displaying complaint marker clusters and red/blue route lines.
* **Test Step 2**: Click "Update Status" on a pending complaint, select crew "Alpha Team", change status to `RESOLVED`, and submit.  
  * *Expected Result*: Complaint status updates to `RESOLVED`, EHI score increases, and citizen receives +50 CleanCoins.

---

## Module 7: CleanCoins Rewards System & Community Leaderboard (`/man-of-the-month/`)

### 7.1 Deep Specification
* **URL Route**: `/man-of-the-month/` (View: `man_of_the_month_view` in `views.py`)
* **Primary Purpose**: Incentivizes active civic participation through gamification.
* **Core Capabilities**:
  1. **CleanCoins Award Engine**: Automatically awards **+50 CleanCoins** to citizen's `UserProfile` when an administrator marks their complaint `RESOLVED`.
  2. **Monthly Community Leaderboard**: Displays top citizen contributors sorted by resolved reports and total CleanCoins.

### 7.2 Testing Verification Protocol
* **Test Step 1**: Log in as citizen, view dashboard at `/citizen/dashboard/` to check initial CleanCoins balance.
* **Test Step 2**: Admin resolves citizen's complaint on `/admin-dashboard/`.
* **Test Step 3**: Refresh `/citizen/dashboard/` and `/man-of-the-month/`.  
  * *Expected Result*: CleanCoins balance increases by +50 and leaderboard reflects updated count.

---

## Module 8: Zero-Touch Presentation Script Flow Automations (`/democitizenai/` & `/demoadmin/`)

### 8.1 Deep Specification
* **URL Routes**: `/democitizenai/` and `/demoadmin/` (Views: `demo_citizen_ai_view` & `demo_admin_view`)
* **Primary Purpose**: 100% automated 5-second step-advancing live presentation routes for hackathon judges.
* **Core Capabilities**:
  1. **`/democitizenai/` Flow**: Auto-waits 5 seconds ➔ Auto-registers demo citizen ➔ Opens AI Chat ➔ Reports waste issue ➔ Asks Sarvam AI waste query ➔ Shows completed flow.
  2. **`/demoadmin/` Flow**: Auto-waits 5 seconds ➔ Logs in as Municipal Admin ➔ Loads Control Dashboard ➔ Displays Hotspot Clusters ➔ Assigns Crew ➔ Resolves complaint.

### 8.2 Testing Verification Protocol
* **Test Step 1**: Open `/democitizenai/` without touching keyboard/mouse.  
  * *Expected Result*: UI automatically advances through registration, waste reporting, and Sarvam AI chat every 5 seconds.
* **Test Step 2**: Open `/demoadmin/` without touching keyboard/mouse.  
  * *Expected Result*: UI automatically advances through admin login, hotspot map loading, and crew dispatching every 5 seconds.

---

## Module 9: System Visualizer & Live REST/WebSocket API Inspector (`/visual/`)

### 9.1 Deep Specification
* **URL Route**: `/visual/` (View: `visual_view` in `views.py`)
* **Primary Purpose**: Dark developer terminal playground for technical judges to inspect system architecture.
* **Core Capabilities**:
  1. **REST API Tester**: Live GET/POST testers for `/api/health/`, `/api/complaints/`, `/api/pickups/`.
  2. **Real-time SVG Particle Animation**: Animates data flow particles across `Client ➔ Nginx ➔ ASGI ➔ Django ➔ ORM/AI ➔ SQLite`.
  3. **Live Requests/sec Chart.js Bandwidth Graph**: Displays real-time request frequency.
  4. **Django Channels WebSocket Stream**: Connects to `ws://.../ws/visualizer/` via `VisualizerConsumer`.

### 9.2 Testing Verification Protocol
* **Test Step 1**: Open `/visual/`.
* **Test Step 2**: Click "Run Live Request Sequence".  
  * *Expected Result*: API test buttons fire, status 200 OK badges light up green, latency displays in ms, and SVG particles animate across the diagram.

---

## Module 10: Platform Knowledge Hub, Waste Awareness & SEO Suite (`/guide/` & `/awareness/`)

### 10.1 Deep Specification
* **URL Routes**: `/guide/`, `/awareness/`, `/robots.txt`, `/sitemap.xml`
* **Primary Purpose**: Educates users on waste segregation and enforces technical SEO best practices.
* **Core Capabilities**:
  1. **Knowledge Hub (`/guide/`)**: Sticky Table of Contents, top progress bar, instant search, brand header, and footer.
  2. **Waste Segregation Rules (`/awareness/`)**: 3-Color Bin Guide (Green = Wet/Organic, Blue = Dry/Recyclable, Red/Black = E-Waste/Hazardous).
  3. **Full SEO Metadata**: OpenGraph social media tags, Twitter cards, SVG favicons, and Google Search `JSON-LD` structured data (`TechArticle` & `WebSite` schemas).

### 10.2 Testing Verification Protocol
* **Test Step 1**: Open `/guide/` and type `"segregation"` in search bar.  
  * *Expected Result*: Content filters instantly to show segregation sections.
* **Test Step 2**: Inspect page source of `/guide/` or `/landing.html`.  
  * *Expected Result*: Valid `<meta property="og:title">`, `<meta name="twitter:card">`, and `<script type="application/ld+json">` tags are present.

---

## 🎯 Verification Summary Matrix

| Module | Route | Primary Tech | Verification Command / URL |
|---|---|---|---|
| **Citizen AI** | `/ai/` | Sarvam AI `sarvam-105b` | GET `/ai/` |
| **Admin AI** | `/admin-ai/` | Sarvam AI + Django ORM | GET `/admin-ai/` |
| **Report Waste** | `/citizen/` | Geolocation + Leafmap + AI classifier | GET `/citizen/` |
| **Pickup Scheduling** | `/pickup/` | Django Forms + Date/Time slot picker | GET `/pickup/` |
| **Tracking** | `/track/` | Django ORM + Audit Trail | GET `/track/` |
| **Admin Control** | `/admin-dashboard/` | Leaflet Hotspots + Nearest-Neighbor Route | GET `/admin-dashboard/` |
| **CleanCoins** | `/man-of-the-month/` | UserProfile Rewards Engine | GET `/man-of-the-month/` |
| **Citizen Demo** | `/democitizenai/` | Automated 5s Presentation Script | GET `/democitizenai/` |
| **Admin Demo** | `/demoadmin/` | Automated 5s Presentation Script | GET `/demoadmin/` |
| **Visualizer** | `/visual/` | WebSockets + Chart.js + SVG Particles | GET `/visual/` |
| **Knowledge Hub** | `/guide/` | HTML5 + Progress Bar + JSON-LD SEO | GET `/guide/` |
