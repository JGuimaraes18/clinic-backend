import threading

_user = threading.local()

def set_current_user(user):
    _user.user = user

def get_current_user():
    return getattr(_user, "value", None)


def set_current_ip(ip):
    _user.ip = ip


def get_current_ip():
    return getattr(_user, "ip", None)



class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _user.value = request.user

        ip = request.META.get("HTTP_X_FORWARDED_FOR")
        if ip:
            ip = ip.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")

        set_current_ip(ip)

        response = self.get_response(request)
        return response


from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.http import JsonResponse

class ForcePasswordChangeMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        # We only check API requests
        if not request.path.startswith("/api/"):
            return None

        # Exclude login, forgot password, reset password
        exempt_urls = [
            "/api/auth/login/",
            "/api/auth/forgot-password/",
            "/api/auth/reset-password/",
        ]
        
        # Check if the URL is exempt
        for url in exempt_urls:
            if request.path.startswith(url):
                return None

        # Try to authenticate the user using JWT
        try:
            auth_result = JWTAuthentication().authenticate(request)
            if auth_result:
                user, token = auth_result
                request.user = user
                request.auth = token
                
                # Check if force_password_change is True
                if getattr(user, "force_password_change", False):
                    # We must allow me, change-password, and update-settings
                    allowed_endpoints = [
                        "/api/auth/me/",
                        "/api/auth/change-password/",
                        "/api/auth/update-settings/",
                    ]
                    is_allowed = False
                    for allowed in allowed_endpoints:
                        if request.path.startswith(allowed):
                            is_allowed = True
                            break
                            
                    if not is_allowed:
                        return JsonResponse(
                            {"detail": "Alteração de senha obrigatória no primeiro acesso.", "code": "password_change_required"},
                            status=403
                        )
        except Exception:
            # Let normal authentication handle invalid tokens
            pass

        return None