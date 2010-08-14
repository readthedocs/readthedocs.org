from .base import *
import os.path


DATABASES = {
        'default': 
                {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': os.path.join(SITE_ROOT, 'dev.db'),
                }
}
