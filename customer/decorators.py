from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied


def customer_login_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and getattr(
            request.user, "is_customer", False
        ):
            return view_func(request, *args, **kwargs)
        raise PermissionDenied

    return _wrapped_view
