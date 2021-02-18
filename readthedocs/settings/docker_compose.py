import os
import socket

from .dev import CommunityDevSettings


class DockerBaseSettings(CommunityDevSettings):

    """Settings for local development with Docker"""

    DOCKER_ENABLE = True
    RTD_DOCKER_COMPOSE = True
    RTD_DOCKER_COMPOSE_VOLUME = 'community_build-user-builds'
    RTD_DOCKER_USER = f'{os.geteuid()}:{os.getegid()}'
    DOCKER_LIMITS = {'memory': '1g', 'time': 900}
    USE_SUBDOMAIN = True

    PRODUCTION_DOMAIN = 'community.dev.readthedocs.io'
    PUBLIC_DOMAIN = 'community.dev.readthedocs.io'
    PUBLIC_API_URL = f'http://{PRODUCTION_DOMAIN}'

    SLUMBER_API_HOST = 'http://web:8000'
    SLUMBER_USERNAME = 'admin'
    SLUMBER_PASSWORD = 'admin'

    RTD_EXTERNAL_VERSION_DOMAIN = 'org.dev.readthedocs.build'

    STATIC_URL = '/static/'

    # In the local docker environment, nginx should be trusted to set the host correctly
    USE_X_FORWARDED_HOST = True

    MULTIPLE_APP_SERVERS = ['web']
    MULTIPLE_BUILD_SERVERS = ['build']

    # https://docs.docker.com/engine/reference/commandline/run/#add-entries-to-container-hosts-file---add-host
    # export HOSTIP=`ip -4 addr show scope global dev wlp4s0 | grep inet | awk '{print \$2}' | cut -d / -f 1`
    HOSTIP = os.environ.get('HOSTIP')

    # If the host IP is not specified, try to get it from the socket address list
    _, __, ips = socket.gethostbyname_ex(socket.gethostname())
    if ips and not HOSTIP:
        HOSTIP = ips[0][:-1] + "1"

    # Turn this on to test ads
    USE_PROMOS = False
    ADSERVER_API_BASE = f'http://{HOSTIP}:5000'
    # Create a Token for an admin User and set it here.
    ADSERVER_API_KEY = None
    ADSERVER_API_TIMEOUT = 2  # seconds - Docker for Mac is very slow

    # New templates
    @property
    def RTD_EXT_THEME_DEV_SERVER_ENABLED(self):
        return os.environ.get('RTD_EXT_THEME_DEV_SERVER_ENABLED') is not None

    @property
    def RTD_EXT_THEME_DEV_SERVER(self):
        if self.RTD_EXT_THEME_DEV_SERVER_ENABLED:
            return "http://assets.community.dev.readthedocs.io:10001"

    # Enable auto syncing elasticsearch documents
    ELASTICSEARCH_DSL_AUTOSYNC = 'SEARCH' in os.environ

    RTD_CLEAN_AFTER_BUILD = True

    @property
    def LOGGING(self):
        logging = super().LOGGING
        logging['loggers'].update({
            # Disable S3 logging
            'boto3': {
                'handlers': ['null'],
                'propagate': False,
            },
            'botocore': {
                'handlers': ['null'],
                'propagate': False,
            },
            's3transfer': {
                'handlers': ['null'],
                'propagate': False,
            },
            # Disable Docker API logging
            'urllib3': {
                'handlers': ['null'],
                'propagate': False,
            },
            # Disable gitpython logging
            'git.cmd': {
                'handlers': ['null'],
                'propagate': False,
            },
        })
        return logging

    @property
    def DATABASES(self):  # noqa
        return {
            "default": {
                "ENGINE": "django.db.backends.postgresql_psycopg2",
                "NAME": "docs_db",
                "USER": os.environ.get("DB_USER", "docs_user"),
                "PASSWORD": os.environ.get("DB_PWD", "docs_pwd"),
                "HOST": os.environ.get("DB_HOST", "database"),
                "PORT": "",
            }
        }

    def show_debug_toolbar(request):
        from django.conf import settings
        return settings.DEBUG

    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': show_debug_toolbar,
    }

    ACCOUNT_EMAIL_VERIFICATION = "none"
    SESSION_COOKIE_DOMAIN = None
    CACHES = {
        'default': {
            'BACKEND': 'redis_cache.RedisCache',
            'LOCATION': 'cache:6379',
        }
    }

    BROKER_URL = "redis://cache:6379/0"
    CELERY_RESULT_BACKEND = "redis://cache:6379/0"
    CELERY_RESULT_SERIALIZER = "json"
    CELERY_ALWAYS_EAGER = False
    CELERY_TASK_IGNORE_RESULT = False

    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

    RTD_BUILD_MEDIA_STORAGE = 'readthedocs.storage.s3_storage.S3BuildMediaStorage'
    # Storage backend for build cached environments
    RTD_BUILD_ENVIRONMENT_STORAGE = 'readthedocs.storage.s3_storage.S3BuildEnvironmentStorage'
    # Storage for static files (those collected with `collectstatic`)
    STATICFILES_STORAGE = 'readthedocs.storage.s3_storage.S3StaticStorage'

    AWS_ACCESS_KEY_ID = 'admin'
    AWS_SECRET_ACCESS_KEY = 'password'
    S3_MEDIA_STORAGE_BUCKET = 'media'
    S3_BUILD_COMMANDS_STORAGE_BUCKET = 'builds'
    S3_BUILD_ENVIRONMENT_STORAGE_BUCKET = 'envs'
    S3_STATIC_STORAGE_BUCKET = 'static'
    S3_STATIC_STORAGE_OVERRIDE_HOSTNAME = 'community.dev.readthedocs.io'
    S3_MEDIA_STORAGE_OVERRIDE_HOSTNAME = 'community.dev.readthedocs.io'

    AWS_AUTO_CREATE_BUCKET = True
    AWS_DEFAULT_ACL = 'public-read'
    AWS_BUCKET_ACL = 'public-read'
    AWS_S3_ENCRYPTION = False
    AWS_S3_SECURE_URLS = False
    AWS_S3_USE_SSL = False
    AWS_S3_ENDPOINT_URL = 'http://storage:9000/'
    AWS_QUERYSTRING_AUTH = False

    RTD_SAVE_BUILD_COMMANDS_TO_STORAGE = True
    RTD_BUILD_COMMANDS_STORAGE = 'readthedocs.storage.s3_storage.S3BuildCommandsStorage'
    BUILD_COLD_STORAGE_URL = 'http://storage:9000/builds'

    STATICFILES_DIRS = [
        os.path.join(CommunityDevSettings.SITE_ROOT, 'readthedocs', 'static'),
        os.path.join(CommunityDevSettings.SITE_ROOT, 'media'),
    ]

    # Remove the checks on the number of fields being submitted
    # This limit is mostly hit on large forms in the Django admin
    DATA_UPLOAD_MAX_NUMBER_FIELDS = None

    # This allows us to have CORS work well in dev
    CORS_ORIGIN_ALLOW_ALL = True
