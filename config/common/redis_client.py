import redis
from django.conf import settings

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=getattr(settings, "REDIS_SECURITY_DB", 1),
    password=getattr(settings, "REDIS_PASSWORD", None),
    decode_responses=True,
)