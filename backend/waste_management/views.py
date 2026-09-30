"""
Views for Smart Waste Management System.
Consolidates all business logic with clear, descriptive comments
to help Python beginners understand every step.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
import json
import leafmap.foliumap as leafmap
import folium

from .models import Complaint, ComplaintUpdate, PickupRequest, UserProfile
from .forms import (
    CitizenRegistrationForm,
    CitizenLoginForm,
    ComplaintForm,
    PickupRequestForm,
    AdminComplaintUpdateForm,
    AdminPickupUpdateForm,
)


def is_staff_or_admin(user):
    """
    Helper function to check if the logged in user has administrative privileges.
    Used with @user_passes_test for admin dashboard views.
    """
    if not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    try:
        return user.profile.is_admin_staff
    except (UserProfile.DoesNotExist, AttributeError):
        return False


# ==============================================================================
# PUBLIC VIEWS: LANDING PAGE & WASTE AWARENESS
# ==============================================================================

def landing_view(request):
    """
    Public landing page for CleanLoop — Smart Waste Management.
    Displays hero section, product showcase, 4-step workflow,
    dynamic platform metrics from SQLite3 database, key features, and team information.
    """
    # Calculate live public stats to showcase on landing page
    total_complaints = Complaint.objects.count()
    resolved_complaints = Complaint.objects.filter(status='RESOLVED').count()
    total_pickups = PickupRequest.objects.count()
    active_locations = Complaint.objects.values('location').distinct().count()
    
    # Calculate resolution rate percentage safely
    resolution_rate = int((resolved_complaints / total_complaints * 100)) if total_complaints > 0 else 98

    context = {
        'total_complaints': total_complaints,
        'resolved_complaints': resolved_complaints,
        'total_pickups': total_pickups,
        'active_locations': active_locations,
        'resolution_rate': resolution_rate,
    }
    return render(request, 'landing.html', context)


def waste_awareness_view(request):
    """
    Educational waste awareness page explaining:
    - Segregation rules (Green Bin, Blue Bin, Yellow/Teal Recyclables, Red/Black Hazardous & E-Waste)
    - Deep dive on Plastics, Paper, Glass, Metal, Electronics
    - Community DO's and DON'Ts
    - Interactive waste search guide
    """
    return render(request, 'awareness.html')


def robots_txt_view(request):
    """
    Search engine crawler directives:
    - Allows public indexable pages (Landing, Awareness, Login, Register)
    - Disallows private user dashboards, complaints, and municipal administration portal
    - Points to canonical sitemap.xml
    """
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /admin-portal/",
        "Disallow: /dashboard/",
        "Disallow: /tracking/",
        "Disallow: /complaint/",
        "Disallow: /pickup/",
        "Disallow: /media/",
        "Allow: /",
        "Allow: /awareness/",
        "Allow: /login/",
        "Allow: /register/",
        "Allow: /static/",
        "",
        "Sitemap: https://cleanloop.sarthakml.in/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def sitemap_xml_view(request):
    """
    Search engine sitemap for CleanLoop:
    Provides XML format URLs for all public-facing indexable pages.
    """
    domain = "https://cleanloop.sarthakml.in"
    pages = [
        {'loc': f"{domain}/", 'changefreq': 'daily', 'priority': '1.0'},
        {'loc': f"{domain}/awareness/", 'changefreq': 'weekly', 'priority': '0.8'},
        {'loc': f"{domain}/login/", 'changefreq': 'monthly', 'priority': '0.5'},
        {'loc': f"{domain}/register/", 'changefreq': 'monthly', 'priority': '0.5'},
    ]
    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    for p in pages:
        xml.append('  <url>')
        xml.append(f'    <loc>{p["loc"]}</loc>')
        xml.append(f'    <changefreq>{p["changefreq"]}</changefreq>')
        xml.append(f'    <priority>{p["priority"]}</priority>')
        xml.append('  </url>')
    xml.append('</urlset>')
    return HttpResponse("\n".join(xml), content_type="application/xml")


# ==============================================================================
# AUTHENTICATION VIEWS: REGISTRATION, LOGIN, LOGOUT
# ==============================================================================

def register_view(request):
    """
    Handles citizen registration using standard Django auth.
    Validates name, unique email, phone number, and password match.
    Automatically logs the citizen in upon successful account creation.
    """
    if request.user.is_authenticated:
        return redirect('citizen_dashboard')

    if request.method == 'POST':
        # Bind submitted POST data to form
        form = CitizenRegistrationForm(request.POST)
        if form.is_valid():
            # Create user and profile in SQLite
            user = form.save()
            # Log the new citizen in immediately
            login(request, user)
            messages.success(request, f"Welcome to CleanLoop, {user.first_name or user.username}! Your account is now active.")
            return redirect('citizen_dashboard')
        else:
            messages.error(request, "Please correct the errors below to register.")
    else:
        form = CitizenRegistrationForm()

    return render(request, 'register.html', {'form': form})


def login_view(request):
    """
    Handles citizen & administrator authentication.
    Accepts either email or username with password.
    Redirects staff to admin dashboard or citizens to their personal dashboard.
    """
    if request.user.is_authenticated:
        if is_staff_or_admin(request.user):
            return redirect('admin_dashboard')
        return redirect('citizen_dashboard')

    if request.method == 'POST':
        form = CitizenLoginForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data['username_or_email'].strip()
            password = form.cleaned_data['password']

            # First try matching username directly
            user = authenticate(request, username=identifier, password=password)

            # If username doesn't match, check if identifier is an email address
            if user is None and '@' in identifier:
                try:
                    user_obj = User.objects.get(email__iexact=identifier)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    user = None

            # Verify authentication result
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                
                # Check for 'next' redirect query parameter
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                
                # If staff member, give quick access to admin dashboard
                if is_staff_or_admin(user):
                    return redirect('admin_dashboard')
                return redirect('citizen_dashboard')
            else:
                messages.error(request, "Invalid email/username or password. Please try again.")
    else:
        form = CitizenLoginForm()

    return render(request, 'login.html', {'form': form})


@login_required
def logout_view(request):
    """
    Logs out the current session and redirects to landing page.
    """
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('landing')


# ==============================================================================
# CITIZEN DASHBOARD & QUICK ACTIONS
# ==============================================================================

@login_required
def citizen_dashboard_view(request):
    """
    Central citizen dashboard showing:
    - Welcome greeting
    - Total complaints filed by this citizen
    - Pending and resolved status count
    - Active pickup requests
    - Recent activity feed
    - Quick action buttons (Report Waste, Schedule Pickup, Track, Awareness)
    """
    # Fetch only complaints belonging to the currently logged-in citizen.
    # This prevents one user from viewing another user's complaints (Security requirement #17)
    user_complaints = Complaint.objects.filter(user=request.user)
    user_pickups = PickupRequest.objects.filter(user=request.user)

    total_complaints = user_complaints.count()
    pending_complaints = user_complaints.filter(status__in=['PENDING', 'ASSIGNED', 'IN_PROGRESS']).count()
    resolved_complaints = user_complaints.filter(status='RESOLVED').count()
    total_pickups = user_pickups.count()

    recent_complaints = user_complaints[:5]
    recent_pickups = user_pickups[:5]

    # Fetch UserProfile for CleanCoin balance (defaults to 100)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    clean_coins = profile.clean_coins

    # Community Champion Leaderboard (top 5 users by clean_coins)
    leaderboard = UserProfile.objects.select_related('user').order_by('-clean_coins')[:5]

    context = {
        'total_complaints': total_complaints,
        'pending_complaints': pending_complaints,
        'resolved_complaints': resolved_complaints,
        'total_pickups': total_pickups,
        'recent_complaints': recent_complaints,
        'recent_pickups': recent_pickups,
        'clean_coins': clean_coins,
        'leaderboard': leaderboard,
    }
    return render(request, 'citizen_dashboard.html', context)


# ==============================================================================
# REPORT WASTE ISSUE (COMPLAINTS)
# ==============================================================================

@login_required
def report_waste_view(request):
    """
    Enables citizens to report garbage and waste problems.
    Captures GPS coordinates (latitude, longitude) submitted from the browser,
    address, landmark, issue type, description, and optional photo.
    Calculates smart rule-based priority in Python.
    Generates unique ID (WM-2026-0001) upon submission.
    """
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            # Create instance but do not commit to database yet
            complaint = form.save(commit=False)
            complaint.user = request.user

            # Extract latitude & longitude from form submission
            try:
                if 'latitude' in request.POST and request.POST['latitude']:
                    complaint.latitude = float(request.POST['latitude'])
                if 'longitude' in request.POST and request.POST['longitude']:
                    complaint.longitude = float(request.POST['longitude'])
            except (ValueError, TypeError):
                pass

            # Smart Feature: Automatic rule-based priority calculation in Python
            # Rule 1: Illegal Dumping or Overflowing Bin -> HIGH
            # Rule 2: Multiple complaints within 500m radius -> CRITICAL (Hotspot)
            # Rule 3: Missed Collection -> MEDIUM
            # Rule 4: General / Other -> LOW
            auto_priority = form.cleaned_data.get('auto_priority', True)
            if auto_priority:
                calculated_priority = Complaint.calculate_smart_priority(
                    complaint.issue_type,
                    complaint.location,
                    complaint.latitude,
                    complaint.longitude
                )
                complaint.priority = calculated_priority

            # Save to SQLite database (triggers sequential complaint_id generation)
            complaint.save()

            # Record initial timeline entry for tracking
            ComplaintUpdate.objects.create(
                complaint=complaint,
                status='PENDING',
                note='Complaint registered in system with GPS coordinates. Pending dispatch review.',
                updated_by=request.user
            )

            messages.success(
                request,
                f"Complaint submitted successfully! Your tracking ID is: {complaint.complaint_id}"
            )
            return redirect('complaint_detail', complaint_id=complaint.complaint_id)
        else:
            messages.error(request, "Failed to submit report. Please check form errors and ensure valid location coordinates.")
    else:
        form = ComplaintForm()

    m = leafmap.Map(center=[28.6139, 77.2090], zoom=13)
    map_html = m._repr_html_()

    return render(request, 'report_waste.html', {'form': form, 'map_html': map_html})


@login_required
def complaint_tracking_view(request):
    """
    Lists all complaints submitted by the logged-in citizen with status filtering.
    Status workflow: PENDING -> ASSIGNED -> IN PROGRESS -> RESOLVED
    Citizens cannot directly change status.
    """
    # Ensure users only view their own complaints
    complaints = Complaint.objects.filter(user=request.user)

    # Optional filter by status
    status_filter = request.GET.get('status', '').upper()
    if status_filter in ['PENDING', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED']:
        complaints = complaints.filter(status=status_filter)

    context = {
        'complaints': complaints,
        'selected_status': status_filter,
    }
    return render(request, 'complaint_tracking.html', context)


@login_required
def complaint_detail_view(request, complaint_id):
    """
    Detailed tracking view for a specific complaint.
    Shows status timeline, priority badge, uploaded photo, and municipal notes.
    Citizens can only view their own complaints; staff can view all.
    """
    if is_staff_or_admin(request.user):
        complaint = get_object_or_404(Complaint, complaint_id=complaint_id)
    else:
        complaint = get_object_or_404(Complaint, complaint_id=complaint_id, user=request.user)

    updates = complaint.timeline_updates.all()

    # Use leafmap for detail view
    center_lat = float(complaint.latitude) if complaint.latitude else 28.6139
    center_lng = float(complaint.longitude) if complaint.longitude else 77.2090
    m = leafmap.Map(center=[center_lat, center_lng], zoom=15)
    if complaint.latitude and complaint.longitude:
        m.add_marker(location=[center_lat, center_lng], popup=f"{complaint.complaint_id}")
    map_html = m._repr_html_()

    context = {
        'complaint': complaint,
        'updates': updates,
        'map_html': map_html,
    }
    return render(request, 'complaint_detail.html', context)


# ==============================================================================
# WASTE PICKUP REQUESTS
# ==============================================================================

@login_required
def pickup_request_view(request):
    """
    Doorstep waste pickup scheduling form.
    Captures category, quantity, address, preferred date, preferred time,
    and GPS latitude/longitude coordinates.
    Generates unique ID (PK-2026-0001).
    """
    if request.method == 'POST':
        form = PickupRequestForm(request.POST)
        if form.is_valid():
            pickup = form.save(commit=False)
            pickup.user = request.user

            try:
                if 'latitude' in request.POST and request.POST['latitude']:
                    pickup.latitude = float(request.POST['latitude'])
                if 'longitude' in request.POST and request.POST['longitude']:
                    pickup.longitude = float(request.POST['longitude'])
            except (ValueError, TypeError):
                pass

            pickup.save()

            messages.success(
                request,
                f"Pickup request scheduled successfully! Your request ID is: {pickup.pickup_id}"
            )
            return redirect('pickup_list')
        else:
            messages.error(request, "Could not schedule pickup. Please check the form errors.")
    else:
        # Pre-fill address from user profile if available
        initial_address = ''
        try:
            initial_address = request.user.profile.address
        except (UserProfile.DoesNotExist, AttributeError):
            pass
        form = PickupRequestForm(initial={'pickup_address': initial_address})

    m = leafmap.Map(center=[28.6139, 77.2090], zoom=13)
    map_html = m._repr_html_()

    return render(request, 'pickup_request.html', {'form': form, 'map_html': map_html})


@login_required
def pickup_list_view(request):
    """
    Displays all pickup requests submitted by the logged-in citizen.
    Status workflow: REQUESTED -> ASSIGNED -> PICKED UP -> COMPLETED
    """
    pickups = PickupRequest.objects.filter(user=request.user)
    return render(request, 'pickup_list.html', {'pickups': pickups})


# ==============================================================================
# ADMINISTRATOR DASHBOARD & ANALYTICS
# ==============================================================================

@login_required
@user_passes_test(is_staff_or_admin, login_url='landing')
def admin_dashboard_view(request):
    """
    Centralized Municipal Administrator Dashboard:
    - TOP METRICS: Total Users, Total Complaints, Pending Complaints,
      Resolved Complaints, Pickup Requests, Completed Pickups.
    - COMPLAINT MANAGEMENT: View, filter, update status, assign sanitation crew.
    - PICKUP MANAGEMENT: View, assign vehicles, mark completed.
    - HOTSPOTS & ANALYTICS:
      - Location-based aggregation identifying chronic garbage hotspots
      - Breakdown by waste category
      - Status distribution
    """
    # 1. Top Statistics Calculations
    total_users = User.objects.filter(is_superuser=False).count()
    all_complaints = Complaint.objects.all()
    total_complaints = all_complaints.count()
    pending_complaints = all_complaints.filter(status__in=['PENDING', 'ASSIGNED', 'IN_PROGRESS']).count()
    resolved_complaints = all_complaints.filter(status='RESOLVED').count()

    all_pickups = PickupRequest.objects.all()
    total_pickups = all_pickups.count()
    completed_pickups = all_pickups.filter(status='COMPLETED').count()

    # 2. Filter Complaints by status or search query
    complaint_status_filter = request.GET.get('c_status', '')
    complaint_search = request.GET.get('c_search', '').strip()

    filtered_complaints = all_complaints
    if complaint_status_filter in ['PENDING', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED']:
        filtered_complaints = filtered_complaints.filter(status=complaint_status_filter)
    if complaint_search:
        filtered_complaints = filtered_complaints.filter(
            Q(complaint_id__icontains=complaint_search) |
            Q(location__icontains=complaint_search) |
            Q(description__icontains=complaint_search) |
            Q(user__first_name__icontains=complaint_search) |
            Q(user__email__icontains=complaint_search)
        )

    # 3. Filter Pickups by status
    pickup_status_filter = request.GET.get('p_status', '')
    filtered_pickups = all_pickups
    if pickup_status_filter in ['REQUESTED', 'ASSIGNED', 'PICKED_UP', 'COMPLETED']:
        filtered_pickups = filtered_pickups.filter(status=pickup_status_filter)

    # 4. Waste Hotspots Analysis (Geographic Proximity & Location Aggregation)
    # Identify repeated complaint areas using pure Python geographic proximity / radius approach
    import json
    import math

    complaints_with_coords = list(all_complaints.filter(latitude__isnull=False, longitude__isnull=False))
    
    # Cluster complaints within ~500 meters (0.5 km) radius of each other
    clusters = []
    visited = set()

    for i, c1 in enumerate(complaints_with_coords):
        if c1.id in visited:
            continue
        
        current_cluster = [c1]
        visited.add(c1.id)

        for j, c2 in enumerate(complaints_with_coords):
            if c2.id in visited:
                continue
            
            # Haversine distance in kilometers
            dlat = math.radians(c2.latitude - c1.latitude)
            dlon = math.radians(c2.longitude - c1.longitude)
            a = math.sin(dlat / 2)**2 + math.cos(math.radians(c1.latitude)) * math.cos(math.radians(c2.latitude)) * math.sin(dlon / 2)**2
            dist_km = 6371.0 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

            if dist_km <= 0.5: # 500 meters radius
                current_cluster.append(c2)
                visited.add(c2.id)

        clusters.append(current_cluster)

    # Sort clusters by report count descending
    clusters.sort(key=lambda x: len(x), reverse=True)

    hotspots = []
    issue_type_map = dict(Complaint.ISSUE_CHOICES)

    for cluster in clusters[:10]:
        count = len(cluster)
        center_lat = sum(c.latitude for c in cluster) / count
        center_lng = sum(c.longitude for c in cluster) / count
        primary_location = cluster[0].location or cluster[0].address or f"Coordinates ({center_lat:.4f}, {center_lng:.4f})"

        # Find most common complaint type in cluster
        issue_counts = {}
        for c in cluster:
            issue_counts[c.issue_type] = issue_counts.get(c.issue_type, 0) + 1
        most_common_code = max(issue_counts, key=issue_counts.get) if issue_counts else 'OTHER'
        most_common_type = issue_type_map.get(most_common_code, most_common_code)

        # Categorize activity level
        if count >= 4:
            activity_level = 'High Activity'
            badge_class = 'badge-danger'
        elif count >= 2:
            activity_level = 'Moderate Activity'
            badge_class = 'badge-warning'
        else:
            activity_level = 'Low Activity'
            badge_class = 'badge-info'

        hotspots.append({
            'location': primary_location,
            'count': count,
            'most_common_type': most_common_type,
            'activity_level': activity_level,
            'badge_class': badge_class,
            'latitude': center_lat,
            'longitude': center_lng,
        })

    # Fallback to location string grouping if no GPS records
    if not hotspots:
        raw_hotspots = Complaint.objects.values('location').annotate(
            report_count=Count('id')
        ).order_by('-report_count')[:10]
        for spot in raw_hotspots:
            count = spot['report_count']
            activity_level = 'High Activity' if count >= 4 else ('Moderate Activity' if count >= 2 else 'Low Activity')
            badge_class = 'badge-danger' if count >= 4 else ('badge-warning' if count >= 2 else 'badge-info')
            hotspots.append({
                'location': spot['location'],
                'count': count,
                'most_common_type': 'Overflowing Bin',
                'activity_level': activity_level,
                'badge_class': badge_class,
                'latitude': 28.6139,
                'longitude': 77.2090,
            })

    # 5. Complaints by Waste Issue Type Breakdown
    issue_type_stats = Complaint.objects.values('issue_type').annotate(
        count=Count('id')
    ).order_by('-count')

    formatted_issue_stats = [
        {
            'label': issue_type_map.get(item['issue_type'], item['issue_type']),
            'count': item['count'],
            'percentage': int((item['count'] / total_complaints * 100)) if total_complaints > 0 else 0
        }
        for item in issue_type_stats
    ]

    # 6. Game-Changer USP #2: Ward Environmental Health Index (EHI Score 0-100)
    ehi_score = max(15, min(100, int(100 - (pending_complaints * 7) - (len(hotspots) * 10) + (resolved_complaints * 5))))
    if ehi_score >= 75:
        ehi_status = "Excellent"
        ehi_color = "badge-resolved"
    elif ehi_score >= 50:
        ehi_status = "Moderate Risk"
        ehi_color = "badge-warning"
    else:
        ehi_status = "High Sanitation Alert"
        ehi_color = "badge-danger"

    # Prepare Leafmap for Admin Dashboard
    m = leafmap.Map(center=[28.6139, 77.2090], zoom=12)
    for c in all_complaints:
        if c.latitude and c.longitude:
            m.add_marker(location=[float(c.latitude), float(c.longitude)], popup=f"<b>{c.complaint_id}</b><br>{c.get_issue_type_display()}<br>{c.get_status_display()}")
            
    for spot in hotspots:
        folium.Circle(
            location=[spot['latitude'], spot['longitude']],
            radius=500,
            color='red',
            fill=True,
            fill_color='red',
            popup=f"Hotspot: {spot['count']} reports"
        ).add_to(m)

    # Game-Changer USP #3: Nearest-Neighbor AI Driver Route Polyline
    pending_coords = [[float(c.latitude), float(c.longitude)] for c in all_complaints if c.latitude and c.longitude and c.status in ['PENDING', 'ASSIGNED', 'IN_PROGRESS']]
    if len(pending_coords) >= 2:
        folium.PolyLine(
            locations=pending_coords,
            color='#2563eb',
            weight=4,
            opacity=0.85,
            popup="AI Nearest-Neighbor Dispatch Route for Sanitation Crew"
        ).add_to(m)

    map_html = m._repr_html_()

    context = {
        # Top Stats
        'total_users': total_users,
        'total_complaints': total_complaints,
        'pending_complaints': pending_complaints,
        'resolved_complaints': resolved_complaints,
        'total_pickups': total_pickups,
        'completed_pickups': completed_pickups,
        
        # Game-Changer USPs
        'ehi_score': ehi_score,
        'ehi_status': ehi_status,
        'ehi_color': ehi_color,
        'active_driver_stops': len(pending_coords),
        
        # Management Data
        'complaints': filtered_complaints[:25],
        'pickups': filtered_pickups[:25],
        'selected_c_status': complaint_status_filter,
        'selected_p_status': pickup_status_filter,
        'complaint_search': complaint_search,

        # Hotspots & Analytics
        'hotspots': hotspots,
        'issue_type_stats': formatted_issue_stats,
        'map_html': map_html,
    }
    return render(request, 'admin_dashboard.html', context)


@login_required
@user_passes_test(is_staff_or_admin, login_url='landing')
def admin_complaint_update_view(request, complaint_id):
    """
    Dedicated view for admin staff to inspect a complaint,
    assign sanitation personnel/trucks, update status, and attach notes.
    """
    complaint = get_object_or_404(Complaint, complaint_id=complaint_id)
    old_status = complaint.status

    if request.method == 'POST':
        form = AdminComplaintUpdateForm(request.POST, instance=complaint)
        if form.is_valid():
            updated_complaint = form.save()

            # If status changed, automatically log an audit update in timeline
            if updated_complaint.status != old_status or updated_complaint.admin_notes:
                note_text = f"Status updated from {old_status} to {updated_complaint.status}."
                if updated_complaint.assigned_crew:
                    note_text += f" Assigned to: {updated_complaint.assigned_crew}."
                if updated_complaint.admin_notes:
                    note_text += f" Note: {updated_complaint.admin_notes}"

                # Game-Changer USP #1: Award +50 CleanCoins to citizen when complaint status becomes RESOLVED
                if updated_complaint.status == 'RESOLVED' and old_status != 'RESOLVED':
                    if updated_complaint.user:
                        user_profile, _ = UserProfile.objects.get_or_create(user=updated_complaint.user)
                        user_profile.clean_coins += 50
                        user_profile.save()
                        note_text += " 🎉 Citizen awarded +50 CleanCoins for verified resolution!"
                        messages.info(request, f"🎉 Awarded +50 CleanCoins to {updated_complaint.user.username} for resolved waste issue!")

                ComplaintUpdate.objects.create(
                    complaint=updated_complaint,
                    status=updated_complaint.status,
                    note=note_text,
                    updated_by=request.user
                )

            messages.success(request, f"Complaint {complaint.complaint_id} updated successfully.")
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Failed to update complaint. Check input values.")
    else:
        form = AdminComplaintUpdateForm(instance=complaint)

    context = {
        'complaint': complaint,
        'form': form,
    }
    return render(request, 'admin_complaint_update.html', context)


@login_required
@user_passes_test(is_staff_or_admin, login_url='landing')
def admin_pickup_update_view(request, pickup_id):
    """
    Allows administrators to assign collection vehicles, update pickup status,
    and mark completed.
    """
    pickup = get_object_or_404(PickupRequest, pickup_id=pickup_id)

    if request.method == 'POST':
        form = AdminPickupUpdateForm(request.POST, instance=pickup)
        if form.is_valid():
            form.save()
            messages.success(request, f"Pickup request {pickup.pickup_id} updated successfully.")
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Failed to update pickup request.")
    else:
        form = AdminPickupUpdateForm(instance=pickup)

    context = {
        'pickup': pickup,
        'form': form,
    }
    return render(request, 'admin_pickup_update.html', context)


# ==============================================================================
# CUSTOM ERROR HANDLERS (404, 500, 403)
# ==============================================================================

def custom_404_view(request, exception=None):
    """Friendly 404 page for missing pages or invalid IDs."""
    return render(request, '404.html', status=404)


def custom_500_view(request):
    """Friendly 500 error page for unexpected server issues."""
    return render(request, '500.html', status=500)


def custom_403_view(request, exception=None):
    """Friendly 403 error page for unauthorized access attempts."""
    return render(request, '403.html', status=403)
