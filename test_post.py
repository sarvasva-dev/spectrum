import os
import django
from django.test.client import Client

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartwaste_project.settings')
django.setup()

from waste_management.models import Complaint
from django.contrib.auth.models import User

# create test user
admin_user, _ = User.objects.get_or_create(username='admin', is_staff=True, is_superuser=True)
if not admin_user.check_password('adminpass'):
    admin_user.set_password('adminpass')
    admin_user.save()

citizen, _ = User.objects.get_or_create(username='citizen')

c = Complaint.objects.create(user=citizen, issue_type='OTHER', description='Test', location='Test Loc', status='PENDING', priority='LOW')

client = Client()
client.force_login(admin_user)

response = client.post(f'/admin-portal/complaint/{c.complaint_id}/', {
    'status': 'RESOLVED',
    'priority': 'LOW',
    'assigned_crew': 'Crew 1',
    'admin_notes': 'Fixed'
})
print("POST status code:", response.status_code)

c.refresh_from_db()
print("Complaint status in DB after POST:", c.status)

