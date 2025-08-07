
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
