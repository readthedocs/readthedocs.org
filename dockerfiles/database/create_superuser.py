#!/usr/bin/env python
import os
import sys


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.sqlite")
    sys.path.append('readthedocs')

    from django.contrib.auth.models import User
    User.objects.create_superuser('admin', 'admin@example.com', 'password')
