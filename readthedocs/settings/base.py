# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import getpass
import os

from celery.schedules import crontab

from readthedocs.core.settings import Settings


try:
    import readthedocsext  # noqa
    ext = True
except ImportError:
    ext = False


_ = gettext = lambda s: s


class CommunityBaseSettings(Settings):

    """Community base settings, don't use this directly."""

    # Django settings
    SITE_ID = 1
    ROOT_URLCONF = 'readthedocs.urls'
    SUBDOMAIN_URLCONF = 'readthedocs.core.urls.subdomain'
    SINGLE_VERSION_URLCONF = 'readthedocs.core.urls.single_version'
    LOGIN_REDIRECT_URL = '/dashboard/'
    FORCE_WWW = False
    SECRET_KEY = 'replace-this-please'  # noqa
    ATOMIC_REQUESTS = True

    # Debug settings
    DEBUG = True

    # Domains and URLs
    PRODUCTION_DOMAIN = 'readthedocs.org'
    PUBLIC_DOMAIN = None
    PUBLIC_DOMAIN_USES_HTTPS = False
    USE_SUBDOMAIN = False
    PUBLIC_API_URL = 'https://{}'.format(PRODUCTION_DOMAIN)

    # Doc Builder Backends
    MKDOCS_BACKEND = 'readthedocs.doc_builder.backends.mkdocs'
    SPHINX_BACKEND = 'readthedocs.doc_builder.backends.sphinx'

    # slumber settings
    SLUMBER_API_HOST = 'https://readthedocs.org'
    SLUMBER_USERNAME = None
    SLUMBER_PASSWORD = None

    # Email
    DEFAULT_FROM_EMAIL = 'no-reply@readthedocs.org'
    SERVER_EMAIL = DEFAULT_FROM_EMAIL
    SUPPORT_EMAIL = None

    # Sessions
    SESSION_COOKIE_DOMAIN = 'readthedocs.org'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_AGE = 30 * 24 * 60 * 60  # 30 days
    SESSION_SAVE_EVERY_REQUEST = True

    # CSRF
    CSRF_COOKIE_HTTPONLY = True
    CSRF_COOKIE_AGE = 30 * 24 * 60 * 60

    # Read the Docs
    READ_THE_DOCS_EXTENSIONS = ext
    RTD_LATEST = 'latest'
    RTD_LATEST_VERBOSE_NAME = 'latest'
    RTD_STABLE = 'stable'
    RTD_STABLE_VERBOSE_NAME = 'stable'

    # Database and API hitting settings
    DONT_HIT_API = False
    DONT_HIT_DB = True

    SYNC_USER = getpass.getuser()

    USER_MATURITY_DAYS = 7

    # override classes
    CLASS_OVERRIDES = {}

    # Application classes
    @property
    def INSTALLED_APPS(self):  # noqa
        apps = [
            'django.contrib.auth',
            'django.contrib.admin',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',
            'django.contrib.staticfiles',
            'django.contrib.messages',
            'django.contrib.humanize',

            # third party apps
            'dj_pagination',
            'taggit',
            'guardian',
            'django_gravatar',
            'rest_framework',
            'corsheaders',
            'textclassifier',
            'annoying',
            'django_extensions',
            'crispy_forms',
            'messages_extends',
            'django_filters',
            'django_elasticsearch_dsl',

            # our apps
            'readthedocs.projects',
            'readthedocs.builds',
            'readthedocs.core',
            'readthedocs.doc_builder',
            'readthedocs.oauth',
            'readthedocs.redirects',
            'readthedocs.rtd_tests',
            'readthedocs.restapi',
            'readthedocs.gold',
            'readthedocs.payments',
            'readthedocs.notifications',
            'readthedocs.integrations',
            'readthedocs.analytics',
            'readthedocs.sphinx_domains',
            'readthedocs.search',


            # allauth
            'allauth',
            'allauth.account',
            'allauth.socialaccount',
            'allauth.socialaccount.providers.github',
            'allauth.socialaccount.providers.gitlab',
            'allauth.socialaccount.providers.bitbucket',
            'allauth.socialaccount.providers.bitbucket_oauth2',
        ]
        if ext:
            apps.append('django_countries')
            apps.append('readthedocsext.donate')
            apps.append('readthedocsext.embed')
        return apps

    @property
    def USE_PROMOS(self):  # noqa
        return 'readthedocsext.donate' in self.INSTALLED_APPS

    MIDDLEWARE = (
        'readthedocs.core.middleware.ProxyMiddleware',
        'readthedocs.core.middleware.FooterNoSessionMiddleware',
        'django.middleware.locale.LocaleMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.security.SecurityMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'dj_pagination.middleware.PaginationMiddleware',
        'readthedocs.core.middleware.SubdomainMiddleware',
        'readthedocs.core.middleware.SingleVersionMiddleware',
        'corsheaders.middleware.CorsMiddleware',
    )

    AUTHENTICATION_BACKENDS = (
        # Needed to login by username in Django admin, regardless of `allauth`
        'django.contrib.auth.backends.ModelBackend',
        # `allauth` specific authentication methods, such as login by e-mail
        'allauth.account.auth_backends.AuthenticationBackend',
    )

    MESSAGE_STORAGE = 'readthedocs.notifications.storages.FallbackUniqueStorage'

    NOTIFICATION_BACKENDS = [
        'readthedocs.notifications.backends.EmailBackend',
        'readthedocs.notifications.backends.SiteBackend',
    ]

    # Paths
    SITE_ROOT = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    TEMPLATE_ROOT = os.path.join(SITE_ROOT, 'readthedocs', 'templates')
    DOCROOT = os.path.join(SITE_ROOT, 'user_builds')
    UPLOAD_ROOT = os.path.join(SITE_ROOT, 'user_uploads')
    CNAME_ROOT = os.path.join(SITE_ROOT, 'cnames')
    LOGS_ROOT = os.path.join(SITE_ROOT, 'logs')
    PRODUCTION_ROOT = os.path.join(SITE_ROOT, 'prod_artifacts')
    PRODUCTION_MEDIA_ARTIFACTS = os.path.join(PRODUCTION_ROOT, 'media')

    # Assets and media
    STATIC_ROOT = os.path.join(SITE_ROOT, 'static')
    STATIC_URL = '/static/'
    MEDIA_ROOT = os.path.join(SITE_ROOT, 'media/')
    MEDIA_URL = '/media/'
    ADMIN_MEDIA_PREFIX = '/media/admin/'
    STATICFILES_DIRS = [
        os.path.join(SITE_ROOT, 'readthedocs', 'static'),
        os.path.join(SITE_ROOT, 'media'),
    ]
    STATICFILES_FINDERS = [
        'readthedocs.core.static.SelectiveFileSystemFinder',
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    ]
    PYTHON_MEDIA = False

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [TEMPLATE_ROOT],
            'OPTIONS': {
                'debug': DEBUG,
                'context_processors': [
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                    'django.template.context_processors.debug',
                    'django.template.context_processors.i18n',
                    'django.template.context_processors.media',
                    'django.template.context_processors.request',
                    # Read the Docs processor
                    'readthedocs.core.context_processors.readthedocs_processor',
                ],
                'loaders': [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ],
            },
        },
    ]

    # Cache
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'PREFIX': 'docs',
        }
    }
    CACHE_MIDDLEWARE_SECONDS = 60
    GLOBAL_PIP_CACHE = False

    # I18n
    TIME_ZONE = 'UTC'
    USE_TZ = True
    LANGUAGE_CODE = 'en-us'
    LANGUAGES = (
        ('ca', gettext('Catalan')),
        ('en', gettext('English')),
        ('es', gettext('Spanish')),
        ('pt-br', gettext('Brazilian Portuguese')),
        ('nb', gettext('Norwegian Bokmål')),
        ('fr', gettext('French')),
        ('ru', gettext('Russian')),
        ('de', gettext('German')),
        ('gl', gettext('Galician')),
        ('vi', gettext('Vietnamese')),
        ('zh-cn', gettext('Simplified Chinese')),
        ('zh-tw', gettext('Traditional Chinese')),
        ('ja', gettext('Japanese')),
        ('uk', gettext('Ukrainian')),
        ('it', gettext('Italian')),
        ('ko', gettext('Korean')),
    )
    LOCALE_PATHS = [
        os.path.join(SITE_ROOT, 'readthedocs', 'locale'),
    ]
    USE_I18N = True
    USE_L10N = True

    # Celery
    CELERY_APP_NAME = 'readthedocs'
    CELERY_ALWAYS_EAGER = True
    CELERYD_TASK_TIME_LIMIT = 60 * 60  # 60 minutes
    CELERY_SEND_TASK_ERROR_EMAILS = False
    CELERYD_HIJACK_ROOT_LOGGER = False
    # Don't queue a bunch of tasks in the workers
    CELERYD_PREFETCH_MULTIPLIER = 1
    CELERY_CREATE_MISSING_QUEUES = True

    CELERY_DEFAULT_QUEUE = 'celery'
    CELERYBEAT_SCHEDULE = {
        # Ran every hour on minute 30
        'hourly-remove-orphan-symlinks': {
            'task': 'readthedocs.projects.tasks.broadcast_remove_orphan_symlinks',
            'schedule': crontab(minute=30),
            'options': {'queue': 'web'},
        },
        'quarter-finish-inactive-builds': {
            'task': 'readthedocs.projects.tasks.finish_inactive_builds',
            'schedule': crontab(minute='*/15'),
            'options': {'queue': 'web'},
        },
        'every-three-hour-clear-persistent-messages': {
            'task': 'readthedocs.core.tasks.clear_persistent_messages',
            'schedule': crontab(minute=0, hour='*/3'),
            'options': {'queue': 'web'},
        },
    }
    MULTIPLE_APP_SERVERS = [CELERY_DEFAULT_QUEUE]
    MULTIPLE_BUILD_SERVERS = [CELERY_DEFAULT_QUEUE]

    # Sentry
    SENTRY_CELERY_IGNORE_EXPECTED = True

    # Docker
    DOCKER_ENABLE = False
    DOCKER_SOCKET = 'unix:///var/run/docker.sock'
    # This settings has been deprecated in favor of DOCKER_IMAGE_SETTINGS
    DOCKER_BUILD_IMAGES = None
    DOCKER_LIMITS = {'memory': '200m', 'time': 600}
    DOCKER_DEFAULT_IMAGE = 'readthedocs/build'
    DOCKER_VERSION = 'auto'
    DOCKER_DEFAULT_VERSION = 'latest'
    DOCKER_IMAGE = '{}:{}'.format(DOCKER_DEFAULT_IMAGE, DOCKER_DEFAULT_VERSION)
    DOCKER_IMAGE_SETTINGS = {
        'readthedocs/build:1.0': {
            'python': {'supported_versions': [2, 2.7, 3, 3.4]},
        },
        'readthedocs/build:2.0': {
            'python': {'supported_versions': [2, 2.7, 3, 3.5]},
        },
        'readthedocs/build:3.0': {
            'python': {'supported_versions': [2, 2.7, 3, 3.3, 3.4, 3.5, 3.6]},
        },
        'readthedocs/build:4.0': {
            'python': {'supported_versions': [2, 2.7, 3, 3.5, 3.6, 3.7]},
        },
    }

    # Alias tagged via ``docker tag`` on the build servers
    DOCKER_IMAGE_SETTINGS.update({
        'readthedocs/build:stable': DOCKER_IMAGE_SETTINGS.get('readthedocs/build:3.0'),
        'readthedocs/build:latest': DOCKER_IMAGE_SETTINGS.get('readthedocs/build:4.0'),
    })

    # All auth
    ACCOUNT_ADAPTER = 'readthedocs.core.adapters.AccountAdapter'
    ACCOUNT_EMAIL_REQUIRED = True
    ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
    ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
    ACCOUNT_ACTIVATION_DAYS = 7
    SOCIALACCOUNT_AUTO_SIGNUP = False
    SOCIALACCOUNT_PROVIDERS = {
        'github': {
            'SCOPE': [
                'user:email',
                'read:org',
                'admin:repo_hook',
                'repo:status',
            ],
        },
        'gitlab': {
            'SCOPE': [
                'api',
                'read_user',
            ],
        },
    }

    # CORS
    CORS_ORIGIN_REGEX_WHITELIST = (
        r'^http://(.+)\.readthedocs\.io$',
        r'^https://(.+)\.readthedocs\.io$',
    )
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

    # RTD Settings
    REPO_LOCK_SECONDS = 30
    ALLOW_PRIVATE_REPOS = False
    DEFAULT_PRIVACY_LEVEL = 'public'
    DEFAULT_VERSION_PRIVACY_LEVEL = 'public'
    GROK_API_HOST = 'https://api.grokthedocs.com'
    SERVE_DOCS = ['public']
    ALLOW_ADMIN = True

    # Elasticsearch settings.
    ES_HOSTS = ['127.0.0.1:9200']
    ELASTICSEARCH_DSL = {
        'default': {
            'hosts': '127.0.0.1:9200'
        },
    }
    # Chunk size for elasticsearch reindex celery tasks
    ES_TASK_CHUNK_SIZE = 100

    ES_INDEXES = {
        'domain': {
            'name': 'domain_index',
            'settings': {'number_of_shards': 2,
                         'number_of_replicas': 0
                         }
        },
        'project': {
            'name': 'project_index',
            'settings': {'number_of_shards': 2,
                         'number_of_replicas': 0
                         }
        },
        'page': {
            'name': 'page_index',
            'settings': {
                'number_of_shards': 2,
                'number_of_replicas': 0,
                "index": {
                    "sort.field": ["project", "version"]
                }
            }
        },
    }

    # ANALYZER = 'analysis': {
    #     'analyzer': {
    #         'default_icu': {
    #             'type': 'custom',
    #             'tokenizer': 'icu_tokenizer',
    #             'filter': ['word_delimiter', 'icu_folding', 'icu_normalizer'],
    #         }
    #     }
    # }

    # Disable auto refresh for increasing index performance
    ELASTICSEARCH_DSL_AUTO_REFRESH = False

    ALLOWED_HOSTS = ['*']

    ABSOLUTE_URL_OVERRIDES = {
        'auth.user': lambda o: '/profiles/{}/'.format(o.username)
    }

    INTERNAL_IPS = ('127.0.0.1',)

    # Guardian Settings
    GUARDIAN_RAISE_403 = True

    # Stripe
    STRIPE_SECRET = None
    STRIPE_PUBLISHABLE = None

    # Do Not Track support
    DO_NOT_TRACK_ENABLED = False

    # Misc application settings
    GLOBAL_ANALYTICS_CODE = None
    DASHBOARD_ANALYTICS_CODE = None  # For the dashboard, not docs
    GRAVATAR_DEFAULT_IMAGE = 'https://assets.readthedocs.org/static/images/silhouette.png'  # NOQA
    OAUTH_AVATAR_USER_DEFAULT_URL = GRAVATAR_DEFAULT_IMAGE
    OAUTH_AVATAR_ORG_DEFAULT_URL = GRAVATAR_DEFAULT_IMAGE
    RESTRICTEDSESSIONS_AUTHED_ONLY = True
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
    REST_FRAMEWORK = {
        'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',),
        'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',  # NOQA
        'PAGE_SIZE': 10,
    }
    SILENCED_SYSTEM_CHECKS = ['fields.W342', 'guardian.W001']

    # Logging
    LOG_FORMAT = '%(name)s:%(lineno)s[%(process)d]: %(levelname)s %(message)s'
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'default': {
                'format': LOG_FORMAT,
                'datefmt': '%d/%b/%Y %H:%M:%S',
            },
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'default'
            },
            'debug': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(LOGS_ROOT, 'debug.log'),
                'formatter': 'default',
            },
            'null': {
                'class': 'logging.NullHandler',
            },
        },
        'loggers': {
            '': {  # root logger
                'handlers': ['debug', 'console'],
                # Always send from the root, handlers can filter levels
                'level': 'DEBUG',
            },
            'readthedocs': {
                'handlers': ['debug', 'console'],
                'level': 'DEBUG',
                # Don't double log at the root logger for these.
                'propagate': False,
            },
            'django.security.DisallowedHost': {
                'handlers': ['null'],
                'propagate': False,
            },
        },
    }
