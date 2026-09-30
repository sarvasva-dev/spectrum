# SmartWaste Project Documentation

## Project Overview
SmartWaste is a localized waste management platform built with Django, targeting cities, residential societies, and public spaces to solve the common issue of manual waste management which leads to overflowing garbage, illegal dumping, and poor segregation. It bridges the gap between citizens reporting issues and municipal bodies acting on them.

**Tagline:** "Smarter Waste Management for Cleaner Communities"

## Architecture
This project implements a monolithic web architecture tailored for quick deployment and reliable performance in local environments or basic cloud hosting (like an EC2 instance), aligning with Hackathon requirements.

- **Backend:** Python + Django framework, handling routing, ORM abstractions, security, and authentication.
- **Frontend:** HTML5, CSS3 (using a customized Blue Light modern theme), and Vanilla JavaScript for mapping.
- **Database:** SQLite3 for lightweight, zero-configuration local development.
- **Map Integration:** Leafmap (Python) with Folium/Leaflet rendering backend.

### Structure
The codebase has been refactored into a clear separation of concerns:
1. `backend/`: Contains the Django project (`smartwaste_project/`), apps (`waste_management/`), business logic (`views.py`, `models.py`), and the `manage.py` entry point.
2. `frontend/`: Contains all static assets (`css/`, `js/`, `img/`) and HTML templates (`pages/`).
3. `media/`: Stores user uploads like images attached to complaints.

## Key Features

### Citizen Portal
- **Dashboard:** At-a-glance view of user-reported issues and requested pickups.
- **Report Waste:** Users can report illegal dumping or overflowing bins by submitting a photo and tagging the exact location on an interactive map.
- **Schedule Pickup:** Users can book a doorstep waste pickup for bulk or specialized waste.
- **Complaint Tracking:** Real-time timeline view of a complaint's status (Pending -> Assigned -> In Progress -> Resolved).

### Municipal Admin Portal
- **Dashboard:** Provides aggregate statistics (total reports, pending issues).
- **Map Visualization:** A city-wide map view plotting all active complaints and automatically identified waste "hotspots" to coordinate resources.
- **Hotspot Analytics:** Algorithms cluster complaints within a 0.5km radius to identify chronic dumping areas and suggest municipal action (e.g., placing new bins or scheduling patrols).
- **Complaint Management:** Update the status of reports and assign specific crews.
- **Logistics Management:** Route doorstep pickup requests to appropriate municipal vehicles.

## Development Setup

1. **Prerequisites:** Python 3.9+ installed.
2. **Virtual Environment:** 
   ```bash
   python -m venv venv
   source venv/bin/activate  # Or venv\Scripts\activate on Windows
   ```
3. **Install Dependencies:**
   ```bash
   pip install django pillow leafmap folium
   ```
4. **Run Server:**
   ```bash
   cd backend
   python manage.py runserver
   ```
5. **Access Application:** Visit `http://127.0.0.1:8000` in your web browser.

## Next Steps for Production
*This iteration is expressly built for LOCAL DEVELOPMENT as per Hackathon scope.* 
Future iterations will require:
1. **Production Server:** Gunicorn serving the WSGI application.
2. **Reverse Proxy:** Nginx for SSL termination and static file serving.
3. **Database Migration:** Transition from SQLite3 to PostgreSQL.
4. **Object Storage:** Use AWS S3 or GCP Cloud Storage for media files.
5. **DNS & HTTPS:** Setting up domain names and Let's Encrypt certificates.
