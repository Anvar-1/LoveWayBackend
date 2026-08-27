import time
import uuid
from config.user.models import User
import base64
from typing import Optional
from config.common.story_redis import story_meta_redis, story_media_redis


STORY_TTL_SECONDS = 24 * 60 * 60


def _now_ts() -> int:
    return int(time.time())


def _story_key(story_id: str) -> str:
    return f"story:{story_id}"


def _story_media_key(story_id: str) -> str:
    return f"story:{story_id}:media"


def _story_views_key(story_id: str) -> str:
    return f"story:{story_id}:views"


def _story_likes_key(story_id: str) -> str:
    return f"story:{story_id}:likes"


def _story_comments_key(story_id: str) -> str:
    return f"story:{story_id}:comments"


def _story_comment_key(story_id: str, comment_id: str) -> str:
    return f"story:{story_id}:comment:{comment_id}"


def _user_stories_key(user_id: int) -> str:
    return f"user:{user_id}:stories"


ACTIVE_STORIES_KEY = "stories:active"


def cleanup_expired_stories():
    now = _now_ts()
    expired_story_ids = story_meta_redis.zrangebyscore(ACTIVE_STORIES_KEY, 0, now)

    if not expired_story_ids:
        return 0

    pipe_meta = story_meta_redis.pipeline()
    pipe_media = story_media_redis.pipeline()

    for story_id in expired_story_ids:
        # kommentlarni ham tozalaymiz
        comment_ids = story_meta_redis.zrange(_story_comments_key(story_id), 0, -1)
        story_data = story_meta_redis.hgetall(_story_key(story_id))
        owner_id = story_data.get("user_id")

        pipe_meta.delete(
            _story_key(story_id),
            _story_views_key(story_id),
            _story_likes_key(story_id),
            _story_comments_key(story_id),
        )
        pipe_media.delete(_story_media_key(story_id))

        for comment_id in comment_ids:
            pipe_meta.delete(_story_comment_key(story_id, comment_id))

        if owner_id:
            pipe_meta.zrem(_user_stories_key(owner_id), story_id)

        pipe_meta.zrem(ACTIVE_STORIES_KEY, story_id)

    pipe_meta.execute()
    pipe_media.execute()
    return len(expired_story_ids)


def create_story(
    *,
    user_id: int,
    media_bytes: bytes,
    media_type: str,
    caption: str = "",
) -> dict:
    cleanup_expired_stories()

    story_id = uuid.uuid4().hex
    now = _now_ts()
    expires_at = now + STORY_TTL_SECONDS

    meta_key = _story_key(story_id)
    media_key = _story_media_key(story_id)

    pipe_meta = story_meta_redis.pipeline()
    pipe_media = story_media_redis.pipeline()

    pipe_meta.hset(meta_key, mapping={
        "id": story_id,
        "user_id": str(user_id),
        "media_type": media_type,
        "caption": caption,
        "created_at": str(now),
        "expires_at": str(expires_at),
    })

    pipe_media.set(media_key, media_bytes)

    # user stories
    pipe_meta.zadd(_user_stories_key(user_id), {story_id: now})

    # global active index
    pipe_meta.zadd(ACTIVE_STORIES_KEY, {story_id: expires_at})

    # individual key ttl
    pipe_meta.expireat(meta_key, expires_at)
    pipe_meta.expireat(_story_views_key(story_id), expires_at)
    pipe_meta.expireat(_story_likes_key(story_id), expires_at)
    pipe_meta.expireat(_story_comments_key(story_id), expires_at)
    pipe_meta.expireat(_user_stories_key(user_id), expires_at + 3600)
    pipe_media.expireat(media_key, expires_at)

    pipe_meta.execute()
    pipe_media.execute()

    return {
        "id": story_id,
        "user_id": user_id,
        "media_type": media_type,
        "caption": caption,
        "created_at": now,
        "expires_at": expires_at,
    }


def get_story(story_id: str) -> Optional[dict]:
    cleanup_expired_stories()

    data = story_meta_redis.hgetall(_story_key(story_id))
    if not data:
        return None

    data["views_count"] = story_meta_redis.zcard(_story_views_key(story_id))
    data["likes_count"] = story_meta_redis.scard(_story_likes_key(story_id))
    data["comments_count"] = story_meta_redis.zcard(_story_comments_key(story_id))
    return data


def get_user_stories(user_id: int) -> list[dict]:
    cleanup_expired_stories()

    story_ids = story_meta_redis.zrevrange(_user_stories_key(user_id), 0, -1)
    result = []

    for story_id in story_ids:
        story = get_story(story_id)
        if story:
            result.append(story)

    return result


def delete_story(story_id: str, user) -> dict:
    story = story_meta_redis.hgetall(_story_key(story_id))

    if not story:
        return {"ok": False, "detail": "Story not found"}

    # Story egasi yoki admin o'chira oladi
    if int(story["user_id"]) != user.id and not (user.is_staff or user.is_superuser):
        return {"ok": False, "detail": "Permission denied"}

    comment_ids = story_meta_redis.zrange(_story_comments_key(story_id), 0, -1)

    pipe_meta = story_meta_redis.pipeline()
    pipe_media = story_media_redis.pipeline()

    pipe_meta.delete(
        _story_key(story_id),
        _story_views_key(story_id),
        _story_likes_key(story_id),
        _story_comments_key(story_id),
    )

    for comment_id in comment_ids:
        pipe_meta.delete(_story_comment_key(story_id, comment_id))

    # Story egasining ro'yxatidan o'chirish
    pipe_meta.zrem(_user_stories_key(story["user_id"]), story_id)

    # Active storylardan o'chirish
    pipe_meta.zrem(ACTIVE_STORIES_KEY, story_id)

    # Media faylini o'chirish
    pipe_media.delete(_story_media_key(story_id))

    pipe_meta.execute()
    pipe_media.execute()

    return {
        "ok": True,
        "detail": "Story deleted successfully"
    }



def add_view(story_id: str, viewer_id: int):
    story = story_meta_redis.hgetall(_story_key(story_id))
    if not story:
        return False

    expires_at = int(story["expires_at"])
    now = _now_ts()

    pipe = story_meta_redis.pipeline()
    pipe.zadd(_story_views_key(story_id), {str(viewer_id): now})
    pipe.expireat(_story_views_key(story_id), expires_at)
    pipe.execute()
    return True


def toggle_like(story_id: str, user_id: int) -> dict:
    story = story_meta_redis.hgetall(_story_key(story_id))
    if not story:
        return {"ok": False, "detail": "Story not found"}

    expires_at = int(story["expires_at"])
    likes_key = _story_likes_key(story_id)
    member = str(user_id)

    if story_meta_redis.sismember(likes_key, member):
        story_meta_redis.srem(likes_key, member)
        liked = False
    else:
        story_meta_redis.sadd(likes_key, member)
        story_meta_redis.expireat(likes_key, expires_at)
        liked = True

    return {
        "ok": True,
        "liked": liked,
        "likes_count": story_meta_redis.scard(likes_key),
    }


def add_comment(story_id: str, user_id: int, text: str) -> Optional[dict]:
    story = story_meta_redis.hgetall(_story_key(story_id))
    if not story:
        return None

    expires_at = int(story["expires_at"])
    now = _now_ts()
    comment_id = uuid.uuid4().hex

    comment_key = _story_comment_key(story_id, comment_id)

    pipe = story_meta_redis.pipeline()
    pipe.hset(comment_key, mapping={
        "id": comment_id,
        "story_id": story_id,
        "user_id": str(user_id),
        "text": text,
        "created_at": str(now),
    })
    pipe.zadd(_story_comments_key(story_id), {comment_id: now})
    pipe.expireat(comment_key, expires_at)
    pipe.expireat(_story_comments_key(story_id), expires_at)
    pipe.execute()

    return {
        "id": comment_id,
        "story_id": story_id,
        "user_id": user_id,
        "text": text,
        "created_at": now,
    }


def get_story_comments(story_id: str) -> list[dict]:
    story = story_meta_redis.hgetall(_story_key(story_id))
    if not story:
        return []

    comment_ids = story_meta_redis.zrange(_story_comments_key(story_id), 0, -1)
    comments = []

    for comment_id in comment_ids:
        data = story_meta_redis.hgetall(_story_comment_key(story_id, comment_id))
        if data:
            comments.append(data)

    return comments


def get_story_viewers(story_id: str) -> list[dict]:
    story = story_meta_redis.hgetall(_story_key(story_id))
    if not story:
        return []

    viewers = story_meta_redis.zrevrange(
        _story_views_key(story_id),
        0,
        -1,
        withscores=True,
    )

    return [
        {"user_id": int(user_id), "viewed_at": int(score)}
        for user_id, score in viewers
    ]


def get_story_media(story_id: str) -> Optional[bytes]:
    if not story_meta_redis.exists(_story_key(story_id)):
        return None
    return story_media_redis.get(_story_media_key(story_id))




def get_story_viewers_with_profiles(story_id: str):
    viewers = get_story_viewers(story_id)
    user_ids = [item["user_id"] for item in viewers]

    users = User.objects.filter(id__in=user_ids).select_related("profile")
    user_map = {u.id: u for u in users}

    result = []
    for item in viewers:
        user = user_map.get(item["user_id"])
        if not user:
            continue
        result.append({
            "user_id": user.id,
            "username": getattr(user.profile, "username", ""),
            "full_name": getattr(user.profile, "full_name", ""),
            "avatar": user.profile.avatar.url if getattr(user.profile, "avatar", None) else None,
            "viewed_at": item["viewed_at"],
        })
    return result