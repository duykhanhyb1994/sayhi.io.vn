web: bash -c "python manage.py makemigrations --noinput && python manage.py migrate --noinput && daphne -b 0.0.0.0 -p $PORT chat_project.asgi:application"
