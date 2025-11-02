from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Room
from django.contrib.auth.models import User
from django.contrib.auth import login

@login_required
def home(request):
    rooms = Room.objects.all()
    return render(request, "chat/home.html", {"rooms": rooms})

@login_required
def create_room(request):
    """Tạo phòng (có thể đặt mật khẩu)"""
    if request.method == "POST":
        name = request.POST.get("name").strip()
        password = request.POST.get("password", "").strip()

        if not name:
            messages.error(request, "⚠️ Tên phòng không được để trống.")
            return redirect("create_room")

        if Room.objects.filter(name=name).exists():
            messages.error(request, "⚠️ Phòng đã tồn tại.")
            return redirect("create_room")

        room = Room.objects.create(name=name, created_by=request.user)  # ✅ ghi lại người tạo
        if password:
            room.set_password(password)
            room.is_private = True
        room.save()
        room.members.add(request.user)

        messages.success(request, f"✅ Đã tạo phòng '{room.name}' thành công.")
        return redirect("home")

    return render(request, "chat/create_room.html")

@login_required
def delete_room(request, room_name):
    """Xóa phòng (chỉ admin hoặc người tạo mới được quyền)"""
    room = get_object_or_404(Room, name=room_name)

    if request.user == room.created_by or request.user.is_superuser:
        room.delete()
        messages.success(request, f"🗑️ Đã xóa phòng '{room_name}'.")
    else:
        messages.error(request, "❌ Bạn không có quyền xóa phòng này.")

    return redirect("home")

@login_required
def room(request, room_name):
    """Kiểm tra mật khẩu trước khi vào phòng"""
    room = get_object_or_404(Room, name=room_name)

    if room.password and not request.session.get(f"room_access_{room_name}", False):
        if request.method == "POST":
            input_pw = request.POST.get("password")
            if room.check_password(input_pw):
                request.session[f"room_access_{room_name}"] = True
                messages.success(request, f"🔓 Đã vào phòng '{room_name}'")
                return redirect("room", room_name=room_name)
            else:
                messages.error(request, "❌ Mật khẩu sai, vui lòng thử lại.")
        return render(request, "chat/enter_password.html", {"room": room})

    return render(request, "chat/room.html", {"room_name": room_name})

def register(request):
    """Đăng ký tài khoản"""
    if request.method == "POST":
        username = request.POST.get("username").strip()
        password = request.POST.get("password").strip()

        if not username or not password:
            return render(request, "chat/register.html", {"error": "Vui lòng nhập đủ tên và mật khẩu."})

        if User.objects.filter(username=username).exists():
            return render(request, "chat/register.html", {"error": "Tên người dùng đã tồn tại."})

        user = User.objects.create_user(username=username, password=password)
        login(request, user)
        return redirect("home")

    return render(request, "chat/register.html")
