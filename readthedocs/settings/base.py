# encoding: utf-8
import os
import djcelery
from kombu.common import Broadcast
from kombu import Exchange, Queue

djcelery.setup_loader()

_ = gettext = lambda s: s

DEBUG = True
TEMPLATE_DEBUG = DEBUG
TASTYPIE_FULL_DEBUG = True
LOG_DEBUG = False

PRODUCTION_DOMAIN = 'readthedocs.org'
USE_SUBDOMAIN = False

ADMINS = (
    ('Eric Holscher', 'eric@readthedocs.org'),
    ('Anthony Johnson', 'anthony@readthedocs.org'),
)

MANAGERS = ADMINS

SITE_ROOT = '/'.join(os.path.dirname(os.path.realpath(__file__)).split('/')[0:-2])
DOCROOT = os.path.join(SITE_ROOT, 'user_builds')
UPLOAD_ROOT = os.path.join(SITE_ROOT, 'user_uploads')
CNAME_ROOT = os.path.join(SITE_ROOT, 'cnames')
LOGS_ROOT = os.path.join(SITE_ROOT, 'logs')

# A new base for production files
PRODUCTION_ROOT = os.path.join(SITE_ROOT, 'prod_artifacts')
PRODUCTION_MEDIA_ARTIFACTS = os.path.join(PRODUCTION_ROOT, 'media')

MEDIA_ROOT = '%s/media/' % (SITE_ROOT)
MEDIA_URL = '/media/'
ADMIN_MEDIA_PREFIX = '/media/admin/'

GROK_API_HOST = 'https://api.grokthedocs.com'

# For 1.4
STATIC_ROOT = os.path.join(SITE_ROOT, 'media/static/')
STATIC_URL = '/static/'
#STATICFILES_DIRS = ()
#STATICFILES_FINDERS = ()

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        'PREFIX': 'docs',
    }
}

CACHE_MIDDLEWARE_SECONDS = 60

LOGIN_REDIRECT_URL = '/dashboard/'
FORCE_WWW = False
#APPEND_SLASH = False

# Docker
DOCKER_ENABLE = False
DOCKER_IMAGE = 'rtfd-build'

TIME_ZONE = 'America/Chicago'
LANGUAGE_CODE = 'en-us'
LANGUAGES = (
    ('en', gettext('English')),
    ('es', gettext('Spanish')),
    ('nb', gettext('Norwegian Bokmål')),
    ('fr', gettext('French')),
    ('ru', gettext('Russian')),
    ('de', gettext('German')),
    ('gl', gettext('Galician')),
    ('vi', gettext('Vietnamese')),
    ('zh-cn', gettext('Chinese')),
    ('zh-tw', gettext('Taiwanese')),
    ('ja', gettext('Japanese')),
    ('uk', gettext('Ukrainian')),
    ('it', gettext('Italian')),
)
LOCALE_PATHS = [
    os.path.join(SITE_ROOT, 'readthedocs', 'locale'),
]


USE_I18N = True
USE_L10N = True
SITE_ID = 1
SECRET_KEY = 'replace-this-please'

ACCOUNT_ACTIVATION_DAYS = 7


ATOMIC_REQUESTS = True

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'djangosecure.middleware.SecurityMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'pagination.middleware.PaginationMiddleware',
    'maintenancemode.middleware.MaintenanceModeMiddleware',
    # Hack
    # 'core.underscore_middleware.UnderscoreMiddleware',
    'core.middleware.SubdomainMiddleware',
    'core.middleware.SingleVersionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    #'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
)

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
)

# All auth

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"

CORS_ORIGIN_REGEX_WHITELIST = ('^http://(.+)\.readthedocs\.org$', '^https://(.+)\.readthedocs\.org$')
# So people can post to their accounts
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = (
    'x-requested-with',
    'content-type',
    'accept',
    'origin',
    'authorization',
    'x-csrftoken'
)


ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    '%s/readthedocs/templates/' % SITE_ROOT,
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
    # Read the Docs processor
    "core.context_processors.readthedocs_processor",
    # allauth specific context processors
    "allauth.account.context_processors.account",
    "allauth.socialaccount.context_processors.socialaccount",
)

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django.contrib.messages',

    # third party apps
    'pagination',
    'profiles',
    'taggit',
    'south',
    'djangosecure',
    'guardian',
    'django_gravatar',
    'rest_framework',
    'corsheaders',
    'copyright',

    # Celery bits
    'djcelery',

    # daniellindsleyrocksdahouse
    'haystack',
    'tastypie',



    # our apps
    'bookmarks',
    'projects',
    'builds',
    'comments',
    'core',
    'doc_builder',
    'oauth',
    'redirects',
    'rtd_tests',
    'restapi',
    'privacy',
    'gold',
    'donate',

    # allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.github',
    'allauth.socialaccount.providers.bitbucket',
    #'allauth.socialaccount.providers.twitter',
]

SOUTH_MIGRATION_MODULES = {
    'taggit': 'taggit.south_migrations',
}

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAdminUser',),
    'DEFAULT_FILTER_BACKENDS': ('rest_framework.filters.DjangoFilterBackend',),
    'PAGINATE_BY': 10
}

if DEBUG:
    INSTALLED_APPS.append('django_extensions')

CELERY_ALWAYS_EAGER = True
CELERYD_TASK_TIME_LIMIT = 60 * 60  # 60 minutes
CELERY_SEND_TASK_ERROR_EMAILS = False
CELERYD_HIJACK_ROOT_LOGGER = False
# Don't queue a bunch of tasks in the workers
CELERYD_PREFETCH_MULTIPLIER = 1
CELERY_CREATE_MISSING_QUEUES = True

CELERY_DEFAULT_QUEUE = 'celery'
CELERY_QUEUES = (
    Queue('celery', Exchange('celery'), routing_key='celery'),
    Broadcast('build_broadcast_tasks'),
)

DEFAULT_FROM_EMAIL = "no-reply@readthedocs.org"
SERVER_EMAIL = DEFAULT_FROM_EMAIL
SESSION_COOKIE_DOMAIN = 'readthedocs.org'

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
    },
}

# Elasticsearch settings.
ES_HOSTS = ['127.0.0.1:9200']
ES_DEFAULT_NUM_REPLICAS = 0
ES_DEFAULT_NUM_SHARDS = 5

ALLOWED_HOSTS = ['*']

AUTH_PROFILE_MODULE = "core.UserProfile"
SOUTH_TESTS_MIGRATE = False

ABSOLUTE_URL_OVERRIDES = {
    'auth.user': lambda o: "/profiles/%s/" % o.username
}

INTERNAL_IPS = ('127.0.0.1',)

backup_count = 1000
maxBytes = 500 * 100 * 100
if LOG_DEBUG:
    backup_count = 2
    maxBytes = 500 * 100 * 10

# Guardian Settings
GUARDIAN_RAISE_403 = True
ANONYMOUS_USER_ID = -1

# Stripe
STRIPE_SECRET = None
STRIPE_PUBLISHABLE = None

# Maintenance
MAINTENANCE_IGNORE_URLS = (
    r'^/(?:static|media)/',
)

# RTD Settings
REPO_LOCK_SECONDS = 30
ALLOW_PRIVATE_REPOS = False

GLOBAL_ANALYTICS_CODE = 'UA-17997319-1'

GRAVATAR_DEFAULT_IMAGE = 'http://media.readthedocs.org/images/silhouette.png'

COPY_START_YEAR = 2010

LOG_FORMAT = "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s"

RESTRUCTUREDTEXT_FILTER_SETTINGS = {
    'cloak_email_addresses': True,
    'file_insertion_enabled': False,
    'raw_enabled': False,
    'strip_comments': True,
    'doctitle_xform': True,
    'sectsubtitle_xform': True,
    'initial_header_level': 2,
    'report_level': 5,
    'syntax_highlight': 'none',
    'math_output': 'latex',
    'field_name_limit': 50,
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': LOG_FORMAT,
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },
        'exceptionlog': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_ROOT, "exceptions.log"),
            'maxBytes': maxBytes,
            'backupCount': backup_count,
            'formatter': 'standard',
        },
        'errorlog': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_ROOT, "rtd.log"),
            'maxBytes': maxBytes,
            'backupCount': backup_count,
            'formatter': 'standard',
        },
        'postcommit': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_ROOT, "postcommit.log"),
            'maxBytes': maxBytes,
            'backupCount': backup_count,
            'formatter': 'standard',
        },
        'middleware': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_ROOT, "middleware.log"),
            'maxBytes': maxBytes,
            'backupCount': backup_count,
            'formatter': 'standard',
        },
        'restapi': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_ROOT, "api.log"),
            'maxBytes': maxBytes,
            'backupCount': backup_count,
            'formatter': 'standard',
        },
        'db': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_ROOT, "db.log"),
            'maxBytes': maxBytes,
            'backupCount': backup_count,
            'formatter': 'standard',
        },
        'search': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_ROOT, "search.log"),
            'maxBytes': maxBytes,
            'backupCount': backup_count,
            'formatter': 'standard',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'errorlog'],
            'propagate': True,
            'level': 'WARN',
        },
        'django.db.backends': {
            'handlers': ['db'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'core.views.post_commit': {
            'handlers': ['postcommit'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'core.middleware': {
            'handlers': ['middleware'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'restapi': {
            'handlers': ['restapi'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['exceptionlog'],
            'level': 'ERROR',
            'propagate': False,
        },
        'projects.views.public.search': {
            'handlers': ['search'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'search': {
            'handlers': ['search'],
            'level': 'DEBUG',
            'propagate': False,
        },
        # Uncomment if you want to see Elasticsearch queries in the console.
        #'elasticsearch.trace': {
        #    'level': 'DEBUG',
        #    'handlers': ['console'],
        #},

        # Default handler for everything that we're doing. Hopefully this
        # doesn't double-print the Django things as well. Not 100% sure how
        # logging works :)
        '': {
            'handlers': ['console', 'errorlog'],
            'level': 'INFO',
        },
    }
}

if DEBUG:
    LOGGING['handlers']['console']['level'] = 'DEBUG'
