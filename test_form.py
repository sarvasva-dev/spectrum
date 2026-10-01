import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartwaste_project.settings')
django.setup()

from waste_management.models import Complaint
from waste_management.forms import AdminComplaintUpdateForm

complaint = Complaint.objects.first()
data = {
    'status': 'RESOLVED',
    'priority': complaint.priority,
    'assigned_crew': 'Crew 1',
    'admin_notes': 'Fixed'
}
form = AdminComplaintUpdateForm(data, instance=complaint)
print("Is valid?", form.is_valid())
if not form.is_valid():
    print("Errors:", form.errors)
