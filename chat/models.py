from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from cryptography.fernet import Fernet

class Room(models.Model):
    name = models.CharField(max_length=255, unique=True)
    is_private = models.BooleanField(default=False)
    password = models.CharField(max_length=128, blank=True, null=True)
    members = models.ManyToManyField(User, related_name="rooms", blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_rooms", null=True, blank=True)  # ✅ ai tạo phòng

    def __str__(self):
        return self.name

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)



class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to="chat_images/", null=True, blank=True)
    file = models.FileField(upload_to="chat_files/", null=True, blank=True)  # ✅ thêm dòng này
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.room.name}: {self.content[:30]}"



class UserStatus(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="status")
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} ({'Online' if self.is_online else 'Offline'})"
from cryptography.fernet import Fernet
from django.conf import settings

# Sinh 1 khóa bí mật (chạy 1 lần duy nhất)
# import os; from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())

ENCRYPTION_KEY = b"n5QergO_eFsagxO-wIon6QCJhxKYNodnRWVX9s6ueMw="
fernet = Fernet(ENCRYPTION_KEY)

class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)
    file = models.FileField(upload_to='chat_files/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.content:
            self.content = fernet.encrypt(self.content.encode()).decode()
        super().save(*args, **kwargs)

    def decrypted(self):
        if not self.content:
            return ""
        try:
            return fernet.decrypt(self.content.encode()).decode()
        except Exception:
            return "[Tin nhắn mã hóa lỗi]"
