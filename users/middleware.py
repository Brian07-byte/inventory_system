from django.shortcuts import redirect

class RoleBasedAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if request.path.startswith('/dashboard/admin/') and not request.user.is_admin():
                return redirect('customer_dashboard')
            elif request.path.startswith('/dashboard/customer/') and not request.user.is_customer():
                return redirect('admin_dashboard')

        return self.get_response(request)
