
from django.shortcuts import redirect
from django.contrib import messages

class BlockedUserLogoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated and hasattr(user, 'is_blocked') and user.is_blocked:
            from django.contrib.auth import logout
            logout(request)
            messages.error(request, "You have been blocked by the admin.")
            return redirect('user_panel:login')
        return self.get_response(request)

from django.shortcuts import redirect
from django.urls import reverse
from django.urls import path
from django.shortcuts import redirect
from django.urls import reverse, resolve

class AdminAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info

        try:
            admin_login_url = reverse('admin_panel:admin_login')
            admin_logout_url = reverse('admin_panel:admin_logout')
        except:
           
            return self.get_response(request)

    
        if path in [admin_login_url, admin_logout_url]:
            return self.get_response(request)

      
        if path.startswith('/admin_panel/'):
            if not request.user.is_authenticated:
                return redirect(admin_login_url)
            if not request.user.is_staff:
                return redirect(reverse('user_panel:home'))

     
        return self.get_response(request)

