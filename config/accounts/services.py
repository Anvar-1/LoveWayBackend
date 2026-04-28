import json

from config.common.redis_client import redis_client
from .serializers import MeSerializer


def get_user_cache_key(user_id: int) -> str:
    return f"user:session:{user_id}"


def cache_user_session(user, ttl: int = 3600):
    data = MeSerializer(user).data
    redis_client.setex(
        get_user_cache_key(user.id),
        ttl,
        json.dumps(data),
    )
    return data


def get_cached_user_session(user_id: int):
    cached_data = redis_client.get(get_user_cache_key(user_id))
    if not cached_data:
        return None
    return json.loads(cached_data)


def delete_cached_user_session(user_id: int):
    redis_client.delete(get_user_cache_key(user_id))