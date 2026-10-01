import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartwaste_project.settings')
django.setup()

from waste_management.models import Complaint
from django.contrib.auth.models import User

# Let's see the first complaint
complaint = Complaint.objects.first()
if not complaint:
    print("No complaints found")
    exit()

print("Original status:", complaint.status)
complaint.status = 'RESOLVED'
complaint.save()

# Let's query it again
complaint.refresh_from_db()
print("Saved status:", complaint.status)

# Now use tracking query
complaints = Complaint.objects.filter(user=complaint.user)
print("Tracking status:", complaints.first().status)
