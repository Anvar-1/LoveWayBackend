# import redis
# from django.conf import settings

# redis_client = redis.Redis(
#     host=settings.REDIS_HOST,
#     port=settings.REDIS_PORT,
#     db=getattr(settings, "REDIS_SECURITY_DB", 1),
#     password=getattr(settings, "REDIS_PASSWORD", None),
#     decode_responses=True,
# )




import redis
from django.conf import settings

redis_url = getattr(
    settings, 
    "REDIS_URL", 
    f"redis://:{getattr(settings, 'REDIS_PASSWORD', '')}@{settings.REDIS_HOST}:{getattr(settings, 'REDIS_PORT', 6379)}/{getattr(settings, 'REDIS_SECURITY_DB', 1)}"
)

redis_client = redis.from_url(redis_url, decode_responses=True)