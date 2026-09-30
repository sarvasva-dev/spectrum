"""
Seed initial demo data for Smart Waste Management System.
Creates superuser, citizen accounts, complaints, timeline updates, and pickups.
"""

import os
import django
from datetime import date, timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartwaste_project.settings')
django.setup()

from django.contrib.auth.models import User
from waste_management.models import UserProfile, Complaint, ComplaintUpdate, PickupRequest


def seed():
    print("🌱 Seeding Smart Waste Management System data...")

    # 1. Create or Update Superuser / Admin
    admin_user, created = User.objects.get_or_create(
        username='admin@smartwaste.org',
        defaults={
            'email': 'admin@smartwaste.org',
            'first_name': 'Municipal',
            'last_name': 'Administrator',
            'is_staff': True,
            'is_superuser': True,
        }
    )
    admin_user.set_password('admin1234')
    admin_user.is_staff = True
    admin_user.is_superuser = True
    admin_user.save()

    admin_profile, _ = UserProfile.objects.get_or_create(
        user=admin_user,
        defaults={
            'phone': '+1 555-0100',
            'address': 'City Municipal Sanitation Headquarters, Control Room 3',
            'is_admin_staff': True,
        }
    )
    admin_profile.is_admin_staff = True
    admin_profile.save()
    print("✓ Admin user created: admin@smartwaste.org / admin1234")

    # 2. Create Demo Citizen 1
    citizen1, _ = User.objects.get_or_create(
        username='citizen@smartwaste.org',
        defaults={
            'email': 'citizen@smartwaste.org',
            'first_name': 'Priya',
            'last_name': 'Sharma',
        }
    )
    citizen1.set_password('demo1234')
    citizen1.save()

    UserProfile.objects.get_or_create(
        user=citizen1,
        defaults={
            'phone': '+1 555-0199',
            'address': 'Apartment 4B, Green Glen Residency, Sector 4',
            'is_admin_staff': False,
        }
    )
    print("✓ Citizen 1 created: citizen@smartwaste.org / demo1234")

    # 3. Create Demo Citizen 2
    citizen2, _ = User.objects.get_or_create(
        username='arun@smartwaste.org',
        defaults={
            'email': 'arun@smartwaste.org',
            'first_name': 'Arun',
            'last_name': 'Patel',
        }
    )
    citizen2.set_password('demo1234')
    citizen2.save()

    UserProfile.objects.get_or_create(
        user=citizen2,
        defaults={
            'phone': '+1 555-0177',
            'address': 'House 12, Sunrise Enclave, Main Road',
            'is_admin_staff': False,
        }
    )
    print("✓ Citizen 2 created: arun@smartwaste.org / demo1234")

    # 4. Seed Complaints (demonstrating hotspot logic at "Main Gate")
    complaints_data = [
        {
            'complaint_id': 'WM-2026-0001',
            'user': citizen1,
            'issue_type': 'OVERFLOWING_BIN',
            'location': 'Main Gate',
            'landmark': 'Near Security Checkpost #1',
            'description': 'Public waste bin overflowing onto sidewalk. Stray animals gathering around scattered food waste.',
            'priority': 'HIGH',
            'status': 'IN_PROGRESS',
            'assigned_crew': 'Rapid Sanitation Unit 3 (Truck 104)',
            'admin_notes': 'Crew dispatched with high-capacity compactor.',
        },
        {
            'complaint_id': 'WM-2026-0002',
            'user': citizen2,
            'issue_type': 'ILLEGAL_DUMPING',
            'location': 'Main Gate',
            'landmark': 'Beside Electrical Substation',
            'description': 'Commercial packaging materials, plastic crates, and thermocol dumped overnight along the perimeter wall.',
            'priority': 'CRITICAL',
            'status': 'ASSIGNED',
            'assigned_crew': 'Heavy Debris Hauler #07',
            'admin_notes': 'Hotspot alert triggered. Surveillance review initiated.',
        },
        {
            'complaint_id': 'WM-2026-0003',
            'user': citizen1,
            'issue_type': 'GARBAGE_ON_ROAD',
            'location': 'Sector 4 Market',
            'landmark': 'Opposite Central Pharmacy',
            'description': 'Litter and fruit peels scattered across road following the morning vegetable vendor market.',
            'priority': 'HIGH',
            'status': 'RESOLVED',
            'assigned_crew': 'Daytime Sweeper Squad B',
            'admin_notes': 'Street swept clean and sprayed with eco-disinfectant.',
        },
        {
            'complaint_id': 'WM-2026-0004',
            'user': citizen2,
            'issue_type': 'MISSED_COLLECTION',
            'location': 'Main Gate',
            'landmark': 'Bus Stop Shelter',
            'description': 'Morning municipal collection route skipped the two segregated bins adjacent to the bus stop.',
            'priority': 'CRITICAL',  # Elevates because Main Gate is a hotspot with >= 2 complaints
            'status': 'PENDING',
            'assigned_crew': '',
            'admin_notes': '',
        },
        {
            'complaint_id': 'WM-2026-0005',
            'user': citizen1,
            'issue_type': 'IMPROPER_SEGREGATION',
            'location': 'Block C Community Hall',
            'landmark': 'Sports Pavilion',
            'description': 'Plastic cups and bottles mixed directly into green organic compost bin after an event.',
            'priority': 'MEDIUM',
            'status': 'RESOLVED',
            'assigned_crew': 'Segregation Quality Inspector',
            'admin_notes': 'Bins sorted and clear signage re-applied.',
        },
    ]

    for item in complaints_data:
        c, created = Complaint.objects.get_or_create(
            complaint_id=item['complaint_id'],
            defaults=item
        )
        if created:
            # Add timeline audit entries
            ComplaintUpdate.objects.create(
                complaint=c,
                status='PENDING',
                note='Complaint logged by citizen.',
                updated_by=c.user
            )
            if c.status in ['ASSIGNED', 'IN_PROGRESS', 'RESOLVED']:
                ComplaintUpdate.objects.create(
                    complaint=c,
                    status='ASSIGNED',
                    note=f"Assigned to {c.assigned_crew or 'Sanitation Crew'}.",
                    updated_by=admin_user
                )
            if c.status in ['IN_PROGRESS', 'RESOLVED']:
                ComplaintUpdate.objects.create(
                    complaint=c,
                    status='IN_PROGRESS',
                    note='Sanitation crew on site executing cleanup.',
                    updated_by=admin_user
                )
            if c.status == 'RESOLVED':
                c.resolved_at = timezone.now()
                c.save()
                ComplaintUpdate.objects.create(
                    complaint=c,
                    status='RESOLVED',
                    note=f"Resolution complete: {c.admin_notes}",
                    updated_by=admin_user
                )
    print("✓ Complaints and timeline updates seeded.")

    # 5. Seed Doorstep Pickups
    today = date.today()
    pickups_data = [
        {
            'pickup_id': 'PK-2026-0001',
            'user': citizen1,
            'waste_category': 'E_WASTE',
            'quantity': '2 old laptops, 4 chargers, 1 microwave',
            'pickup_address': 'Apartment 4B, Green Glen Residency, Sector 4',
            'preferred_date': today + timedelta(days=1),
            'preferred_time': 'Morning (08:00 AM - 11:00 AM)',
            'notes': 'Please call 10 mins prior to arrival. Gate intercom #402.',
            'status': 'ASSIGNED',
            'assigned_vehicle': 'Eco-Van #02 (Driver: Rajesh)',
        },
        {
            'pickup_id': 'PK-2026-0002',
            'user': citizen2,
            'waste_category': 'PAPER',
            'quantity': '3 large boxes (~25 kg) flattened packaging cardboard',
            'pickup_address': 'House 12, Sunrise Enclave, Main Road',
            'preferred_date': today + timedelta(days=2),
            'preferred_time': 'Afternoon (02:00 PM - 05:00 PM)',
            'notes': 'Boxes kept near covered garage porch.',
            'status': 'COMPLETED',
            'assigned_vehicle': 'Recyclables Truck #05 (Driver: Sunil)',
            'admin_notes': 'Collected and delivered to municipal paper pulping recycling plant.',
        },
    ]

    for p in pickups_data:
        PickupRequest.objects.get_or_create(
            pickup_id=p['pickup_id'],
            defaults=p
        )
    print("✓ Doorstep pickups seeded.")
    print("🎉 All demo data successfully initialized!")


if __name__ == '__main__':
    seed()
