"""
Comprehensive Unit and Integration Tests for Smart Waste Management System.
Tests authentication, complaint workflows, pickup scheduling, admin controls,
permissions, smart priority calculations, and security constraints.
"""

from datetime import date, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from waste_management.models import UserProfile, Complaint, ComplaintUpdate, PickupRequest


class SmartWasteTestCase(TestCase):
    """Base test setup with standard citizen and administrator accounts."""

    def setUp(self):
        # 1. Create Citizen User
        self.citizen = User.objects.create_user(
            username='priya@example.com',
            email='priya@example.com',
            password='password123',
            first_name='Priya',
            last_name='Sharma'
        )
        self.citizen_profile = UserProfile.objects.create(
            user=self.citizen,
            phone='+1 555-0199',
            address='Block A, Sunrise Apartments',
            is_admin_staff=False
        )

        # 2. Create Second Citizen User (for permission isolation tests)
        self.other_citizen = User.objects.create_user(
            username='arun@example.com',
            email='arun@example.com',
            password='password123',
            first_name='Arun',
            last_name='Patel'
        )
        self.other_profile = UserProfile.objects.create(
            user=self.other_citizen,
            phone='+1 555-0177',
            address='Sector 9, Green Park',
            is_admin_staff=False
        )

        # 3. Create Admin Staff User
        self.admin = User.objects.create_user(
            username='admin@smartwaste.org',
            email='admin@smartwaste.org',
            password='adminpassword',
            first_name='Municipal',
            last_name='Officer',
            is_staff=True,
            is_superuser=True
        )
        self.admin_profile = UserProfile.objects.create(
            user=self.admin,
            phone='+1 555-0100',
            address='Municipal Sanitation HQ',
            is_admin_staff=True
        )

        self.client = Client()

    # --------------------------------------------------------------------------
    # 1. PUBLIC VIEWS & LANDING
    # --------------------------------------------------------------------------
    def test_landing_page(self):
        """Landing page renders successfully with status 200 and key headlines."""
        response = self.client.get(reverse('landing'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Smarter Waste Management for")
        self.assertContains(response, "Cleaner Communities")
        self.assertContains(response, "Report Waste Issue")
        self.assertContains(response, "Request Pickup")

    def test_awareness_page(self):
        """Awareness page displays segregation bins, guidelines, and do's and don'ts."""
        response = self.client.get(reverse('awareness'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Green Bin")
        self.assertContains(response, "Blue Bin")
        self.assertContains(response, "Red / Black Bin")
        self.assertContains(response, "DO's for Responsible Living")
        self.assertContains(response, "DON'Ts to Avoid Fines")

    # --------------------------------------------------------------------------
    # 2. AUTHENTICATION & REGISTRATION
    # --------------------------------------------------------------------------
    def test_user_registration(self):
        """Registers a new citizen and verifies User and UserProfile creation."""
        data = {
            'full_name': 'Rohan Gupta',
            'email': 'rohan@example.com',
            'phone': '+1 555-0155',
            'address': 'Flat 302, Palm Heights',
            'password': 'securepassword123',
            'confirm_password': 'securepassword123'
        }
        response = self.client.post(reverse('register'), data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(email='rohan@example.com').exists())
        user = User.objects.get(email='rohan@example.com')
        self.assertEqual(user.first_name, 'Rohan')
        self.assertEqual(user.last_name, 'Gupta')
        self.assertEqual(user.profile.phone, '+1 555-0155')
        self.assertEqual(user.profile.address, 'Flat 302, Palm Heights')

    def test_registration_password_mismatch(self):
        """Rejects registration when passwords do not match."""
        data = {
            'full_name': 'Test User',
            'email': 'testmismatch@example.com',
            'phone': '1234567890',
            'password': 'password123',
            'confirm_password': 'differentpassword'
        }
        response = self.client.post(reverse('register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Passwords do not match")
        self.assertFalse(User.objects.filter(email='testmismatch@example.com').exists())

    def test_citizen_login_and_logout(self):
        """Logs in citizen via email/username and tests session logout."""
        # Login via email
        response = self.client.post(reverse('login'), {
            'username_or_email': 'priya@example.com',
            'password': 'password123'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)

        # Logout
        response = self.client.get(reverse('logout'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)

    # --------------------------------------------------------------------------
    # 3. CITIZEN DASHBOARD
    # --------------------------------------------------------------------------
    def test_citizen_dashboard_requires_login(self):
        """Unauthenticated access to dashboard redirects to login."""
        response = self.client.get(reverse('citizen_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_citizen_dashboard_authenticated(self):
        """Authenticated citizen sees dashboard stats and greeting."""
        self.client.login(username='priya@example.com', password='password123')
        response = self.client.get(reverse('citizen_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome, Priya")
        self.assertContains(response, "Total Complaints")

    # --------------------------------------------------------------------------
    # 4. COMPLAINT REPORTING & SMART PRIORITY
    # --------------------------------------------------------------------------
    def test_report_waste_creates_complaint_and_id(self):
        """Citizen files waste complaint; system generates WM ID and timeline update."""
        self.client.login(username='priya@example.com', password='password123')
        data = {
            'issue_type': 'OVERFLOWING_BIN',
            'description': 'Municipal bin near bus stop has been overflowing for two days.',
            'location': 'Central Bus Stop, North Wing',
            'landmark': 'Platform 3',
            'priority': 'LOW',
            'auto_priority': 'on',
            'latitude': 28.6139,
            'longitude': 77.2090
        }
        response = self.client.post(reverse('report_waste'), data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify database record
        complaint = Complaint.objects.get(location='Central Bus Stop, North Wing')
        self.assertEqual(complaint.user, self.citizen)
        self.assertTrue(complaint.complaint_id.startswith('WM-2026-'))
        # Overflowing bin rule triggers HIGH priority
        self.assertEqual(complaint.priority, 'HIGH')
        self.assertEqual(complaint.status, 'PENDING')

        # Verify initial timeline entry
        self.assertTrue(complaint.timeline_updates.filter(status='PENDING').exists())

    def test_smart_priority_hotspot_elevation(self):
        """Location with multiple active complaints elevates priority to CRITICAL."""
        location_name = 'Main Market Crossroad'
        
        # Create 2 existing active complaints at the same location
        Complaint.objects.create(
            user=self.citizen,
            issue_type='GARBAGE_ON_ROAD',
            description='Active complaint 1',
            location=location_name,
            status='PENDING'
        )
        Complaint.objects.create(
            user=self.other_citizen,
            issue_type='OVERFLOWING_BIN',
            description='Active complaint 2',
            location=location_name,
            status='ASSIGNED'
        )

        # Smart priority calculation for a new complaint in the same location
        calc_priority = Complaint.calculate_smart_priority('MISSED_COLLECTION', location_name)
        self.assertEqual(calc_priority, 'CRITICAL')

    # --------------------------------------------------------------------------
    # 5. COMPLAINT TRACKING & SECURITY ISOLATION
    # --------------------------------------------------------------------------
    def test_user_can_only_see_own_complaints(self):
        """Citizen A cannot see Citizen B's complaint in tracking list."""
        c1 = Complaint.objects.create(
            user=self.citizen,
            issue_type='OVERFLOWING_BIN',
            description="Priya's private complaint",
            location='Sector 4',
            status='PENDING'
        )
        c2 = Complaint.objects.create(
            user=self.other_citizen,
            issue_type='ILLEGAL_DUMPING',
            description="Arun's private complaint",
            location='Sector 9',
            status='PENDING'
        )

        self.client.login(username='priya@example.com', password='password123')
        response = self.client.get(reverse('complaint_tracking'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, c1.complaint_id)
        self.assertNotContains(response, c2.complaint_id)

    def test_user_cannot_view_other_users_complaint_detail(self):
        """Citizen A attempting to access Citizen B's complaint detail gets 404."""
        c2 = Complaint.objects.create(
            user=self.other_citizen,
            issue_type='ILLEGAL_DUMPING',
            description="Arun's complaint",
            location='Sector 9',
            status='PENDING'
        )

        self.client.login(username='priya@example.com', password='password123')
        response = self.client.get(reverse('complaint_detail', kwargs={'complaint_id': c2.complaint_id}))
        self.assertEqual(response.status_code, 404)

    # --------------------------------------------------------------------------
    # 6. DOORSTEP PICKUP WORKFLOW
    # --------------------------------------------------------------------------
    def test_schedule_doorstep_pickup(self):
        """Citizen schedules a doorstep waste pickup; verifies PK ID generated."""
        self.client.login(username='priya@example.com', password='password123')
        pickup_date = date.today() + timedelta(days=2)
        data = {
            'waste_category': 'E_WASTE',
            'quantity': '2 boxes old electronics',
            'pickup_address': 'Flat 401, Green View Apartments',
            'preferred_date': pickup_date.strftime('%Y-%m-%d'),
            'preferred_time': 'Morning (08:00 AM - 11:00 AM)',
            'notes': 'Call 15 mins prior',
            'latitude': 28.6139,
            'longitude': 77.2090
        }
        response = self.client.post(reverse('pickup_request'), data, follow=True)
        self.assertEqual(response.status_code, 200)

        pickup = PickupRequest.objects.get(user=self.citizen)
        self.assertTrue(pickup.pickup_id.startswith('PK-2026-'))
        self.assertEqual(pickup.waste_category, 'E_WASTE')
        self.assertEqual(pickup.status, 'REQUESTED')

    # --------------------------------------------------------------------------
    # 7. ADMIN DASHBOARD & CONTROLS
    # --------------------------------------------------------------------------
    def test_regular_citizen_cannot_access_admin_dashboard(self):
        """Non-staff citizen is redirected away from admin dashboard."""
        self.client.login(username='priya@example.com', password='password123')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_admin_dashboard_metrics_and_hotspots(self):
        """Admin can access operations dashboard and view hotspot aggregations."""
        # Create complaints
        Complaint.objects.create(
            user=self.citizen,
            issue_type='OVERFLOWING_BIN',
            description='Hotspot issue 1',
            location='South Metro Gate',
            status='PENDING'
        )
        Complaint.objects.create(
            user=self.other_citizen,
            issue_type='ILLEGAL_DUMPING',
            description='Hotspot issue 2',
            location='South Metro Gate',
            status='ASSIGNED'
        )

        self.client.login(username='admin@smartwaste.org', password='adminpassword')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Administrator Operations Dashboard")
        self.assertContains(response, "South Metro Gate")

    def test_admin_can_update_complaint_status_and_assign_crew(self):
        """Admin updates complaint status to IN_PROGRESS and assigns cleanup crew."""
        complaint = Complaint.objects.create(
            user=self.citizen,
            issue_type='OVERFLOWING_BIN',
            description='Bin needs clearance',
            location='Main Park',
            status='PENDING',
            priority='HIGH'
        )

        self.client.login(username='admin@smartwaste.org', password='adminpassword')
        data = {
            'status': 'IN_PROGRESS',
            'priority': 'CRITICAL',
            'assigned_crew': 'Rapid Sanitation Crew 04',
            'admin_notes': 'Crew on site clearing debris.'
        }
        response = self.client.post(
            reverse('admin_complaint_update', kwargs={'complaint_id': complaint.complaint_id}),
            data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)

        complaint.refresh_from_db()
        self.assertEqual(complaint.status, 'IN_PROGRESS')
        self.assertEqual(complaint.priority, 'CRITICAL')
        self.assertEqual(complaint.assigned_crew, 'Rapid Sanitation Crew 04')
        # Check audit log was created
        self.assertTrue(complaint.timeline_updates.filter(status='IN_PROGRESS').exists())

    def test_admin_can_complete_pickup(self):
        """Admin marks doorstep pickup as COMPLETED with vehicle details."""
        pickup = PickupRequest.objects.create(
            user=self.citizen,
            waste_category='PLASTIC',
            quantity='5 bags',
            pickup_address='Tower B-101',
            preferred_date=date.today(),
            preferred_time='Morning (08:00 AM - 11:00 AM)',
            status='REQUESTED'
        )

        self.client.login(username='admin@smartwaste.org', password='adminpassword')
        data = {
            'status': 'COMPLETED',
            'assigned_vehicle': 'Eco Truck #09',
            'admin_notes': 'Collected and transported to recycling hub.'
        }
        response = self.client.post(
            reverse('admin_pickup_update', kwargs={'pickup_id': pickup.pickup_id}),
            data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)

        pickup.refresh_from_db()
        self.assertEqual(pickup.status, 'COMPLETED')
        self.assertEqual(pickup.assigned_vehicle, 'Eco Truck #09')
