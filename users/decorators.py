from django.http import HttpResponseForbidden

def customer_required(view_func):
    """Allow only customers"""
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_customer():
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("You are not authorized to access this page.")
    return wrapper

def admin_required(view_func):
    """Allow only admins"""
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_admin():
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("You are not authorized to access this page.")
    return wrapper
