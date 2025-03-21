
from django.shortcuts import redirect
from django.urls import reverse

class UserTypeRestrictionMiddleware:
    """
    Middleware to restrict access to dashboards based on user type.
    Redirects unauthenticated users to the login page.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # If the user is not authenticated, redirect to login
        if not request.user.is_authenticated:
            if request.path not in [reverse('login'), reverse('logout')]:
                return redirect(reverse('login'))

        else:
            path = request.path

            # Restrict access for admin users
            if hasattr(request.user, 'is_admin') and request.user.is_admin and path.startswith('/managerpanel/'):
                return redirect(reverse('admin_dashboard'))

            # Restrict access for manager users
            if hasattr(request.user, 'is_manager') and request.user.is_manager and path.startswith('/adminpanel/'):
                return redirect(reverse('manager_dashboard'))

        return self.get_response(request)
