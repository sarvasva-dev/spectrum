import os
import django
from django.test.client import Client

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartwaste_project.settings')
django.setup()

from waste_management.models import Complaint
from django.contrib.auth.models import User

admin_user = User.objects.get(username='admin')
citizen = User.objects.get(username='citizen')

c = Complaint.objects.create(user=citizen, issue_type='OTHER', description='Test 2', location='Test Loc 2', status='PENDING', priority='LOW')

client = Client()
client.force_login(citizen)

resp1 = client.get('/tracking/')
print("Tracking HTML Before:", resp1.content.decode().count(c.complaint_id))
print("Badge Resolved count before:", resp1.content.decode().count('badge-resolved'))

client.force_login(admin_user)
resp_post = client.post(f'/admin-portal/complaint/{c.complaint_id}/', {
    'status': 'RESOLVED',
    'priority': 'LOW',
    'assigned_crew': 'Crew 2',
    'admin_notes': 'Fixed'
})

client.force_login(citizen)
resp2 = client.get('/tracking/')
print("Badge Resolved count after:", resp2.content.decode().count('badge-resolved'))

