"""Local setting for Proxito"""

# pylint: disable=missing-docstring

import os

from readthedocs.core.settings import Settings


class ProxitoDevSettings(Settings):

    DEBUG = False

    SECRET_KEY = 'replace-this-please'  # noqa
    ALLOWED_HOSTS = ['*']
    ROOT_URLCONF = 'readthedocs.proxito.urls'
    USE_SUBDOMAIN = True
    PUBLIC_DOMAIN = 'dev.readthedocs.io'
    PRODUCTION_DOMAIN = 'localhost:8000'

    SITE_ROOT = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    STATIC_ROOT = os.path.join(SITE_ROOT, 'static')
    STATIC_URL = '/static/'
    MEDIA_ROOT = os.path.join(SITE_ROOT, 'media/')

    # These are needed to import RTD models
    RTD_LATEST = 'latest'
    RTD_LATEST_VERBOSE_NAME = 'latest'
    RTD_STABLE = 'stable'
    RTD_STABLE_VERBOSE_NAME = 'stable'
    RTD_BUILD_MEDIA_STORAGE = 'readthedocs.builds.storage.BuildMediaFileSystemStorage'

    DOCKER_SOCKET = 'unix:///var/run/docker.sock'
    DOCKER_BUILD_IMAGES = None
    DOCKER_LIMITS = {'memory': '200m', 'time': 600}
    DOCKER_DEFAULT_IMAGE = 'readthedocs/build'
    DOCKER_VERSION = 'auto'
    DOCKER_DEFAULT_VERSION = 'latest'
    DOCKER_IMAGE = '{}:{}'.format(DOCKER_DEFAULT_IMAGE, DOCKER_DEFAULT_VERSION)
    DOCKER_IMAGE_SETTINGS = {}
    SLUMBER_API_HOST = ''
    SLUMBER_USERNAME = None
    SLUMBER_PASSWORD = None
    CLASS_OVERRIDES = {}
    DEFAULT_PRIVACY_LEVEL = 'public'
    DEFAULT_VERSION_PRIVACY_LEVEL = 'public'
    PUBLIC_DOMAIN_USES_HTTPS = False

    # @property
    # def DATABASES(self):  # noqa
    #     return {
    #         'default': {
    #             'ENGINE': 'django.db.backends.sqlite3',
    #             'NAME': os.path.join(self.SITE_ROOT, 'dev.db'),
    #         }
    #     }

    # Application classes
    @property
    def INSTALLED_APPS(self):  # noqa
        apps = [
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.staticfiles',
            'django.contrib.sites',
            'readthedocs.builds',
            'readthedocs.projects',
            'readthedocs.oauth',
            'allauth',
            'allauth.account',
            'allauth.socialaccount',
            'taggit',
        ]
        return apps

    MIDDLEWARE = (
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.security.SecurityMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'readthedocs.proxito.middleware.ProxitoMiddleware',
        'corsheaders.middleware.CorsMiddleware',
    )


ProxitoDevSettings.load_settings(__name__)

if not os.environ.get('DJANGO_SETTINGS_SKIP_LOCAL', False):
    try:
        # pylint: disable=unused-wildcard-import
        from .local_settings import *  # noqa
    except ImportError:
        pass
