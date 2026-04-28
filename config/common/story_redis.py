import redis
from django.conf import settings

story_meta_redis = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=getattr(settings, "REDIS_DB", 1),
    password=getattr(settings, "REDIS_PASSWORD", None),
    decode_responses=True,
)

story_media_redis = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=getattr(settings, "REDIS_DB", 1),
    password=getattr(settings, "REDIS_PASSWORD", None),
    decode_responses=False,  # media uchun
)