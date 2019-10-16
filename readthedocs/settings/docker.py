import os

from .dev import CommunityDevSettings

class DockerBaseSettings(CommunityDevSettings):

    """Settings for local development with Docker"""

    RTD_DOCKER_ENABLE = True
    RTD_DOCKER_COMPOSE = True
    RTD_DOCKER_USER = f'{os.geteuid()}:{os.getegid()}'
    RTD_DOCKER_LIMITS = {'memory': '1g', 'time': 900}
    USE_SUBDOMAIN = True
    STATIC_URL = 'http://dev.readthedocs.io/devstoreaccount1/static/'

    PRODUCTION_DOMAIN = 'dev.readthedocs.io'
    PUBLIC_DOMAIN = 'dev.readthedocs.io'
    PUBLIC_API_URL = 'http://dev.readthedocs.io'
    SLUMBER_API_HOST = 'http://web:8000'

    MULTIPLE_APP_SERVERS = ['web']
    MULTIPLE_BUILD_SERVERS = ['build']

    # Enable auto syncing elasticsearch documents
    ELASTICSEARCH_DSL_AUTOSYNC = True
    ELASTICSEARCH_DSL = {
        'default': {
            'hosts': 'search:9200',
        },
    }

    RTD_CLEAN_AFTER_BUILD = True

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

    # Avoid syncing to the web servers
    FILE_SYNCER = "readthedocs.builds.syncers.NullSyncer"

    # https://github.com/Azure/Azurite/blob/master/README.md#default-storage-account
    AZURE_ACCOUNT_NAME = 'devstoreaccount1'
    AZURE_ACCOUNT_KEY = 'Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw=='
    AZURE_CONTAINER = 'static'
    AZURE_STATIC_STORAGE_CONTAINER = AZURE_CONTAINER
    AZURE_MEDIA_STORAGE_HOSTNAME = 'storage:10000'

    # We want to replace files for the same version built
    AZURE_OVERWRITE_FILES = True

    # Storage backend for build media artifacts (PDF, HTML, ePub, etc.)
    RTD_BUILD_MEDIA_STORAGE = 'readthedocsext.storage.azure_storage.AzureBuildMediaStorage'
    AZURE_STATIC_STORAGE_HOSTNAME = 'dev.readthedocs.io'

    # Storage for static files (those collected with `collectstatic`)
    STATICFILES_STORAGE = 'readthedocsext.storage.azure_storage.AzureStaticStorage'

    STATICFILES_DIRS = [
        os.path.join(CommunityDevSettings.SITE_ROOT, 'readthedocs', 'static'),
        os.path.join(CommunityDevSettings.SITE_ROOT, 'media'),
    ]
    AZURE_BUILD_STORAGE_CONTAINER = 'builds'
    BUILD_COLD_STORAGE_URL = 'http://storage:10000/builds'
    EXTERNAL_VERSION_URL = 'http://external-builds.dev.readthedocs.io'
    AZURE_EMULATED_MODE = True
    AZURE_CUSTOM_DOMAIN = 'storage:10000'
    AZURE_SSL = False
