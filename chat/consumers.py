# chat/consumers.py
import json
import base64
import imghdr
import uuid
import mimetypes
import logging

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.core.files.base import ContentFile
from django.utils import timezone

from .models import Room, Message, UserStatus

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        Accept connection, join room group, mark user online and send history.
        """
        try:
            self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        except Exception as e:
            logger.exception("No room_name in scope: %s", e)
            await self.close()
            return

        self.room_group_name = f"chat_{self.room_name}"

        # Join group then accept connection
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # set user status if authenticated
        user = self.scope.get("user")
        if user and getattr(user, "is_authenticated", False):
            try:
                await self.set_user_status(user, True)
            except Exception:
                logger.exception("Failed to set user status on connect")

        # send recent history
        try:
            history = await self.get_history(self.room_name, limit=50)
            await self.send(text_data=json.dumps({
                "type": "history",
                "messages": history
            }))
        except Exception:
            logger.exception("Failed to send history")

    async def disconnect(self, close_code):
        """
        Leave group and mark user offline on disconnect.
        """
        user = self.scope.get("user")
        if user and getattr(user, "is_authenticated", False):
            try:
                await self.set_user_status(user, False)
            except Exception:
                logger.exception("Failed to set user status on disconnect")

        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        """
        Handle incoming messages from WebSocket.
        Expected JSON structure:
          { "type": "chat", "message": "..." }
          { "type": "typing" }
          { "type": "image", "image": "data:image/png;base64,..." }
          { "type": "file", "file": "data:...;base64,...", "filename": "name.ext" }
        """
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except Exception:
            logger.exception("Invalid JSON received")
            return

        msg_type = data.get("type")
        user = self.scope.get("user")
        username = user.username if user and hasattr(user, "username") else "Anonymous"

        # Typing indicator
        if msg_type == "typing":
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "broadcast_typing", "username": username}
            )
            return

        # --- TEXT MESSAGE ---
        if msg_type == "chat":
            text = (data.get("message") or "").strip()
            if not text or not user or not getattr(user, "is_authenticated", False):
                return

            try:
                msg_obj = await self.create_text_message(user, self.room_name, text)
                ts = timezone.localtime(msg_obj.timestamp).strftime("%H:%M %d/%m/%Y")
            except Exception:
                logger.exception("Failed to create text message")
                return

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "broadcast_chat",
                    "username": username,
                    "message": text,
                    "timestamp": ts,
                }
            )
            return

        # --- IMAGE MESSAGE ---
        if msg_type == "image":
            image_data_url = data.get("image")
            if not image_data_url or not user or not getattr(user, "is_authenticated", False):
                return

            try:
                msg_obj = await self.create_image_message(user, self.room_name, image_data_url)
                image_url = msg_obj.image.url if msg_obj and msg_obj.image else image_data_url
                ts = timezone.localtime(msg_obj.timestamp).strftime("%H:%M %d/%m/%Y") if msg_obj else timezone.now().strftime("%H:%M %d/%m/%Y")
            except Exception:
                logger.exception("Failed to create image message")
                image_url = image_data_url
                ts = timezone.now().strftime("%H:%M %d/%m/%Y")

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "broadcast_image",
                    "username": username,
                    "image": image_url,
                    "timestamp": ts,
                }
            )
            return

        # --- FILE MESSAGE ---
        if msg_type == "file":
            file_data_url = data.get("file")
            original_name = data.get("filename", "file")
            if not file_data_url or not user or not getattr(user, "is_authenticated", False):
                return

            try:
                msg_obj = await self.create_file_message(user, self.room_name, file_data_url, original_name)
                file_url = msg_obj.file.url if msg_obj and msg_obj.file else None
                ts = timezone.localtime(msg_obj.timestamp).strftime("%H:%M %d/%m/%Y") if msg_obj else timezone.now().strftime("%H:%M %d/%m/%Y")
            except Exception:
                logger.exception("Failed to create file message")
                return

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "broadcast_file",
                    "username": username,
                    "filename": original_name,
                    "file_url": file_url,
                    "timestamp": ts,
                }
            )
            return

    # ---------------- BROADCAST HANDLERS -----------------
    async def broadcast_chat(self, event):
        await self.send(text_data=json.dumps({
            "type": "chat",
            "username": event.get("username"),
            "message": event.get("message"),
            "timestamp": event.get("timestamp"),
        }))

    async def broadcast_image(self, event):
        await self.send(text_data=json.dumps({
            "type": "image",
            "username": event.get("username"),
            "image": event.get("image"),
            "timestamp": event.get("timestamp"),
        }))

    async def broadcast_file(self, event):
        await self.send(text_data=json.dumps({
            "type": "file",
            "username": event.get("username"),
            "filename": event.get("filename"),
            "file_url": event.get("file_url"),
            "timestamp": event.get("timestamp"),
        }))

    async def broadcast_typing(self, event):
        await self.send(text_data=json.dumps({
            "type": "typing",
            "username": event.get("username"),
        }))

    # ---------------- DATABASE METHODS (sync -> async wrappers) -----------------
    @database_sync_to_async
    def get_history(self, room_name, limit=50):
        try:
            room = Room.objects.get(name=room_name)
        except Room.DoesNotExist:
            return []

        qs = Message.objects.filter(room=room).order_by("-timestamp")[:limit]
        msgs = []
        for m in reversed(qs):
            msg_type = "file" if m.file else ("image" if m.image else "text")
            msgs.append({
                "username": m.user.username if m.user else "Anonymous",
                "message": m.content or "",
                "type": msg_type,
                "image": m.image.url if m.image else None,
                "file": m.file.url if m.file else None,
                "filename": m.file.name.split("/")[-1] if m.file else None,
                "timestamp": timezone.localtime(m.timestamp).strftime("%H:%M %d/%m/%Y"),
            })
        return msgs

    @database_sync_to_async
    def create_text_message(self, user, room_name, text):
        room, _ = Room.objects.get_or_create(name=room_name)
        return Message.objects.create(user=user, room=room, content=text)

    @database_sync_to_async
    def create_image_message(self, user, room_name, data_url):
        if "," not in data_url:
            raise ValueError("Invalid image data URL")
        header, b64data = data_url.split(",", 1)
        ext = header.split(";")[0].split("/")[-1]
        decoded = base64.b64decode(b64data)
        kind = imghdr.what(None, decoded) or ext or "png"
        filename = f"{uuid.uuid4().hex}.{kind}"
        room, _ = Room.objects.get_or_create(name=room_name)
        msg = Message.objects.create(user=user, room=room, content="")
        msg.image.save(filename, ContentFile(decoded), save=True)
        return msg

    @database_sync_to_async
    def create_file_message(self, user, room_name, data_url, original_name):
        if "," not in data_url:
            raise ValueError("Invalid file data URL")
        header, b64data = data_url.split(",", 1)
        decoded = base64.b64decode(b64data)

        ext = mimetypes.guess_extension(header.split(";")[0].split(":")[-1]) or ""
        filename = f"{uuid.uuid4().hex}_{original_name}"

        room, _ = Room.objects.get_or_create(name=room_name)
        msg = Message.objects.create(user=user, room=room, content="")
        msg.file.save(filename, ContentFile(decoded), save=True)
        return msg

    @database_sync_to_async
    def set_user_status(self, user, is_online):
        status, _ = UserStatus.objects.get_or_create(user=user)
        status.is_online = is_online
        status.last_seen = timezone.now()
        status.save()
        return status
