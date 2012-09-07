import os
import djcelery
djcelery.setup_loader()

DEBUG = True
TEMPLATE_DEBUG = DEBUG
TASTYPIE_FULL_DEBUG = True

ADMINS = (
    ('Charlie Leifer', 'coleifer@gmail.com'),
    ('Eric Holscher', 'eric@ericholscher.com'),
)

MANAGERS = ADMINS

SITE_ROOT = '/'.join(os.path.dirname(__file__).split('/')[0:-2])
DOCROOT = os.path.join(SITE_ROOT, 'user_builds')
UPLOAD_ROOT = os.path.join(SITE_ROOT, 'user_uploads')
CNAME_ROOT = os.path.join(SITE_ROOT, 'cnames')
LOGS_ROOT = os.path.join(SITE_ROOT, 'logs')

MEDIA_ROOT = '%s/media/' % (SITE_ROOT)
MEDIA_URL = '/media/'
ADMIN_MEDIA_PREFIX = '/media/admin/'

CACHE_BACKEND = 'memcached://localhost:11211/'
CACHE_KEY_PREFIX = 'docs'
CACHE_MIDDLEWARE_SECONDS = 60

LOGIN_REDIRECT_URL = '/dashboard/'
FORCE_WWW = False
#APPEND_SLASH = False

TIME_ZONE = 'America/Chicago'
LANGUAGE_CODE = 'en-us'
USE_I18N = True
SITE_ID = 1
SECRET_KEY = 'asciidick'

ACCOUNT_ACTIVATION_DAYS = 7


TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'pagination.middleware.PaginationMiddleware',
    'core.middleware.SubdomainMiddleware',
    #'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    '%s/readthedocs/templates/' % (SITE_ROOT),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request"
)

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.markup',
    'django.contrib.sessions',
    'django.contrib.sites',

    # third party apps
    'pagination',
    'registration',
    'profiles',
    'taggit',
    'south',
    'basic.flagging',
    'djcelery',
    #'celery_haystack',

    #daniellindsleyrocksdahouse
    'haystack',
    'tastypie',

    # our apps
    'projects',
    'builds',
    'core',
    'rtd_tests',
]

if DEBUG:
    INSTALLED_APPS.append('django_extensions')


#CARROT_BACKEND = "ghettoq.taproot.Database"
CELERY_ALWAYS_EAGER = True
CELERYD_TASK_TIME_LIMIT = 60*60 #60 minutes
CELERY_SEND_TASK_ERROR_EMAILS = True


DEFAULT_FROM_EMAIL = "no-reply@readthedocs.org"
SESSION_COOKIE_DOMAIN = 'readthedocs.org'

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
    },
}


AUTH_PROFILE_MODULE = "core.UserProfile"
SOUTH_TESTS_MIGRATE = False

ABSOLUTE_URL_OVERRIDES = {
    'auth.user': lambda o: "/profiles/%s/" % o.username
}

INTERNAL_IPS = ('127.0.0.1',)

IMPORT_EXTERNAL_DATA = True

backup_count = 1000
if DEBUG:
    backup_count = 2

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'null': {
            'level':'DEBUG',
            'class':'django.utils.log.NullHandler',
        },
        'logfile': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_ROOT, "rtd.log"),
            'maxBytes': 50000,
            'backupCount': backup_count,
            'formatter': 'standard',
        },
        'errorlog': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_ROOT, "rtd.log"),
            'maxBytes': 50000,
            'backupCount': backup_count,
            'formatter': 'standard',
        },
        'db': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_ROOT, "db.log"),
            'maxBytes': 50000,
            'backupCount': backup_count,
            'formatter': 'standard',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'standard'
        },
    },
    'loggers': {
        'django': {
            'handlers':['console', 'errorlog'],
            'propagate': True,
            'level':'WARN',
        },
        'django.db.backends': {
            'handlers': ['db'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        #Default handler for everything that we're doing. Hopefully this doesn't double-print
        #the Django things as well. Not 100% sure how logging works :)
        '': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
    }
}
