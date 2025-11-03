# Procfile — chuẩn cho Django Channels chạy trên Render

# Chạy migrate riêng biệt trước khi khởi động web server
release: python manage.py makemigrations --noinput && python manage.py migrate --noinput

# Khởi động server Daphne để xử lý HTTP + WebSocket
web: daphne -b 0.0.0.0 -p $PORT chat_project.asgi:application
