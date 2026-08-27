import time
import uuid
from typing import Optional

from django.db.models import Q

from config.Friendship.models import Friendship
from config.common.redis_client import redis_client
from config.user.models import User


LIVE_TTL_SECONDS = 60 * 60 * 6  # 6 soat
VIEWER_HEARTBEAT_TTL_SECONDS = 40


def _now_ts() -> int:
    return int(time.time())


def _live_key(live_id: str) -> str:
    return f"live:{live_id}"


def _live_viewers_key(live_id: str) -> str:
    return f"live:{live_id}:viewers"


def _live_likes_key(live_id: str) -> str:
    return f"live:{live_id}:likes"


def _live_comments_key(live_id: str) -> str:
    return f"live:{live_id}:comments"


def _live_comment_key(live_id: str, comment_id: str) -> str:
    return f"live:{live_id}:comment:{comment_id}"


def _user_active_live_key(user_id: int) -> str:
    return f"user:{user_id}:active_live"


def _viewer_last_seen_key(live_id: str, user_id: int) -> str:
    return f"live:{live_id}:viewer_last_seen:{user_id}"


def _last_stats_broadcast_key(live_id: str) -> str:
    return f"live:{live_id}:last_stats_broadcast"


def _active_livestreams_key() -> str:
    return "active_livestreams"



def get_accepted_friends_count(user_id: int) -> int:
    qs = Friendship.objects.filter(status="accepted").filter(
        Q(from_user_id=user_id) | Q(to_user_id=user_id)
    )

    friend_ids = set()
    for row in qs.values("from_user_id", "to_user_id"):
        if row["from_user_id"] == user_id:
            friend_ids.add(row["to_user_id"])
        else:
            friend_ids.add(row["from_user_id"])

    return len(friend_ids)


MIN_FRIENDS_REQUIRED_FOR_LIVE = 50


def can_start_livestream(user_id: int) -> tuple[bool, str]:
    active_live_id = redis_client.get(_user_active_live_key(user_id))
    if active_live_id:
        if isinstance(active_live_id, bytes):
            active_live_id = active_live_id.decode()
        end_live_session(active_live_id, user_id)

    friends_count = get_accepted_friends_count(user_id)
    if friends_count < MIN_FRIENDS_REQUIRED_FOR_LIVE:
        return False, f"Efirga chiqish uchun kamida {MIN_FRIENDS_REQUIRED_FOR_LIVE} ta do'stingiz bo'lishi kerak."

    return True, ""








def create_live_session(user_id: int, title: str = "") -> dict:

    print("=== LIVE DEBUG ===")
    print("USER ID:", user_id)
    print("FRIENDS COUNT:", get_accepted_friends_count(user_id))

    can_start, detail = can_start_livestream(user_id)

    if not can_start:
        return {"ok": False, "detail": detail}

    live_id = uuid.uuid4().hex
    now = _now_ts()
    expires_at = now + LIVE_TTL_SECONDS

# def create_live_session(user_id: int, title: str = "") -> dict:
#     can_start, detail = can_start_livestream(user_id)
#     if not can_start:
#         return {"ok": False, "detail": detail}
#
#
#     live_id = uuid.uuid4().hex
#     now = _now_ts()
#     expires_at = now + LIVE_TTL_SECONDS
#
    live_key = _live_key(live_id)
    user_live_key = _user_active_live_key(user_id)

    pipe = redis_client.pipeline()

    pipe.hset(
        live_key,
        mapping={
            "id": live_id,
            "host_user_id": str(user_id),
            "title": title,
            "status": "live",
            "started_at": str(now),
            "ended_at": "",
            "expires_at": str(expires_at),
            "views": "0",
        },
    )

    pipe.set(user_live_key, live_id)
    pipe.expireat(user_live_key, expires_at)

    pipe.sadd(_active_livestreams_key(), live_id)

    pipe.expireat(live_key, expires_at)
    pipe.expireat(_live_viewers_key(live_id), expires_at)
    pipe.expireat(_live_likes_key(live_id), expires_at)
    pipe.expireat(_live_comments_key(live_id), expires_at)

    pipe.execute()

    return {
        "ok": True,
        "live_id": live_id,
        "host_user_id": user_id,
        "title": title,
        "started_at": now,
    }


def get_live_session(live_id: str) -> Optional[dict]:
    data = redis_client.hgetall(_live_key(live_id))
    if not data:
        return None

    _cleanup_stale_viewers(live_id)

    data["viewers_count"] = redis_client.zcard(_live_viewers_key(live_id))
    data["likes_count"] = redis_client.scard(_live_likes_key(live_id))
    data["comments_count"] = redis_client.zcard(_live_comments_key(live_id))
    return data


def join_live(live_id: str, user_id: int) -> tuple[bool, str]:
    live_data = redis_client.hgetall(_live_key(live_id))
    if not live_data or live_data.get("status") != "live":
        return False, "Live topilmadi yoki tugagan."

    viewer_key = _live_viewers_key(live_id)
    already_viewing = redis_client.zscore(viewer_key, str(user_id)) is not None

    now = _now_ts()
    last_seen_key = _viewer_last_seen_key(live_id, user_id)

    pipe = redis_client.pipeline()
    pipe.zadd(viewer_key, {str(user_id): now})
    pipe.set(last_seen_key, now, ex=VIEWER_HEARTBEAT_TTL_SECONDS)

    expires_at_raw = live_data.get("expires_at")
    if expires_at_raw:
        expires_at = int(expires_at_raw)
        pipe.expireat(viewer_key, expires_at)

    if not already_viewing:
        pipe.hincrby(_live_key(live_id), "views", 1)

    pipe.execute()
    return True, ""




def heartbeat_viewer(live_id: str, user_id: int) -> bool:
    live_data = redis_client.hgetall(_live_key(live_id))
    if not live_data or live_data.get("status") != "live":
        return False

    now = _now_ts()
    viewer_key = _live_viewers_key(live_id)
    last_seen_key = _viewer_last_seen_key(live_id, user_id)

    pipe = redis_client.pipeline()
    pipe.zadd(viewer_key, {str(user_id): now})
    pipe.set(last_seen_key, now, ex=VIEWER_HEARTBEAT_TTL_SECONDS)
    pipe.execute()

    return True


def leave_live(live_id: str, user_id: int) -> bool:
    if not redis_client.exists(_live_key(live_id)):
        return False

    pipe = redis_client.pipeline()
    pipe.zrem(_live_viewers_key(live_id), str(user_id))
    pipe.delete(_viewer_last_seen_key(live_id, user_id))
    pipe.execute()
    return True


def should_broadcast_stats(live_id: str, throttle_seconds: int = 5) -> bool:
    now = _now_ts()
    key = _last_stats_broadcast_key(live_id)

    last_sent = redis_client.get(key)
    if last_sent and now - int(last_sent) < throttle_seconds:
        return False

    redis_client.set(key, now, ex=throttle_seconds + 5)
    return True


def toggle_like_live(live_id: str, user_id: int) -> dict:
    live_data = redis_client.hgetall(_live_key(live_id))
    if not live_data or live_data.get("status") != "live":
        return {"ok": False, "detail": "Live topilmadi yoki tugagan."}

    likes_key = _live_likes_key(live_id)
    member = str(user_id)

    if redis_client.sismember(likes_key, member):
        redis_client.srem(likes_key, member)
        liked = False
    else:
        redis_client.sadd(likes_key, member)
        liked = True

    expires_at_raw = live_data.get("expires_at")
    if expires_at_raw:
        redis_client.expireat(likes_key, int(expires_at_raw))

    return {
        "ok": True,
        "liked": liked,
        "likes_count": redis_client.scard(likes_key),
    }


def add_live_comment(live_id: str, user_id: int, text: str) -> Optional[dict]:
    live_data = redis_client.hgetall(_live_key(live_id))
    if not live_data or live_data.get("status") != "live":
        return None

    now = _now_ts()
    comment_id = uuid.uuid4().hex

    comment_key = _live_comment_key(live_id, comment_id)
    comments_key = _live_comments_key(live_id)

    pipe = redis_client.pipeline()
    pipe.hset(
        comment_key,
        mapping={
            "id": comment_id,
            "live_id": live_id,
            "user_id": str(user_id),
            "text": text,
            "created_at": str(now),
        },
    )
    pipe.zadd(comments_key, {comment_id: now})

    expires_at = int(live_data["expires_at"])
    pipe.expireat(comment_key, expires_at)
    pipe.expireat(comments_key, expires_at)
    pipe.execute()

    return {
        "id": comment_id,
        "live_id": live_id,
        "user_id": user_id,
        "text": text,
        "created_at": now,
    }


def get_live_comments(live_id: str, limit: int = 50) -> list[dict]:
    if not redis_client.exists(_live_key(live_id)):
        return []

    comment_ids = redis_client.zrevrange(_live_comments_key(live_id), 0, limit - 1)
    result = []

    for comment_id in comment_ids:
        data = redis_client.hgetall(_live_comment_key(live_id, comment_id))
        if data:
            result.append(data)

    return result


def get_live_viewers_with_profiles(live_id: str) -> list[dict]:
    if not redis_client.exists(_live_key(live_id)):
        return []

    _cleanup_stale_viewers(live_id)

    viewers = redis_client.zrevrange(
        _live_viewers_key(live_id),
        0,
        -1,
        withscores=True,
    )

    user_ids = [int(user_id) for user_id, _ in viewers]
    users = User.objects.filter(id__in=user_ids).select_related("profile")
    user_map = {u.id: u for u in users}

    result = []
    for user_id, score in viewers:
        user_id = int(user_id)
        user = user_map.get(user_id)
        if not user:
            continue

        profile = getattr(user, "profile", None)

        result.append(
            {
                "user_id": user.id,
                "phone": user.phone,
                "username": getattr(profile, "username", ""),
                "full_name": getattr(profile, "full_name", ""),
                "avatar": profile.avatar.url if profile and profile.avatar else None,
                "viewed_at": int(score),
            }
        )

    return result


def _get_user_profiles_map(user_ids: list[int]) -> dict[int, dict]:
    if not user_ids:
        return {}

    users = User.objects.filter(id__in=user_ids).select_related("profile")
    user_map = {}
    for user in users:
        profile = getattr(user, "profile", None)
        user_map[user.id] = {
            "user_id": user.id,
            "phone": user.phone,
            "username": getattr(profile, "username", "") or f"user_{user.id}",
            "full_name": getattr(profile, "full_name", "") or "",
            "avatar": profile.avatar.url if profile and profile.avatar else None,
        }
    return user_map


def get_active_livestreams() -> list[dict]:
    active_ids = redis_client.smembers(_active_livestreams_key())
    if not active_ids:
        return []

    stream_ids = []
    for sid in active_ids:
        if isinstance(sid, bytes):
            sid = sid.decode()
        stream_ids.append(sid)

    stale_stream_ids = []
    streams_data = []

    for live_id in stream_ids:
        session = redis_client.hgetall(_live_key(live_id))
        if not session or session.get("status") != "live":
            stale_stream_ids.append(live_id)
            continue

        _cleanup_stale_viewers(live_id)
        session["viewers_count"] = redis_client.zcard(_live_viewers_key(live_id))
        session["likes_count"] = redis_client.scard(_live_likes_key(live_id))
        session["comments_count"] = redis_client.zcard(_live_comments_key(live_id))
        streams_data.append(session)

    if stale_stream_ids:
        redis_client.srem(_active_livestreams_key(), *stale_stream_ids)

    if not streams_data:
        return []

    all_user_ids = set()
    for session in streams_data:
        if session.get("host_user_id"):
            all_user_ids.add(int(session["host_user_id"]))

        raw_viewers = redis_client.zrevrange(_live_viewers_key(session["id"]), 0, -1, withscores=True)
        session["_raw_viewers"] = raw_viewers
        for uid, _ in raw_viewers:
            all_user_ids.add(int(uid))

    user_profiles_map = _get_user_profiles_map(list(all_user_ids))

    result = []
    for session in streams_data:
        live_id = session["id"]
        host_user_id = int(session.get("host_user_id", 0))
        host_info = user_profiles_map.get(
            host_user_id,
            {
                "user_id": host_user_id,
                "phone": "",
                "username": f"user_{host_user_id}",
                "full_name": "",
                "avatar": None,
            },
        )

        viewers_list = []
        for uid, score in session.get("_raw_viewers", []):
            uid = int(uid)
            v_info = user_profiles_map.get(uid)
            if v_info:
                v_item = dict(v_info)
                v_item["viewed_at"] = int(score)
                viewers_list.append(v_item)

        result.append(
            {
                "live_id": live_id,
                "title": session.get("title", ""),
                "status": session.get("status", "live"),
                "started_at": int(session.get("started_at", 0)),
                "views": int(session.get("views", 0)),
                "likes_count": int(session.get("likes_count", 0)),
                "comments_count": int(session.get("comments_count", 0)),
                "viewers_count": len(viewers_list),
                "host": host_info,
                "viewers": viewers_list,
            }
        )

    return result


def get_live_stats(live_id: str) -> Optional[dict]:
    live_data = get_live_session(live_id)
    if not live_data:
        return None

    host_user_id = int(live_data.get("host_user_id", 0))
    viewers = get_live_viewers_with_profiles(live_id)

    host_map = _get_user_profiles_map([host_user_id])
    host_info = host_map.get(
        host_user_id,
        {
            "user_id": host_user_id,
            "phone": "",
            "username": f"user_{host_user_id}",
            "full_name": "",
            "avatar": None,
        },
    )

    return {
        "live_id": live_id,
        "status": live_data.get("status"),
        "host_user_id": host_user_id,
        "host": host_info,
        "title": live_data.get("title"),
        "started_at": int(live_data.get("started_at", 0)) if live_data.get("started_at") else 0,
        "viewers_count": len(viewers),
        "likes_count": int(live_data.get("likes_count", 0)),
        "comments_count": int(live_data.get("comments_count", 0)),
        "views": int(live_data.get("views", 0)),
        "viewers": viewers,
    }


def end_live_session(live_id: str, requested_by_user_id: int) -> dict:
    live_data = redis_client.hgetall(_live_key(live_id))
    if not live_data:
        return {"ok": False, "detail": "Live topilmadi."}

    host_user_id = int(live_data["host_user_id"])
    if host_user_id != requested_by_user_id:
        return {"ok": False, "detail": "Faqat live egasi efirni tugata oladi."}

    comment_ids = redis_client.zrange(_live_comments_key(live_id), 0, -1)
    viewer_ids = redis_client.zrange(_live_viewers_key(live_id), 0, -1)

    pipe = redis_client.pipeline()

    for comment_id in comment_ids:
        pipe.delete(_live_comment_key(live_id, comment_id))

    for viewer_id in viewer_ids:
        pipe.delete(_viewer_last_seen_key(live_id, int(viewer_id)))

    pipe.delete(
        _live_key(live_id),
        _live_viewers_key(live_id),
        _live_likes_key(live_id),
        _live_comments_key(live_id),
        _last_stats_broadcast_key(live_id),
        _user_active_live_key(host_user_id),
    )
    pipe.srem(_active_livestreams_key(), live_id)
    pipe.execute()

    return {"ok": True, "detail": "Live tugatildi va Redisdan o‘chirildi."}


def _cleanup_stale_viewers(live_id: str) -> None:
    viewer_key = _live_viewers_key(live_id)
    viewer_ids = redis_client.zrange(viewer_key, 0, -1)

    stale_ids = []
    for viewer_id in viewer_ids:
        if not redis_client.exists(_viewer_last_seen_key(live_id, int(viewer_id))):
            stale_ids.append(viewer_id)

    if stale_ids:
        redis_client.zrem(viewer_key, *stale_ids)