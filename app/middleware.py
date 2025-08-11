
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
# myapp/middlewares.py
from django.shortcuts import redirect
from django.urls import reverse
from django.urls import path
from django.shortcuts import redirect
from django.urls import reverse, resolve

class AdminAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info  # Always a string

        # Skip check for admin login/logout views to prevent redirect loop
        if path in [reverse('admin_panel:admin_login'), reverse('admin_panel:admin_logout')]:
            return self.get_response(request)

        # Apply check only to admin section
        if path.startswith('/accounts/'):
            if not request.user.is_authenticated:
                return redirect(reverse('admin_panel:admin_login'))
            if not request.user.is_staff:  # Custom admin check if needed
                return redirect(reverse('user_panel:home'))

        return self.get_response(request)


