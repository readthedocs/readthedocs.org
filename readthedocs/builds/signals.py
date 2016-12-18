"""Build signals"""

import django.dispatch


build_complete = django.dispatch.Signal(providing_args=['build'])
