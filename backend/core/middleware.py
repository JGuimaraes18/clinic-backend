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