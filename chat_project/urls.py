from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Trang quản trị
    path('admin/', admin.site.urls),

    # Ứng dụng Chat
    path('chat/', include('chat.urls')),

    # Đăng nhập / đăng xuất
    path('login/', auth_views.LoginView.as_view(template_name='chat/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/chat/login/'), name='logout'),

    # Trang mặc định → chuyển đến trang login
    path('', lambda request: redirect('login')),
]

# Cho phép hiển thị ảnh trong MEDIA (nếu DEBUG=True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
