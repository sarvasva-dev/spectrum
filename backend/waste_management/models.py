"""
Database Models for Smart Waste Management System.
Designed for simplicity, reliability, and easy understanding by Python beginners.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    """
    Extends Django's default User model to store additional citizen profile information
    such as phone number and residential address.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True, help_text="Contact number for SMS/call verification")
    address = models.CharField(max_length=255, blank=True, help_text="Default residence or society address")
    is_admin_staff = models.BooleanField(default=False, help_text="Designates if this citizen is an admin staff member")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} Profile ({self.user.get_full_name() or self.user.email})"


class Complaint(models.Model):
    """
    Stores citizen complaints regarding waste problems like overflowing bins,
    illegal dumping, or missed pickups.
    """
    # Issue Type Choices
    ISSUE_CHOICES = [
        ('OVERFLOWING_BIN', 'Overflowing Bin'),
        ('GARBAGE_ON_ROAD', 'Garbage on Road'),
        ('ILLEGAL_DUMPING', 'Illegal Dumping'),
        ('MISSED_COLLECTION', 'Missed Collection'),
        ('IMPROPER_SEGREGATION', 'Improper Waste Segregation'),
        ('OTHER', 'Other Waste Issue'),
    ]

    # Priority Choices
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    # Workflow Status Choices
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ASSIGNED', 'Assigned'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
    ]

    # Unique human-readable complaint identifier, e.g. WM-2026-0001
    complaint_id = models.CharField(max_length=30, unique=True, editable=False, db_index=True)
    
    # Associated citizen who submitted the complaint
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints')
    
    # Category of waste problem
    issue_type = models.CharField(max_length=40, choices=ISSUE_CHOICES)
    
    # Detailed description from citizen
    description = models.TextField(help_text="Detailed description of the issue")
    
    # Address and Location details
    address = models.CharField(max_length=255, blank=True, default='', help_text="Street address or location name")
    location = models.CharField(max_length=255, help_text="Location or area name, e.g., North Gate, Main Road")
    landmark = models.CharField(max_length=255, blank=True, help_text="Nearby landmark to assist sanitation crew")
    
    # GPS Coordinates stored in SQLite3
    latitude = models.FloatField(default=28.6139, help_text="GPS Latitude coordinate")
    longitude = models.FloatField(default=77.2090, help_text="GPS Longitude coordinate")
    
    # Optional image uploaded by citizen
    image = models.ImageField(upload_to='complaints/%Y/%m/', blank=True, null=True)
    
    # Priority (automatically calculated or adjusted by admin)
    priority = models.CharField(max_length=15, choices=PRIORITY_CHOICES, default='MEDIUM')
    
    # Current lifecycle status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Municipal assignment details
    assigned_crew = models.CharField(max_length=120, blank=True, default='', help_text="Crew name or vehicle assigned")
    admin_notes = models.TextField(blank=True, default='', help_text="Notes from municipality dispatch team")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.complaint_id} - {self.get_issue_type_display()} ({self.status})"

    def save(self, *args, **kwargs):
        """
        Auto-generates sequential, human-friendly complaint ID if not already generated.
        Format: WM-YYYY-NNNN (e.g., WM-2026-0001).
        """
        if not self.address and self.location:
            self.address = self.location
        elif not self.location and self.address:
            self.location = self.address

        if not self.complaint_id:
            year = timezone.now().year
            prefix = f"WM-{year}-"
            # Get latest count for current year
            last_record = Complaint.objects.filter(complaint_id__startswith=prefix).order_by('-id').first()
            if last_record and last_record.complaint_id:
                try:
                    last_num = int(last_record.complaint_id.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = Complaint.objects.filter(complaint_id__startswith=prefix).count() + 1
            else:
                new_num = 1
            self.complaint_id = f"{prefix}{new_num:04d}"

        # If marking resolved, record resolved timestamp
        if self.status == 'RESOLVED' and not self.resolved_at:
            self.resolved_at = timezone.now()
        elif self.status != 'RESOLVED':
            self.resolved_at = None

        super().save(*args, **kwargs)

    @staticmethod
    def calculate_smart_priority(issue_type, location, latitude=None, longitude=None):
        """
        Rule-based smart priority calculator:
        - HIGH / CRITICAL if illegal dumping, overflowing bin, or repeated complaints from nearby location radius
        - MEDIUM for missed collection
        - LOW for general / other issues
        Explanation comments:
        # Rule 1: Illegal dumping or overflowing bins represent immediate public health risks -> HIGH.
        # Rule 2: Repeated complaints in same area / GPS radius indicate chronic hotspot -> CRITICAL.
        # Rule 3: Missed collections represent routine operational delays -> MEDIUM.
        # Rule 4: General or minor issues -> LOW.
        """
        # Check geographic proximity hotspot count if coordinates provided
        nearby_active_count = 0
        if latitude is not None and longitude is not None and latitude != 0 and longitude != 0:
            import math
            active_complaints = Complaint.objects.filter(status__in=['PENDING', 'ASSIGNED', 'IN_PROGRESS'])
            for comp in active_complaints:
                if comp.latitude and comp.longitude:
                    # Calculate Haversine distance in km
                    dlat = math.radians(comp.latitude - latitude)
                    dlon = math.radians(comp.longitude - longitude)
                    a = math.sin(dlat / 2)**2 + math.cos(math.radians(latitude)) * math.cos(math.radians(comp.latitude)) * math.sin(dlon / 2)**2
                    dist_km = 6371.0 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                    if dist_km <= 0.5: # Within 500 meters
                        nearby_active_count += 1

        cleaned_loc = location.strip().lower() if location else ""
        if cleaned_loc and nearby_active_count == 0:
            nearby_active_count = Complaint.objects.filter(
                location__icontains=cleaned_loc,
                status__in=['PENDING', 'ASSIGNED', 'IN_PROGRESS']
            ).count()

        if nearby_active_count >= 2:
            return 'CRITICAL'
        elif issue_type in ['ILLEGAL_DUMPING', 'OVERFLOWING_BIN']:
            return 'HIGH'
        elif issue_type in ['MISSED_COLLECTION', 'IMPROPER_SEGREGATION']:
            return 'MEDIUM'
        else:
            return 'LOW'


class ComplaintUpdate(models.Model):
    """
    Audit log / timeline update for a complaint to show transparent progress
    to citizens (Pending -> Assigned -> In Progress -> Resolved).
    """
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='timeline_updates')
    status = models.CharField(max_length=20)
    note = models.TextField(blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.complaint.complaint_id} updated to {self.status} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class PickupRequest(models.Model):
    """
    Doorstep waste pickup requests submitted by citizens for bulk or segregated waste.
    """
    WASTE_CATEGORIES = [
        ('ORGANIC', 'Organic / Wet Waste'),
        ('PLASTIC', 'Plastic (Bottles, Containers, Wrappers)'),
        ('PAPER', 'Paper & Cardboard'),
        ('E_WASTE', 'E-Waste (Electronics, Batteries, Gadgets)'),
        ('GLASS', 'Glass (Bottles, Jars, Broken Glass)'),
        ('METAL', 'Metal & Scrap Materials'),
        ('GENERAL', 'General Solid Waste'),
        ('OTHER', 'Other Miscellaneous Waste'),
    ]

    STATUS_CHOICES = [
        ('REQUESTED', 'Requested'),
        ('ASSIGNED', 'Assigned'),
        ('PICKED_UP', 'Picked Up'),
        ('COMPLETED', 'Completed'),
    ]

    # Unique human-readable pickup identifier, e.g. PK-2026-0001
    pickup_id = models.CharField(max_length=30, unique=True, editable=False, db_index=True)
    
    # Requesting citizen
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pickup_requests')
    
    # Waste category
    waste_category = models.CharField(max_length=30, choices=WASTE_CATEGORIES)
    
    # Approximate quantity / weight
    quantity = models.CharField(max_length=100, help_text="e.g. 2 bags, 1 carton box, ~10 kg")
    
    # Doorstep pickup address
    pickup_address = models.TextField(help_text="Complete address with flat/door number")
    
    # GPS Coordinates stored in SQLite3
    latitude = models.FloatField(default=28.6139, help_text="GPS Latitude coordinate")
    longitude = models.FloatField(default=77.2090, help_text="GPS Longitude coordinate")
    
    # Date & time preferences
    preferred_date = models.DateField(help_text="Preferred collection date")
    preferred_time = models.CharField(
        max_length=50,
        default='Morning (09:00 AM - 12:00 PM)',
        help_text="Time window for pickup"
    )
    
    # Additional notes
    notes = models.TextField(blank=True, help_text="Access instructions, gate codes, or special handling")
    
    # Status workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REQUESTED')
    assigned_vehicle = models.CharField(max_length=100, blank=True, default='', help_text="Vehicle or team assigned")
    admin_notes = models.TextField(blank=True, default='')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.pickup_id} - {self.get_waste_category_display()} ({self.status})"

    def save(self, *args, **kwargs):
        """
        Auto-generates sequential, human-friendly pickup ID: PK-YYYY-NNNN.
        """
        if not self.pickup_id:
            year = timezone.now().year
            prefix = f"PK-{year}-"
            last_record = PickupRequest.objects.filter(pickup_id__startswith=prefix).order_by('-id').first()
            if last_record and last_record.pickup_id:
                try:
                    last_num = int(last_record.pickup_id.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = PickupRequest.objects.filter(pickup_id__startswith=prefix).count() + 1
            else:
                new_num = 1
            self.pickup_id = f"{prefix}{new_num:04d}"

        super().save(*args, **kwargs)
