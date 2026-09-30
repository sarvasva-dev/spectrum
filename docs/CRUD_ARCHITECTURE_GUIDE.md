# 🛠️ CleanLoop: Complete CRUD Architecture Guide

**For Hackathon Presentation:** Use this document to quickly explain the data flow and database interactions (CRUD) of your platform to the judges. It proves that the application is fully functional and handles complex state management.

---

## 1. 👥 Citizen Profiles (User Management)
*How we handle citizens joining the platform and earning rewards.*

*   🟢 **CREATE:** 
    *   **View:** `register_view`
    *   **Action:** When a citizen registers, the system securely creates a standard Django `User` and simultaneously initializes a `UserProfile` model (to track address and `CleanCoins`).
*   🔵 **READ:** 
    *   **View:** `citizen_dashboard_view`
    *   **Action:** Fetches the logged-in citizen's profile to display their current CleanCoins balance and activity summary.
*   🟠 **UPDATE:** 
    *   **View:** `admin_complaint_update_view`
    *   **Action:** *Automated Gamification.* When an admin resolves a complaint, the backend automatically calls `user_profile.save()` to increment the citizen's `CleanCoins`.
*   🔴 **DELETE:** 
    *   **Action:** Restricted to the superuser via the standard Django `/admin/` portal to prevent accidental loss of citizen data.

---

## 2. 🗑️ Waste Complaints (The Core Engine)
*How civic issues are reported, tracked, and resolved.*

*   🟢 **CREATE:** 
    *   **View:** `report_waste_view`
    *   **Action:** Receives form data (Issue Type, GPS Coordinates). When `complaint.save()` is triggered, the backend automatically intercepts the upload to **compress the image** to WebP and generate a unique `Complaint ID`.
*   🔵 **READ:** 
    *   **View:** Multiple Views
    *   `citizen_dashboard_view` uses `Complaint.objects.filter(user=request.user)` to show only the user's active issues.
    *   `landing_view` uses `Complaint.objects.filter(status='RESOLVED')` to publicly showcase trending/resolved cases (SEO Slugs).
    *   `complaint_detail_view` fetches the exact details of a single issue.
*   🟠 **UPDATE:** 
    *   **View:** `admin_complaint_update_view`
    *   **Action:** Municipal admins change the `status` (Pending ➔ Assigned ➔ Resolved) and can update the `priority` level.
*   🔴 **DELETE:** 
    *   **Action:** Handled strictly via the Django Admin Panel to maintain data integrity and audit trails.

---

## 3. 📜 Complaint Timeline (Audit Logging)
*How we maintain 100% transparency between the municipality and the citizen.*

*   🟢 **CREATE:** 
    *   **View:** `report_waste_view` & `admin_complaint_update_view`
    *   **Action:** Uses `ComplaintUpdate.objects.create()`. Every time a complaint is filed or an admin changes its status, a new timeline entry is spawned (e.g., "Assigned to Truck #4").
*   🔵 **READ:** 
    *   **View:** `complaint_detail_view`
    *   **Action:** Reads all timeline entries related to a complaint, rendering a step-by-step progress tracker for the citizen (like a pizza delivery tracker).
*   *(Update/Delete are disabled for Audit Logs to ensure municipal accountability).*

---

## 4. 🚛 Doorstep Pickup Requests (Bulk / E-Waste)
*How citizens schedule home collection.*

*   🟢 **CREATE:** 
    *   **View:** `pickup_request_view`
    *   **Action:** Saves a new `PickupRequest` with the preferred date and waste category (e.g., E-waste, Bulk waste).
*   🔵 **READ:** 
    *   **View:** `pickup_list_view` (for Citizens) and `admin_dashboard_view` (for Admins).
    *   **Action:** Admins use `PickupRequest.objects.all()` to see a master list of all pending pickups for dispatch.
*   🟠 **UPDATE:** 
    *   **View:** `admin_pickup_update_view`
    *   **Action:** Admins update the status to `SCHEDULED` or `COMPLETED`.

---

### 💡 Pro-Tip for Pitching:
If a judge asks *"How are you handling database interactions?"*
**Your Answer:** *"We are doing full CRUD operations securely via Django's ORM. But we went a step further—our Updates are intelligent. For example, updating a complaint to 'RESOLVED' doesn't just change a string in the DB; it triggers an automatic Update to the citizen's Profile to award them CleanCoins, and it generates an Audit Log Create event simultaneously."*
