import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Charlie Leifer', 'coleifer@gmail.com'),
    ('Eric Holscher', 'eric@ericholscher.com'),
)

MANAGERS = ADMINS

SITE_ROOT = '/'.join(os.path.dirname(__file__).split('/')[0:-1])
DOCROOT = os.path.join(SITE_ROOT, 'user_builds')

MEDIA_ROOT = '%s/media/' % (SITE_ROOT)
MEDIA_URL = '/media/'
ADMIN_MEDIA_PREFIX = '/media/admin/'

CACHE_BACKEND = 'memcached://localhost:11211/'
CACHE_KEY_PREFIX = 'docs'
CACHE_MIDDLEWARE_SECONDS = 60

LOGIN_REDIRECT_URL = '/dashboard/'
FORCE_WWW = False

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
    'pagination.middleware.PaginationMiddleware',
    'core.middleware.NginxSSIMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    '%s/templates/' % (SITE_ROOT),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request"
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
    'taggit',
    'south',
    'taggit',
    'django_extensions',
    #'basic.flagging',

    # our apps
    'projects',
    'core',
    'watching',
)


CARROT_BACKEND = "ghettoq.taproot.Database"
CELERY_ALWAYS_EAGER = True
