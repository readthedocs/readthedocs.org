import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Charlie Leifer', 'coleifer@gmail.com'),
    ('Eric Holscher', 'eric@ericholscher.com'),
)

MANAGERS = ADMINS

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

MEDIA_ROOT = '%s/media/' % (SITE_ROOT)
MEDIA_URL = '/media/'
ADMIN_MEDIA_PREFIX = '/media/admin/'

CACHE_BACKEND = 'memcached://localhost:11211/'
CACHE_KEY_PREFIX = 'docs'
CACHE_MIDDLEWARE_SECONDS = 60

FORCE_WWW = True
LOGIN_REDIRECT_URL = '/'

if DEBUG:
    CACHE_BACKEND = 'dummy://'
    #DATABASES['default']['HOST'] = 'localhost'

TIME_ZONE = 'America/Chicago'
LANGUAGE_CODE = 'en-us'
USE_I18N = True
SITE_ID = 1
SECRET_KEY = 'asciidick'

ACCOUNT_ACTIVATION_DAYS = 7

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    '%s/templates/' % (SITE_ROOT),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.comments',
    'django.contrib.contenttypes',
    'django.contrib.flatpages',
    'django.contrib.markup',
    'django.contrib.sessions',
    'django.contrib.sites',

    # third party apps
    'pagination',
    'profiles',
    'registration',
    'djcelery',
    'ghettoq',
    'south',

    # our apps
    'projects',
)
