import re

def update_views():
    filepath = r"c:\Users\Admin\OneDrive\Desktop\spectrum\backend\waste_management\views.py"
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 1. Add imports and helper at the top if not exists
    if "broadcast_visualizer_event" not in content:
        helper = """
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import uuid
import time

def broadcast_visualizer_event(request_id, event_type, node, extra_data=None):
    channel_layer = get_channel_layer()
    if channel_layer:
        payload = {
            "type": event_type,
            "request_id": request_id,
            "node": node,
            "timestamp": time.time()
        }
        if extra_data:
            payload.update(extra_data)
        async_to_sync(channel_layer.group_send)(
            'visualizer',
            {
                'type': 'backend_event',
                'payload': payload
            }
        )
"""
        # Insert after imports
        content = content.replace("from django.utils import timezone", "from django.utils import timezone" + helper)
    
    # We will redefine the API views completely.
    new_api_views = """
def api_health_view(request):
    \"\"\"
    GET /api/health/
    Lightweight health check endpoint returning service status and database backend.
    \"\"\"
    req_id = str(uuid.uuid4())[:8]
    broadcast_visualizer_event(req_id, 'request_start', 'client', {'method': 'GET', 'path': '/api/health/'})
    broadcast_visualizer_event(req_id, 'backend_received', 'django')
    start_time = time.time()

    if request.method != 'GET':
        duration = int((time.time() - start_time) * 1000)
        broadcast_visualizer_event(req_id, 'response', 'response', {'status': 405, 'duration_ms': duration, 'method': request.method, 'path': '/api/health/'})
        return JsonResponse({'success': False, 'error': 'Method not allowed. Use GET.'}, status=405)

    broadcast_visualizer_event(req_id, 'database', 'sqlite')
    
    res = JsonResponse({
        'success': True,
        'service': 'CleanLoop REST API',
        'status': 'online',
        'timestamp': timezone.now().isoformat(),
        'database': 'SQLite3',
        'version': '1.0.0'
    })
    duration = int((time.time() - start_time) * 1000)
    broadcast_visualizer_event(req_id, 'response', 'response', {'status': res.status_code, 'duration_ms': duration, 'method': request.method, 'path': '/api/health/'})
    return res

def api_complaint_list_create_view(request):
    \"\"\"
    GET /api/complaints/ -> Returns JSON list of complaints from SQLite3.
    POST /api/complaints/ -> Creates a new complaint from JSON payload.
    Reuses existing models & smart priority calculation logic.
    \"\"\"
    req_id = str(uuid.uuid4())[:8]
    broadcast_visualizer_event(req_id, 'request_start', 'client', {'method': request.method, 'path': '/api/complaints/'})
    broadcast_visualizer_event(req_id, 'backend_received', 'django')
    start_time = time.time()

    if request.method == 'GET':
        broadcast_visualizer_event(req_id, 'database', 'sqlite')
        # Retrieve complaints based on authentication status
        if request.user.is_authenticated and is_staff_or_admin(request.user):
            qs = Complaint.objects.all()[:30]
        elif request.user.is_authenticated:
            qs = Complaint.objects.filter(user=request.user)[:30]
        else:
            qs = Complaint.objects.all()[:15]

        data = []
        for c in qs:
            data.append({
                'complaint_id': c.complaint_id,
                'user': c.user.username,
                'issue_type': c.issue_type,
                'issue_type_display': c.get_issue_type_display(),
                'description': c.description,
                'location': c.location,
                'landmark': c.landmark or '',
                'latitude': c.latitude,
                'longitude': c.longitude,
                'priority': c.priority,
                'status': c.status,
                'assigned_crew': c.assigned_crew or '',
                'created_at': c.created_at.isoformat()
            })
        res = JsonResponse({
            'success': True,
            'count': len(data),
            'data': data
        })
        duration = int((time.time() - start_time) * 1000)
        broadcast_visualizer_event(req_id, 'response', 'response', {'status': res.status_code, 'duration_ms': duration, 'method': request.method, 'path': '/api/complaints/'})
        return res

    elif request.method == 'POST':
        # Parse JSON body
        try:
            body = json.loads(request.body.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            res = JsonResponse({
                'success': False,
                'error': 'Invalid JSON body in request.'
            }, status=400)
            duration = int((time.time() - start_time) * 1000)
            broadcast_visualizer_event(req_id, 'response', 'response', {'status': res.status_code, 'duration_ms': duration, 'method': request.method, 'path': '/api/complaints/'})
            return res

        # Mandatory fields validation
        issue_type = body.get('issue_type', '').strip()
        description = body.get('description', '').strip()
        location = body.get('location', body.get('address', '')).strip()

        if not issue_type or not description or not location:
            res = JsonResponse({
                'success': False,
                'error': 'Missing required fields: issue_type, description, location/address are required.'
            }, status=400)
            duration = int((time.time() - start_time) * 1000)
            broadcast_visualizer_event(req_id, 'response', 'response', {'status': res.status_code, 'duration_ms': duration, 'method': request.method, 'path': '/api/complaints/'})
            return res

        # Validate issue_type choices
        valid_issues = [choice[0] for choice in Complaint.ISSUE_CHOICES]
        if issue_type not in valid_issues:
            res = JsonResponse({
                'success': False,
                'error': f'Invalid issue_type. Must be one of: {", ".join(valid_issues)}'
            }, status=400)
            duration = int((time.time() - start_time) * 1000)
            broadcast_visualizer_event(req_id, 'response', 'response', {'status': res.status_code, 'duration_ms': duration, 'method': request.method, 'path': '/api/complaints/'})
            return res

        # User assignment (use request.user or fallback to demo citizen)
        if request.user.is_authenticated:
            comp_user = request.user
        else:
            comp_user = User.objects.filter(is_staff=False).first()
            if not comp_user:
                comp_user = User.objects.first()

        # Parse coordinates
        try:
            latitude = float(body.get('latitude', 28.6139))
            longitude = float(body.get('longitude', 77.2090))
        except (ValueError, TypeError):
            latitude = 28.6139
            longitude = 77.2090

        landmark = body.get('landmark', '').strip()

        broadcast_visualizer_event(req_id, 'logic', 'smart_logic')
        # Calculate smart priority using existing business logic
        calculated_priority = Complaint.calculate_smart_priority(issue_type, location, latitude, longitude)

        broadcast_visualizer_event(req_id, 'database', 'sqlite')
        # Create and save complaint in SQLite3
        complaint = Complaint(
            user=comp_user,
            issue_type=issue_type,
            description=description,
            location=location,
            address=location,
            landmark=landmark,
            latitude=latitude,
            longitude=longitude,
            priority=calculated_priority,
            status='PENDING'
        )
        complaint.save()

        # Log timeline update
        ComplaintUpdate.objects.create(
            complaint=complaint,
            status='PENDING',
            note='Complaint registered via REST API. Pending municipal dispatch review.',
            updated_by=comp_user
        )

        res = JsonResponse({
            'success': True,
            'message': f'Complaint {complaint.complaint_id} registered successfully.',
            'data': {
                'complaint_id': complaint.complaint_id,
                'user': complaint.user.username,
                'issue_type': complaint.issue_type,
                'priority': complaint.priority,
                'status': complaint.status,
                'location': complaint.location,
                'latitude': complaint.latitude,
                'longitude': complaint.longitude,
                'created_at': complaint.created_at.isoformat()
            }
        }, status=201)
        duration = int((time.time() - start_time) * 1000)
        broadcast_visualizer_event(req_id, 'response', 'response', {'status': res.status_code, 'duration_ms': duration, 'method': request.method, 'path': '/api/complaints/'})
        return res

    else:
        res = JsonResponse({'success': False, 'error': 'Method not allowed.'}, status=405)
        duration = int((time.time() - start_time) * 1000)
        broadcast_visualizer_event(req_id, 'response', 'response', {'status': res.status_code, 'duration_ms': duration, 'method': request.method, 'path': '/api/complaints/'})
        return res


def api_complaint_detail_update_delete_view(request, complaint_id):
    \"\"\"
    GET /api/complaints/<id>/ -> Retrieve single complaint JSON
    PATCH /api/complaints/<id>/ -> Update status/priority/crew/notes (Admin authorized)
    DELETE /api/complaints/<id>/ -> Delete complaint (Admin authorized)
    \"\"\"
    req_id = str(uuid.uuid4())[:8]
    url_path = f'/api/complaints/{complaint_id}/'
    broadcast_visualizer_event(req_id, 'request_start', 'client', {'method': request.method, 'path': url_path})
    broadcast_visualizer_event(req_id, 'backend_received', 'django')
    start_time = time.time()

    broadcast_visualizer_event(req_id, 'database', 'sqlite')
    try:
        complaint = Complaint.objects.get(complaint_id=complaint_id)
    except Complaint.DoesNotExist:
        res = JsonResponse({
            'success': False,
            'error': f'Complaint with ID "{complaint_id}" was not found in SQLite3 database.'
        }, status=404)
        duration = int((time.time() - start_time) * 1000)
        broadcast_visualizer_event(req_id, 'response', 'response', {'status': res.status_code, 'duration_ms': duration, 'method': request.method, 'path': url_path})
        return res

    if request.method == 'GET':
        # Enforce security: users can only view their own unless staff
        if not is_staff_or_admin(request.user) and request.user.is_authenticated and complaint.user != request.user:
            res = JsonResponse({
                'success': False,
                'error': 'Forbidden: You do not have permission to access another citizen\\'s complaint data.'
            }, status=403)
            duration = int((time.time() - start_time) * 1000)
            broadcast_visualizer_event(req_id, 'response', 'response', {'status': res.status_code, 'duration_ms': duration, 'method': request.method, 'path': url_path})
            return res

        res = JsonResponse({
            'success': True,
            'data': {
                'complaint_id': complaint.complaint_id,
                'user': complaint.user.username,
                'user_full_name': complaint.user.get_full_name() or complaint.user.username,
                'issue_type': complaint.issue_type,
                'issue_type_display': complaint.get_issue_type_display(),
                'description': complaint.description,
                'location': complaint.location,
                'landmark': complaint.landmark or '',
                'latitude': complaint.latitude,
                'longitude': complaint.longitude,
                'priority': complaint.priority,
                'status': complaint.status,
                'assigned_crew': complaint.assigned_crew or '',
                'admin_notes': complaint.admin_notes or '',
                'created_at': complaint.created_at.isoformat(),
                'resolved_at': complaint.resolved_at.isoformat() if complaint.resolved_at else None
            }
        })
        duration = int((time.time() - start_time) * 1000)
        broadcast_visualizer_event(req_id, 'response', 'response', {'status': res.status_code, 'duration_ms': duration, 'method': request.method, 'path': url_path})
        return res

    elif request.method == 'PATCH':
        # Enforce staff authorization for administrative status updates
        if not is_staff_or_admin(request.user):
            res = JsonResponse({
                'success': False,
                'error': 'Forbidden: Administrative staff credentials required to modify complaint status or assign crews.'
            }, status=403)
            duration = int((time.time() - start_time) * 1000)
            broadcast_visualizer_event(req_id, 'response', 'response', {'status': res.status_code, 'duration_ms': duration, 'method': request.method, 'path': url_path})
            return res

        try:
            body = json.loads(request.body.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            res = JsonResponse({'success': False, 'error': 'Invalid JSON body.'}, status=400)
            duration = int((time.time() - start_time) * 1000)
            broadcast_visualizer_event(req_id, 'response', 'response', {'status': res.status_code, 'duration_ms': duration, 'method': request.method, 'path': url_path})
            return res

        old_status = complaint.status

        # Update allowed fields
        if 'status' in body:
            valid_statuses = [s[0] for s in Complaint.STATUS_CHOICES]
            if body['status'] in valid_statuses:
                complaint.status = body['status']
            else:
                res = JsonResponse({'success': False, 'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}, status=400)
                duration = int((time.time() - start_time) * 1000)
                broadcast_visualizer_event(req_id, 'response', 'response', {'status': res.status_code, 'duration_ms': duration, 'method': request.method, 'path': url_path})
                return res

        if 'priority' in body:
            valid_priorities = [p[0] for p in Complaint.PRIORITY_CHOICES]
            if body['priority'] in valid_priorities:
                complaint.priority = body['priority']

        if 'assigned_crew' in body:
            complaint.assigned_crew = str(body['assigned_crew']).strip()

        if 'admin_notes' in body:
            complaint.admin_notes = str(body['admin_notes']).strip()

        broadcast_visualizer_event(req_id, 'logic', 'smart_logic')
        broadcast_visualizer_event(req_id, 'database', 'sqlite')
        complaint.save()

        # Log timeline update
        if complaint.status != old_status or complaint.admin_notes:
            note_text = f"API update: Status changed from {old_status} to {complaint.status}."
            if complaint.assigned_crew:
                note_text += f" Assigned to {complaint.assigned_crew}."
            
            # Award CleanCoins if resolved
            if complaint.status == 'RESOLVED' and old_status != 'RESOLVED' and complaint.user:
                profile, _ = UserProfile.objects.get_or_create(user=complaint.user)
                profile.clean_coins += 50
                profile.save()
                note_text += " +50 CleanCoins awarded to citizen!"

            ComplaintUpdate.objects.create(
                complaint=complaint,
                status=complaint.status,
                note=note_text,
                updated_by=request.user
            )

        res = JsonResponse({
            'success': True,
            'message': f'Complaint {complaint.complaint_id} updated successfully.',
            'data': {
                'complaint_id': complaint.complaint_id,
                'status': complaint.status,
                'priority': complaint.priority,
                'assigned_crew': complaint.assigned_crew,
                'admin_notes': complaint.admin_notes,
                'updated_at': complaint.updated_at.isoformat()
            }
        })
        duration = int((time.time() - start_time) * 1000)
        broadcast_visualizer_event(req_id, 'response', 'response', {'status': res.status_code, 'duration_ms': duration, 'method': request.method, 'path': url_path})
        return res

    elif request.method == 'DELETE':
        # Enforce staff authorization for record deletion
        if not is_staff_or_admin(request.user):
            res = JsonResponse({
                'success': False,
                'error': 'Forbidden: Administrative staff credentials required to delete records.'
            }, status=403)
            duration = int((time.time() - start_time) * 1000)
            broadcast_visualizer_event(req_id, 'response', 'response', {'status': res.status_code, 'duration_ms': duration, 'method': request.method, 'path': url_path})
            return res

        cid = complaint.complaint_id
        broadcast_visualizer_event(req_id, 'database', 'sqlite')
        complaint.delete()
        res = JsonResponse({
            'success': True,
            'message': f'Complaint {cid} permanently deleted from SQLite3 database.'
        })
        duration = int((time.time() - start_time) * 1000)
        broadcast_visualizer_event(req_id, 'response', 'response', {'status': res.status_code, 'duration_ms': duration, 'method': request.method, 'path': url_path})
        return res

    else:
        res = JsonResponse({'success': False, 'error': 'Method not allowed.'}, status=405)
        duration = int((time.time() - start_time) * 1000)
        broadcast_visualizer_event(req_id, 'response', 'response', {'status': res.status_code, 'duration_ms': duration, 'method': request.method, 'path': url_path})
        return res
"""
    
    # We will replace from def api_health_view(request): to the start of man_of_the_month_view
    pattern = r"def api_health_view\(request\):.*?(?=\n\n\ndef man_of_the_month_view)"
    
    new_content = re.sub(pattern, new_api_views.strip(), content, flags=re.DOTALL)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print("Injected visualizer events into views.")

if __name__ == "__main__":
    update_views()
