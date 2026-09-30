# Smart Waste Management System — Technical & Project Documentation
**Spectrum Hackathon 2026**

---

## 1. Project Overview
The **Smart Waste Management System** is a centralized web platform designed for municipalities, college campuses, residential societies, and urban communities. It modernizes municipal sanitation by connecting citizens directly with waste management authorities, enabling real-time waste complaint logging, doorstep recyclable pickup scheduling, geographic hotspot analytics, and public waste segregation awareness.

- **Live URL**: `http://16.171.238.127/`
- **Admin Portal**: `http://16.171.238.127/admin-portal/`
- **Django Admin**: `http://16.171.238.127/admin/`

---

## 2. Problem Statement
Traditional municipal waste management relies on manual monitoring and disjointed communication channels (such as informal phone calls or physical visits). This leads to:
- Overflowing garbage bins that attract pests and cause severe health hazards.
- Unregulated illegal dumping on roads and empty community plots.
- Missed or inconsistent municipal garbage collection schedules.
- Low recycling rates due to lack of citizen awareness regarding wet vs. dry segregation.
- Lack of centralized tracking, leaving citizens without transparency on complaint resolution.
- Absence of spatial data, preventing municipal administrators from identifying repeat waste hotspots and allocating sanitation trucks effectively.

---

## 3. Solution
Our solution provides a unified, mobile-responsive, light-themed web portal built on a robust Python/Django backend with:
1. **Citizen Portal**:
   - One-click account creation and authentication.
   - Streamlined waste reporting with smart automated priority calculation and optional photo uploads.
   - Doorstep segregated pickup booking (organic, plastic, paper, e-waste, glass, metal, general).
   - Real-time visual tracking of complaints (`PENDING` → `ASSIGNED` → `IN PROGRESS` → `RESOLVED`) with an immutable timeline audit trail.
2. **Municipal Administrator Portal**:
   - Top-level operational metrics (total complaints, pending, resolved, total pickups).
   - Filterable, searchable complaints table with crew assignment and status updates.
   - Pickup management dashboard for vehicle dispatch.
   - Automated **Waste Hotspot Analytics** that aggregate complaints by location to detect chronic dumping zones.
3. **Interactive Waste Awareness Section**:
   - Clear visual color-coded bin guide (Green = Wet/Organic, Blue = Dry/Recyclable, Red/Black = Hazardous/E-Waste).
   - Practical Do's and Don'ts for community members.
   - Instant search tool for household waste items with proper bin disposal advice.

---

## 4. Features

### Citizen Features
- **User Registration & Secure Login**: Full name, email, phone number, and residential address with Django session authentication.
- **Citizen Dashboard**: High-level counters for personal reports, active pickups, recent activity feed, and quick action cards.
- **Report Waste Issue**:
  - Issue categories: *Overflowing Bin*, *Garbage on Road*, *Illegal Dumping*, *Missed Collection*, *Improper Waste Segregation*, *Other*.
  - Rule-based smart priority assessment (*Critical*, *High*, *Medium*, *Low*).
  - Photo attachment support with server-side size validation.
  - Automatic sequential complaint ID generation (`WM-2026-0001`).
- **Complaint Tracking & Timeline**:
  - Detailed view with visual status badge and municipal dispatch notes.
  - Step-by-step progress timeline logging every transition.
  - Strict privacy: Citizens can only inspect their own records.
- **Doorstep Pickup Request**:
  - Select category (Organic, Plastic, Paper, E-waste, Glass, Metal, General, Other).
  - Specify quantity, doorstep address, preferred date, time slot, and notes.
  - Auto-generated sequential pickup ID (`PK-2026-0001`).
- **Interactive Segregation Guide**:
  - Comprehensive guide on 6 core waste types + hazardous/e-waste precautions.

### Administrator Features
- **Centralized Metrics**: Real-time counts of users, complaints, resolution rate, and completed pickups.
- **Complaint Dispatch Center**:
  - Search by complaint ID, location, citizen name, or keywords.
  - Filter by lifecycle status.
  - Assign sanitation crews or vehicles.
  - Update status and append public/internal notes.
- **Doorstep Pickup Dispatch**:
  - Assign collection trucks and driver details.
  - Transition status from `REQUESTED` → `ASSIGNED` → `PICKED UP` → `COMPLETED`.
- **Waste Hotspot Aggregation**:
  - Calculates complaint density by location string.
  - Automatically flags locations with $\ge 4$ reports as *High Activity (Critical)*, $\ge 2$ as *Moderate Activity*, and $< 2$ as *Low Activity*.
- **Category Analytics**:
  - Visual percentage breakdown of complaint volume by issue type.

---

## 5. Tech Stack
- **Backend**: Python 3.14 + Django 6.1
- **Database**: SQLite3 (zero-configuration, embedded ACID relational engine)
- **Frontend**: Semantic HTML5, Custom CSS3 with CSS variables (Light Theme), Vanilla JavaScript (No heavyweight frameworks)
- **WSGI Server**: Gunicorn 26.2 (3 worker processes)
- **Reverse Proxy / Web Server**: Nginx 1.28
- **Process Supervision**: Linux systemd (`smartwaste.service`)
- **Hosting**: AWS EC2 (Ubuntu 24.04 LTS)

---

## 6. System Architecture

```text
               [ Internet / Public Clients ]
                             │
                             ▼
                     [ AWS EC2 Instance ]
                     [ 16.171.238.127:80 ]
                             │
                             ▼
                   [ Nginx Reverse Proxy ]
               ┌─────────────┴─────────────┐
        (Static & Media)              (Dynamic Requests)
               │                             │
               ▼                             ▼
    [ /staticfiles /media ]        [ Gunicorn WSGI :8000 ]
                                             │
                                             ▼
                                     [ Django Application ]
                                   (waste_management app)
                                             │
                                             ▼
                                     [ SQLite3 Database ]
                                      (db.sqlite3 file)
```

---

## 7. Database Design

### `UserProfile`
- `user`: OneToOneField (`django.contrib.auth.models.User`)
- `phone`: CharField(max_length=20)
- `address`: CharField(max_length=255)
- `is_admin_staff`: BooleanField(default=False)
- `created_at`: DateTimeField(auto_now_add=True)

### `Complaint`
- `complaint_id`: CharField(max_length=30, unique=True, indexed) — e.g. `WM-2026-0001`
- `user`: ForeignKey (`User`, related_name='complaints')
- `issue_type`: CharField (choices: `OVERFLOWING_BIN`, `GARBAGE_ON_ROAD`, `ILLEGAL_DUMPING`, `MISSED_COLLECTION`, `IMPROPER_SEGREGATION`, `OTHER`)
- `description`: TextField
- `location`: CharField(max_length=255)
- `landmark`: CharField(max_length=255, blank=True)
- `image`: ImageField(upload_to='complaints/%Y/%m/', blank=True, null=True)
- `priority`: CharField (choices: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
- `status`: CharField (choices: `PENDING`, `ASSIGNED`, `IN_PROGRESS`, `RESOLVED`)
- `assigned_crew`: CharField(max_length=120, blank=True)
- `admin_notes`: TextField(blank=True)
- `created_at`, `updated_at`, `resolved_at`: DateTimeFields

### `ComplaintUpdate`
- `complaint`: ForeignKey (`Complaint`, related_name='timeline_updates')
- `status`: CharField(max_length=20)
- `note`: TextField
- `updated_by`: ForeignKey (`User`, null=True)
- `created_at`: DateTimeField(auto_now_add=True)

### `PickupRequest`
- `pickup_id`: CharField(max_length=30, unique=True, indexed) — e.g. `PK-2026-0001`
- `user`: ForeignKey (`User`, related_name='pickup_requests')
- `waste_category`: CharField (choices: `ORGANIC`, `PLASTIC`, `PAPER`, `E_WASTE`, `GLASS`, `METAL`, `GENERAL`, `OTHER`)
- `quantity`: CharField(max_length=100)
- `pickup_address`: TextField
- `preferred_date`: DateField
- `preferred_time`: CharField(max_length=50)
- `notes`: TextField(blank=True)
- `status`: CharField (choices: `REQUESTED`, `ASSIGNED`, `PICKED_UP`, `COMPLETED`)
- `assigned_vehicle`: CharField(max_length=100, blank=True)
- `admin_notes`: TextField(blank=True)
- `created_at`, `updated_at`: DateTimeFields

---

## 8. User Flow
1. Citizen visits landing page `http://16.171.238.127/`.
2. Citizen registers at `/register/` or logs in at `/login/`.
3. System redirects authenticated citizen to `/dashboard/`.
4. Citizen clicks **Report Waste** (`/report/`):
   - Fills in issue type, description, location, and uploads a photo.
   - Form shows dynamic smart priority guidance.
   - On submission, user receives a unique `WM-2026-XXXX` ID and is redirected to the detail page.
5. Citizen clicks **Doorstep Pickup** (`/pickup/`):
   - Selects waste category, quantity, pickup date, and time slot.
   - Form shows live disposal guidance for the selected category.
   - On submission, user receives a `PK-2026-XXXX` ID.
6. Citizen tracks active complaints and pickups under `/tracking/` and `/pickup/list/`.

---

## 9. Admin Flow
1. Municipal Officer logs in using admin credentials (`admin@smartwaste.org`).
2. System detects staff status and redirects to `/admin-portal/`.
3. Admin views high-level operations metrics, repeat waste hotspots, and issue category distributions.
4. Admin opens complaint details, assigns sanitation truck/crew (e.g. `Truck #4 - South Zone`), updates status to `ASSIGNED` or `IN_PROGRESS`, and saves.
5. When sanitation work finishes, admin marks status as `RESOLVED`.
6. Admin updates pickup requests to `ASSIGNED` and marks `COMPLETED` upon doorstep collection.

---

## 10. Complaint Flow
```text
[ Citizen Reports Issue ]
         │ (Auto-assigns WM-YYYY-NNNN & Smart Priority)
         ▼
     [ PENDING ] ────── Initial submission; awaiting municipal dispatcher review
         │
         ▼
    [ ASSIGNED ] ────── Sanitation crew/vehicle allocated to location
         │
         ▼
  [ IN PROGRESS ] ───── Field crew actively clearing garbage
         │
         ▼
    [ RESOLVED ] ────── Site cleared; resolved_at timestamp logged
```

---

## 11. Pickup Flow
```text
[ Citizen Requests Doorstep Collection ]
         │ (Auto-assigns PK-YYYY-NNNN)
         ▼
    [ REQUESTED ] ───── New doorstep pickup logged in municipal queue
         │
         ▼
    [ ASSIGNED ] ────── Collection vehicle scheduled for specified time slot
         │
         ▼
   [ PICKED UP ] ───── Crew arrived, weighed, and collected segregated waste
         │
         ▼
   [ COMPLETED ] ───── Recyclables transported to recovery facility
```

---

## 12. Security
- **Django Authentication**: Standard PBKDF2 with SHA-256 password hashing; zero plaintext credentials.
- **CSRF Protection**: All POST forms include `{% csrf_token %}` with trusted origins configured for the EC2 IP.
- **Strict Data Isolation**: SQL queries filter by `user=request.user` on all citizen views to prevent IDOR (Insecure Direct Object Reference).
- **Access Control**: `@login_required` on citizen pages; `@user_passes_test(is_staff_or_admin)` on all municipal portal pages.
- **Upload Validation**: File size capped at 5 MB; images validated via Pillow library.
- **Production Hardening**: `DEBUG=False` in systemd service; secret key read from environment.

---

## 13. Deployment
- **Directory**: `/home/ubuntu/spectrum`
- **Virtual Environment**: `/home/ubuntu/spectrum/venv`
- **Systemd Daemon**: `/etc/systemd/system/smartwaste.service`
  - Runs Gunicorn on `127.0.0.1:8000` with 3 workers under user `ubuntu`.
- **Nginx Reverse Proxy**: `/etc/nginx/sites-available/smartwaste`
  - Listens on port 80.
  - Serves static files directly from `/home/ubuntu/spectrum/staticfiles/`.
  - Serves uploaded media from `/home/ubuntu/spectrum/media/`.
  - Reverse proxies dynamic requests to Gunicorn.

---

## 14. Future Scope
1. **Computer Vision Waste Classifier**: Edge/cloud image classification to automatically identify garbage overflow and segment plastic vs. organic from photos.
2. **Dynamic Route Optimization**: Integrate open-source routing (e.g. OSRM) to plan optimal collection truck paths based on active hotspots.
3. **IoT Smart Bin Telemetry**: Integrate ultrasonic bin fill-level sensors reporting via MQTT/HTTP.
4. **Citizen Reward Points / Green Credits**: Gamification awarding redeemable credits for verified dry waste segregation.
5. **Multi-language Support**: Localization for regional Indian and international languages.
