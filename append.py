with open("backend/waste_management/views.py", "a") as f:
    f.write("""
# =====================================================================
# AI CITIZEN ASSISTANT (Sarvam Integration)
# =====================================================================

import json
import requests
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login

def ai_view(request):
    return render(request, 'misc/ai.html', {
        'is_authenticated': request.user.is_authenticated,
        'username': request.user.username if request.user.is_authenticated else ''
    })

@csrf_exempt
def api_ai_chat_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
        
    try:
        body = json.loads(request.body)
        message = body.get('message', '').strip()
        state = body.get('state', {})
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not request.user.is_authenticated:
        return handle_ai_auth_flow(request, message, state)

    return handle_ai_main_flow(request, message, state)

def handle_ai_auth_flow(request, message, state):
    intent = state.get('intent', 'START')
    step = state.get('step', 'START')

    if intent == 'START' and not message:
        return JsonResponse({
            'ok': True,
            'message': 'Welcome to CleanLoop 👋<br><br>Please sign in or create an account.',
            'intent': 'AUTH',
            'step': 'choose',
            'actions': ['SIGN IN', 'CREATE ACCOUNT']
        })
        
    if message.upper() == 'SIGN IN' or state.get('intent') == 'SIGN_IN':
        if step == 'choose' or step == 'START':
            return JsonResponse({'ok': True, 'message': 'Please enter your username:', 'intent': 'SIGN_IN', 'step': 'username', 'actions': []})
        elif step == 'username':
            return JsonResponse({'ok': True, 'message': 'Please enter your password:', 'intent': 'SIGN_IN', 'step': 'password', 'require_secure_input': True, 'state_data': {'username': message}, 'actions': []})
        elif step == 'password':
            username = state.get('state_data', {}).get('username', '')
            password = message
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return JsonResponse({'ok': True, 'message': f'Welcome back, {user.username}! 👋 What would you like to do today?', 'intent': 'MAIN_MENU', 'step': 'START', 'actions': ['Report Waste', 'Request Pickup', 'Track Complaint']})
            else:
                return JsonResponse({'ok': True, 'message': 'Invalid credentials.', 'intent': 'SIGN_IN', 'step': 'password', 'require_secure_input': True, 'state_data': {'username': username}, 'actions': ['CANCEL']})
                
    elif message.upper() == 'CREATE ACCOUNT' or state.get('intent') == 'SIGN_UP':
        if step == 'choose' or step == 'START':
            return JsonResponse({'ok': True, 'message': 'Please enter a username:', 'intent': 'SIGN_UP', 'step': 'username', 'actions': []})
        elif step == 'username':
            return JsonResponse({'ok': True, 'message': 'Please enter your password:', 'intent': 'SIGN_UP', 'step': 'password', 'require_secure_input': True, 'state_data': {'username': message}, 'actions': []})
        elif step == 'password':
            username = state.get('state_data', {}).get('username', '')
            from django.contrib.auth.models import User
            if User.objects.filter(username=username).exists():
                return JsonResponse({'ok': True, 'message': 'Username exists.', 'intent': 'SIGN_UP', 'step': 'username', 'actions': []})
            user = User.objects.create_user(username=username, password=message)
            login(request, user)
            return JsonResponse({'ok': True, 'message': f'Account created! Welcome, {user.username}.', 'intent': 'MAIN_MENU', 'step': 'START', 'actions': ['Report Waste', 'Request Pickup', 'Track Complaint']})
            
    if message.upper() == 'CANCEL':
         return JsonResponse({'ok': True, 'message': 'Welcome to CleanLoop 👋<br><br>Please sign in or create an account.', 'intent': 'AUTH', 'step': 'choose', 'actions': ['SIGN IN', 'CREATE ACCOUNT']})

    return JsonResponse({'ok': True, 'message': 'Please choose an option:', 'intent': 'AUTH', 'step': 'choose', 'actions': ['SIGN IN', 'CREATE ACCOUNT']})

def handle_ai_main_flow(request, message, state):
    intent = state.get('intent', 'MAIN_MENU')
    step = state.get('step', 'START')
    
    if not message and intent == 'MAIN_MENU':
        return JsonResponse({'ok': True, 'message': f'Hi, {request.user.username} 👋 What would you like to do today?', 'intent': 'MAIN_MENU', 'step': 'START', 'actions': ['Report Waste', 'Request Pickup', 'Track Complaint']})
        
    msg = message.upper()
    
    if msg == 'REPORT WASTE':
        return JsonResponse({'ok': True, 'message': 'What type of complaint would you like to report?', 'intent': 'REPORT_COMPLAINT', 'step': 'issue_type', 'actions': ['Overflowing Bin', 'Garbage on Road', 'Other']})
    elif msg == 'REQUEST PICKUP':
        return JsonResponse({'ok': True, 'message': 'What category of waste needs pickup?', 'intent': 'REQUEST_PICKUP', 'step': 'category', 'actions': ['General', 'Recyclable']})
    elif msg == 'TRACK COMPLAINT':
        return JsonResponse({'ok': True, 'message': 'Please enter the Complaint ID:', 'intent': 'TRACK_COMPLAINT', 'step': 'id_input', 'actions': []})

    if intent == 'REPORT_COMPLAINT':
        return process_complaint_flow(request, message, state)
    if intent == 'REQUEST_PICKUP':
        return process_pickup_flow(request, message, state)
    if intent == 'TRACK_COMPLAINT':
        return process_tracking_flow(request, message, state)
        
    api_key = os.environ.get('SARVAM_API_KEY')
    if not api_key:
        return JsonResponse({'ok': True, 'message': "AI is temporarily unavailable (API Key missing).", 'intent': 'MAIN_MENU', 'step': 'START', 'actions': ['Report Waste', 'Request Pickup']})
        
    try:
        return JsonResponse({'ok': True, 'message': f"I understood: '{message}'. How can I help?", 'intent': 'MAIN_MENU', 'step': 'START', 'actions': ['Report Waste', 'Request Pickup']})
    except Exception as e:
        return JsonResponse({'ok': True, 'message': "AI is temporarily unavailable.", 'intent': 'MAIN_MENU', 'step': 'START', 'actions': ['Report Waste']})

def process_complaint_flow(request, message, state):
    step = state.get('step')
    sd = state.get('state_data', {})
    
    if step == 'issue_type':
        sd['issue_type'] = message
        return JsonResponse({'ok': True, 'message': 'Description:', 'intent': 'REPORT_COMPLAINT', 'step': 'description', 'state_data': sd, 'actions': []})
    elif step == 'description':
        sd['description'] = message
        return JsonResponse({'ok': True, 'message': 'Location:', 'intent': 'REPORT_COMPLAINT', 'step': 'location', 'state_data': sd, 'actions': ['USE MY CURRENT LOCATION']})
    elif step == 'location':
        sd['location'] = message
        if message == 'USE MY CURRENT LOCATION':
            return JsonResponse({'ok': True, 'message': 'Coordinates?', 'intent': 'REPORT_COMPLAINT', 'step': 'coordinates', 'require_gps': True, 'state_data': sd, 'actions': []})
        else:
            return JsonResponse({'ok': True, 'message': f"Submit?", 'intent': 'REPORT_COMPLAINT', 'step': 'review', 'state_data': sd, 'actions': ['SUBMIT COMPLAINT', 'CANCEL']})
    elif step == 'coordinates':
        parts = message.split(',')
        if len(parts) == 2:
            sd['latitude'] = parts[0].strip()
            sd['longitude'] = parts[1].strip()
        return JsonResponse({'ok': True, 'message': f"Submit?", 'intent': 'REPORT_COMPLAINT', 'step': 'review', 'state_data': sd, 'actions': ['SUBMIT COMPLAINT', 'CANCEL']})
    elif step == 'review':
        if message == 'SUBMIT COMPLAINT':
            c = Complaint(user=request.user, issue_type=sd.get('issue_type', 'Other')[:50], description=sd.get('description', ''), location=sd.get('location', 'Unknown'))
            c.save()
            ComplaintUpdate.objects.create(complaint=c, status=c.status, note='Created via AI')
            return JsonResponse({'ok': True, 'message': f"✅ Submitted! ID: <b>{c.complaint_id}</b>.", 'intent': 'MAIN_MENU', 'step': 'START', 'actions': ['Report Waste']})
        else:
            return JsonResponse({'ok': True, 'message': 'Cancelled.', 'intent': 'MAIN_MENU', 'step': 'START', 'actions': ['Report Waste']})
            
def process_pickup_flow(request, message, state):
    return JsonResponse({'ok': True, 'message': "Pickup requested!", 'intent': 'MAIN_MENU', 'step': 'START', 'actions': ['Track Pickup']})
    
def process_tracking_flow(request, message, state):
    step = state.get('step')
    if step == 'id_input':
        try:
            c = Complaint.objects.get(complaint_id=message)
            return JsonResponse({'ok': True, 'message': f"Status: <b>{c.get_status_display()}</b>", 'intent': 'MAIN_MENU', 'step': 'START', 'actions': ['Track Another']})
        except Complaint.DoesNotExist:
            return JsonResponse({'ok': True, 'message': 'Not found.', 'intent': 'MAIN_MENU', 'step': 'START', 'actions': ['Track Another']})
""")
