from django.urls import path
from . import views

urlpatterns = [
    path("home/", views.home, name="home"),
    path("create/", views.create_room, name="create_room"),
    path("room/<str:room_name>/", views.room, name="room"),
    path("room/<str:room_name>/delete/", views.delete_room, name="delete_room"),  # ✅ Thêm dòng này
    path("register/", views.register, name="register"),
]
