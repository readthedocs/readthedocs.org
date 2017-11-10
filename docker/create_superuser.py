# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from allauth.account.models import EmailAddress

query = User.objects.filter(username='admin')
if not query.exists():
    admin = User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    EmailAddress.objects.create(user=admin, email='admin@example.com', primary=True, verified=True)
    print('`admin` user created')
else:
    print('`admin` user already exists')

print('Exit.')
