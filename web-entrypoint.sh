#! /bin/sh

python manage.py migrate
echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'pass')" | python manage.py shell
python manage.py collectstatic --no-input
python manage.py loaddata test_data

gunicorn readthedocs.wsgi:application -w 3 -b :8000