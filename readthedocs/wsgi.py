"""WSGI application helper."""

import os


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "readthedocs.settings.docker_compose")

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
from django.core.wsgi import get_wsgi_application  # noqa

application = get_wsgi_application()
