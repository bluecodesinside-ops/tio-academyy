from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

@login_required
def user_profile(request):
    """Get user profile information"""
    user = request.user
    data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'date_joined': user.date_joined.isoformat(),
    }
    return JsonResponse(data)

@csrf_exempt
@require_http_methods(["POST"])
def register(request):
    """Register new user"""
    username = request.POST.get('username')
    email = request.POST.get('email')
    password = request.POST.get('password')
    
    if not all([username, email, password]):
        return JsonResponse({'error': 'All fields are required'}, status=400)
    
    try:
        user = User.objects.create_user(username=username, email=email, password=password)
        return JsonResponse({'message': 'User registered successfully', 'user_id': user.id})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
