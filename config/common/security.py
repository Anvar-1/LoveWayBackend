from rest_framework.exceptions import PermissionDenied
from .redis_client import redis_client
from .utils import get_client_ip


# =========================
# Rate limit / block helpers
# =========================

def increment_rate(key: str, limit: int, ttl: int):
    count = redis_client.incr(key)
    if count == 1:
        redis_client.expire(key, ttl)
    return count > limit, count


def block_key(key: str, ttl: int):
    redis_client.setex(key, ttl, "1")


def is_blocked(key: str) -> bool:
    return redis_client.exists(key) == 1


def enforce_block(request, phone=None):
    ip = get_client_ip(request)

    if is_blocked(f"block:ip:{ip}"):
        raise PermissionDenied("This IP is temporarily blocked.")

    if phone and is_blocked(f"block:phone:{phone}"):
        raise PermissionDenied("This phone number is temporarily blocked.")


# =========================
# OTP helpers
# =========================

def set_otp(phone: str, code: str, ttl: int = 60):
    redis_client.setex(f"otp:{phone}", ttl, code)


def get_otp(phone: str):
    return redis_client.get(f"otp:{phone}")


def delete_otp(phone: str):
    redis_client.delete(f"otp:{phone}")


# =========================
# Password reset OTP helpers
# =========================

def set_reset_otp(phone: str, code: str, ttl: int = 60):
    redis_client.setex(f"reset-otp:{phone}", ttl, code)


def get_reset_otp(phone: str):
    return redis_client.get(f"reset-otp:{phone}")


def delete_reset_otp(phone: str):
    redis_client.delete(f"reset-otp:{phone}")


# =========================
# Registration session helpers
# OTP verify bo'lgandan keyin register uchun phone saqlanadi
# =========================

def set_registration_session(phone: str, request, ttl: int = 60):
    ip = get_client_ip(request)
    redis_client.setex(f"register:session:{ip}", ttl, phone)


def get_registration_session(request):
    ip = get_client_ip(request)
    return redis_client.get(f"register:session:{ip}")


def delete_registration_session(request):
    ip = get_client_ip(request)
    redis_client.delete(f"register:session:{ip}")