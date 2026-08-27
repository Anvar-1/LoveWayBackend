from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from .services import should_broadcast_stats
from .services import (add_live_comment, get_live_stats, heartbeat_viewer, join_live, leave_live, toggle_like_live,)


class LiveConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.live_id = self.scope["url_route"]["kwargs"]["live_id"]
        self.room_group_name = f"live_room_{self.live_id}"
        self.user = self.scope.get("user")
        self.joined = False

        await self.accept()

        if not self.user or not self.user.is_authenticated:
            await self._send_error("Autentifikatsiya talab qilinadi.")
            await self.close(code=4001)
            return

        joined, err_msg = await database_sync_to_async(join_live)(self.live_id, self.user.id)
        if not joined:
            await self._send_error(err_msg or "Live topilmadi yoki tugagan.")
            await self.close(code=4004)
            return


        self.joined = True

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.send_json({
            "type": "connected",
            "data": {
                "live_id": self.live_id,
                "user_id": self.user.id,
            },
        })

        await self._broadcast_stats()

    async def disconnect(self, close_code):
        try:
            if getattr(self, "joined", False) and self.user and self.user.is_authenticated:
                await database_sync_to_async(leave_live)(self.live_id, self.user.id)
                self.joined = False
                await self._broadcast_stats()
        finally:
            try:
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name,
                )
            except Exception:
                pass

    async def receive_json(self, content, **kwargs):
        if not self.user or not self.user.is_authenticated:
            await self._send_error("Autentifikatsiya talab qilinadi.")
            await self.close(code=4001)
            return

        if not self.joined:
            await self._send_error("Live session faol emas.")
            await self.close(code=4004)
            return

        action = (content.get("action") or "").strip().lower()

        if action == "heartbeat":
            ok = await database_sync_to_async(heartbeat_viewer)(self.live_id, self.user.id)
            if not ok:
                await self._send_error("Live topilmadi yoki tugagan.")
                await self.close(code=4004)
                return

            await self.send_json({
                "type": "heartbeat",
                "data": {"ok": True},
            })
            await self._broadcast_stats()
            return

        if action == "like":
            result = await database_sync_to_async(toggle_like_live)(self.live_id, self.user.id)
            if not result.get("ok"):
                await self._send_error(result.get("detail", "Like bajarilmadi."))
                return

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "live.like",
                    "payload": {
                        "user_id": self.user.id,
                        "liked": result.get("liked", False),
                        "likes_count": result.get("likes_count", 0),
                    },
                },
            )

            await self._broadcast_stats()
            return

        if action == "comment":
            text = (content.get("text") or "").strip()
            if not text:
                await self._send_error("Comment bo‘sh bo‘lmasligi kerak.")
                return

            comment = await database_sync_to_async(add_live_comment)(
                self.live_id,
                self.user.id,
                text,
            )
            if not comment:
                await self._send_error("Live topilmadi yoki tugagan.")
                return

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "live.comment",
                    "payload": comment,
                },
            )

            await self._broadcast_stats()
            return

        if action == "leave":
            await database_sync_to_async(leave_live)(self.live_id, self.user.id)
            self.joined = False

            await self.send_json({
                "type": "left",
                "data": {
                    "live_id": self.live_id,
                    "user_id": self.user.id,
                },
            })

            await self._broadcast_stats()
            await self.close(code=1000)
            return

        await self._send_error("Noma’lum action.")

    async def live_comment(self, event):
        await self.send_json({
            "type": "comment",
            "data": event["payload"],
        })

    async def live_like(self, event):
        await self.send_json({
            "type": "like",
            "data": event["payload"],
        })

    async def live_stats(self, event):
        await self.send_json({
            "type": "stats",
            "data": event["stats"],
        })

    async def _broadcast_stats(self):
        stats = await database_sync_to_async(get_live_stats)(self.live_id)

        if not stats:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "live.stats",
                    "stats": {
                        "live_id": self.live_id,
                        "status": "ended",
                        "viewers_count": 0,
                        "likes_count": 0,
                        "comments_count": 0,
                    },
                },
            )
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "live.stats",
                "stats": stats,
            },
        )

    async def _send_error(self, detail: str):
        await self.send_json({
            "type": "error",
            "detail": detail,
        })


class LiveFeedConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        self.group_name = "global_livestreams"

        await self.accept()

        if not self.user or not self.user.is_authenticated:
            await self.send_json({
                "type": "error",
                "detail": "Autentifikatsiya talab qilinadi.",
            })
            await self.close(code=4001)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)

        await self.send_json({
            "type": "connected",
            "data": {
                "message": "Live feedga ulandingiz",
            },
        })

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        except Exception:
            pass

    async def live_started(self, event):
        await self.send_json({
            "type": "live_started",
            "data": event["payload"],
        })

    async def live_ended(self, event):
        await self.send_json({
            "type": "live_ended",
            "data": event["payload"],
        })

    async def _broadcast_stats(self):

        allowed = await database_sync_to_async(
            should_broadcast_stats
        )(self.live_id)

        if not allowed:
            return

        stats = await database_sync_to_async(
            get_live_stats
        )(self.live_id)

        if not stats:
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "live.stats",
                "stats": stats,
            },
        )