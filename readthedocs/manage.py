#!/usr/bin/env python

import settings.sqlite
from django.core.management import execute_manager
execute_manager(settings.sqlite)
