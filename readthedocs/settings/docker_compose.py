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
    RTD_EXTERNAL_VERSION_DOMAIN = 'org.dev.readthedocs.build'

    STATIC_URL = '/devstoreaccount1/static/'

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

    # Enable auto syncing elasticsearch documents
    ELASTICSEARCH_DSL_AUTOSYNC = 'SEARCH' in os.environ

    RTD_CLEAN_AFTER_BUILD = True

    @property
    def LOGGING(self):
        logging = super().LOGGING
        logging['loggers'].update({
            # Disable azurite logging
            'azure.storage.common': {
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

    # https://github.com/Azure/Azurite/blob/master/README.md#default-storage-account
    AZURE_ACCOUNT_NAME = 'devstoreaccount1'
    AZURE_ACCOUNT_KEY = 'Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw=='
    AZURE_CONTAINER = 'static'
    AZURE_STATIC_STORAGE_CONTAINER = AZURE_CONTAINER

    # We want to replace files for the same version built
    AZURE_OVERWRITE_FILES = True

    # Storage backend for build media artifacts (PDF, HTML, ePub, etc.)
    RTD_BUILD_MEDIA_STORAGE = 'readthedocs.storage.azure_storage.AzureBuildMediaStorage'
    AZURE_STATIC_STORAGE_HOSTNAME = 'assets.community.dev.readthedocs.io:10000'

    RTD_SAVE_BUILD_COMMANDS_TO_STORAGE = True
    RTD_BUILD_COMMANDS_STORAGE = 'readthedocs.storage.azure_storage.AzureBuildStorage'

    # Storage backend for build cached environments
    RTD_BUILD_ENVIRONMENT_STORAGE = 'readthedocs.storage.azure_storage.AzureBuildEnvironmentStorage'

    # Storage for static files (those collected with `collectstatic`)
    STATICFILES_STORAGE = 'readthedocs.storage.azure_storage.AzureStaticStorage'

    STATICFILES_DIRS = [
        os.path.join(CommunityDevSettings.SITE_ROOT, 'readthedocs', 'static'),
        os.path.join(CommunityDevSettings.SITE_ROOT, 'media'),
    ]
    AZURE_BUILD_COMMANDS_STORAGE_CONTAINER = 'builds'
    BUILD_COLD_STORAGE_URL = 'http://storage:10000/builds'
    AZURE_EMULATED_MODE = True
    AZURE_CUSTOM_DOMAIN = 'storage:10000'
    AZURE_SSL = False

    # Remove the checks on the number of fields being submitted
    # This limit is mostly hit on large forms in the Django admin
    DATA_UPLOAD_MAX_NUMBER_FIELDS = None

    # This allows us to have CORS work well in dev
    CORS_ORIGIN_ALLOW_ALL = True
