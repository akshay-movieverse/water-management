from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth.views import LoginView, LogoutView

def redirect_based_on_role(request):
    """ Redirects users to the correct dashboard based on their role. """
    if request.user.is_authenticated:
        if hasattr(request.user, 'is_admin') and request.user.is_admin:
            return redirect('admin_dashboard')
        elif hasattr(request.user, 'is_manager') and request.user.is_manager:
            print("manager_dashboard")
            return redirect('manager_dashboard')
    return redirect('login')

urlpatterns = [
    path('', redirect_based_on_role, name='home'),  # Redirect to respective dashboard
    path('adminpanel/', include('admin_dashboard.urls')),
    path('manager/', include('manager_dashboard.urls')),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
        # path('login/', LoginView.as_view(template_name='login.html', redirect_authenticated_user=True), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
]