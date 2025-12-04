# pylint: disable=missing-docstring

import os
import re
import socket
import subprocess

import structlog
from pathlib import Path
from celery.schedules import crontab
from corsheaders.defaults import default_headers
from django.conf.global_settings import PASSWORD_HASHERS

from readthedocs.builds import constants_docker
from readthedocs.core.logs import shared_processors
from readthedocs.core.settings import Settings

try:
    import readthedocsext.cdn  # noqa

    ext = True
except ImportError:
    ext = False

try:
    import readthedocsext.theme  # noqa

    ext_theme = True
except ImportError:
    ext_theme = False


_ = gettext = lambda s: s
log = structlog.get_logger(__name__)


class CommunityBaseSettings(Settings):
    """Community base settings, don't use this directly."""

    # Django settings
    SITE_ID = 1
    ROOT_URLCONF = "readthedocs.urls"
    LOGIN_REDIRECT_URL = "/dashboard/"
    FORCE_WWW = False
    SECRET_KEY = "replace-this-please"  # noqa
    ATOMIC_REQUESTS = True

    DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

    # Debug settings
    DEBUG = True
    RTD_FORCE_SHOW_DEBUG_TOOLBAR = False

    # Build FTD index for all versions
    RTD_FILETREEDIFF_ALL = False

    @property
    def DEBUG_TOOLBAR_CONFIG(self):
        def _show_debug_toolbar(request):
            return (
                request.environ.get("SERVER_NAME", None) != "testserver"
                and self.SHOW_DEBUG_TOOLBAR
            )

        return {
            "SHOW_TOOLBAR_CALLBACK": _show_debug_toolbar,
            "DISABLE_PANELS": [
                # Default ones
                "debug_toolbar.panels.profiling.ProfilingPanel",
                "debug_toolbar.panels.redirects.RedirectsPanel",
                # Custome ones
                # We are disabling these because they take a lot of time to execute in the new dashboard.
                # We make an intensive usage of the ``include`` template tag there.
                # It's a "known issue/bug" and there is no solution as far as we can tell.
                "debug_toolbar.panels.sql.SQLPanel",
                "debug_toolbar.panels.templates.TemplatesPanel",
            ],
        }

    @property
    def SHOW_DEBUG_TOOLBAR(self):
        """
        Show django-debug-toolbar on DEBUG or if it's forced by RTD_FORCE_SHOW_DEBUG_TOOLBAR.

        This will show the debug toolbar on:

          - Docker local instance
          - web-extra production instance
        """
        return self.DEBUG or self.RTD_FORCE_SHOW_DEBUG_TOOLBAR

    # Domains and URLs
    RTD_IS_PRODUCTION = False
    PRODUCTION_DOMAIN = "readthedocs.org"
    PUBLIC_DOMAIN = None
    PUBLIC_DOMAIN_USES_HTTPS = False
    PUBLIC_API_URL = "https://{}".format(PRODUCTION_DOMAIN)
    RTD_INTERSPHINX_URL = "https://{}".format(PRODUCTION_DOMAIN)
    RTD_EXTERNAL_VERSION_DOMAIN = "external-builds.readthedocs.io"

    @property
    def RTD_RESTRICTED_DOMAINS(self):
        """
        Domains that are restricted for users to use as custom domains.

        This is to avoid users hijacking our domains.
        We return the last two parts of our public domains to cover all subdomains,
        e.g, if our domain is "app.readthedocs.org", we restrict all subdomains from "readthedocs.org".

        If your domain is like "readthedocs.co.uk", you might want to override this property.

        We recommend disallowing:

        - Dashboard domain
        - Public domain (from where documentation pages are served)
        - External version domain (from where PR previews are served)
        - Any public domains that point to the validation record (e.g., CNAME to readthedocs.io)
        """
        domains = [
            self.PRODUCTION_DOMAIN,
            self.PUBLIC_DOMAIN,
            self.RTD_EXTERNAL_VERSION_DOMAIN,
            "rtfd.io",
            "rtfd.org",
        ]
        return [
            ".".join(domain.split(".")[-2:])
            for domain in domains
        ]

    # Doc Builder Backends
    MKDOCS_BACKEND = "readthedocs.doc_builder.backends.mkdocs"
    SPHINX_BACKEND = "readthedocs.doc_builder.backends.sphinx"

    # slumber settings
    SLUMBER_API_HOST = "https://readthedocs.org"

    # Email
    DEFAULT_FROM_EMAIL = "no-reply@readthedocs.org"
    SERVER_EMAIL = DEFAULT_FROM_EMAIL
    SUPPORT_EMAIL = None
    SUPPORT_FORM_ENDPOINT = None

    # Sessions
    SESSION_COOKIE_DOMAIN = "readthedocs.org"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_AGE = 30 * 24 * 60 * 60  # 30 days
    SESSION_SAVE_EVERY_REQUEST = False
    SESSION_COOKIE_SAMESITE = "Lax"

    # CSRF
    CSRF_COOKIE_HTTPONLY = True
    CSRF_COOKIE_AGE = 30 * 24 * 60 * 60  # 30 days

    # Security & X-Frame-Options Middleware
    # https://docs.djangoproject.com/en/1.11/ref/middleware/#django.middleware.security.SecurityMiddleware
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
    X_FRAME_OPTIONS = "DENY"

    # Pagination
    # Only show 1 page on either side of the current page
    PAGINATION_DEFAULT_WINDOW = 1
    # Only show 1 page at the beginning and end 
    PAGINATION_DEFAULT_MARGIN = 1

    # Read the Docs
    READ_THE_DOCS_EXTENSIONS = ext
    RTD_LATEST = "latest"
    RTD_LATEST_VERBOSE_NAME = "latest"
    RTD_STABLE = "stable"
    RTD_STABLE_VERBOSE_NAME = "stable"
    RTD_CLEAN_AFTER_BUILD = False
    RTD_BUILD_HEALTHCHECK_TIMEOUT = 60 # seconds
    RTD_BUILD_HEALTHCHECK_DELAY = 15 # seconds
    RTD_MAX_CONCURRENT_BUILDS = 4
    RTD_BUILDS_MAX_RETRIES = 25
    RTD_BUILDS_RETRY_DELAY = 5 * 60  # seconds
    RTD_BUILD_STATUS_API_NAME = "docs/readthedocs"
    RTD_ANALYTICS_DEFAULT_RETENTION_DAYS = 30 * 3
    RTD_AUDITLOGS_DEFAULT_RETENTION_DAYS = 30 * 3

    # Number of days the validation process for a domain will be retried.
    RTD_CUSTOM_DOMAINS_VALIDATION_PERIOD = 30

    # Keep BuildData models on database during this time
    RTD_TELEMETRY_DATA_RETENTION_DAYS = 30 * 6  # 180 days / 6 months

    # Number of days an invitation is valid.
    RTD_INVITATIONS_EXPIRATION_DAYS = 15

    RTD_ENFORCE_BROWNOUTS_FOR_DEPRECATIONS = False

    @property
    def RTD_DEFAULT_FEATURES(self):
        # Features listed here will be available to users that don't have a
        # subscription or if their subscription doesn't include the feature.
        # Depending on the feature type, the numeric value represents a
        # number of days or limit of the feature.
        from readthedocs.subscriptions import constants
        from readthedocs.subscriptions.products import RTDProductFeature

        return dict(
            (
                # Max number of domains allowed per project.
                RTDProductFeature(type=constants.TYPE_CNAME, value=2).to_item(),
                RTDProductFeature(type=constants.TYPE_EMBED_API).to_item(),
                # Retention days for search analytics.
                RTDProductFeature(
                    type=constants.TYPE_SEARCH_ANALYTICS,
                    value=self.RTD_ANALYTICS_DEFAULT_RETENTION_DAYS,
                ).to_item(),
                # Retention days for page view analytics.
                RTDProductFeature(
                    type=constants.TYPE_PAGEVIEW_ANALYTICS,
                    value=self.RTD_ANALYTICS_DEFAULT_RETENTION_DAYS,
                ).to_item(),
                # Retention days for audit logs.
                RTDProductFeature(
                    type=constants.TYPE_AUDIT_LOGS,
                    value=self.RTD_AUDITLOGS_DEFAULT_RETENTION_DAYS,
                ).to_item(),
                # Max number of concurrent builds.
                RTDProductFeature(
                    type=constants.TYPE_CONCURRENT_BUILDS,
                    value=self.RTD_MAX_CONCURRENT_BUILDS,
                ).to_item(),
                # Max number of redirects allowed per project.
                RTDProductFeature(
                    type=constants.TYPE_REDIRECTS_LIMIT, value=100
                ).to_item(),
            )
        )

    # A dictionary of Stripe products mapped to a RTDProduct object.
    # In .org we don't have subscriptions/products, default features are
    # defined in RTD_DEFAULT_FEATURES.
    RTD_PRODUCTS = {}

    # Database and API hitting settings
    DONT_HIT_DB = True
    RTD_SAVE_BUILD_COMMANDS_TO_STORAGE = False
    DATABASE_ROUTERS = ["readthedocs.core.db.MapAppsRouter"]

    USER_MATURITY_DAYS = 7

    # override classes
    CLASS_OVERRIDES = {}

    DOC_PATH_PREFIX = "_/"

    RTD_EXT_THEME_DEV_SERVER = None

    # Application classes
    @property
    def INSTALLED_APPS(self):  # noqa
        apps = [
            "django.contrib.auth",
            "django.contrib.admin",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.sites",
            "django.contrib.messages",
            "django.contrib.humanize",
            # readthedocs.core app needs to be before
            # django.contrib.staticfiles to use our custom collectstatic
            # command
            "readthedocs.core",
            "django.contrib.staticfiles",
            # third party apps
            "dj_pagination",
            "taggit",
            "django_gravatar",
            "rest_framework",
            "rest_framework.authtoken",
            "rest_framework_api_key",
            "generic_relations",
            "corsheaders",
            "annoying",
            "django_extensions",
            "crispy_forms",
            "django_elasticsearch_dsl",
            "django_filters",
            "polymorphic",
            "simple_history",
            "djstripe",
            "django_celery_beat",
            "django_safemigrate.apps.SafeMigrateConfig",
            "django_structlog",
            # our apps
            "readthedocs.projects",
            "readthedocs.organizations",
            "readthedocs.builds",
            "readthedocs.doc_builder",
            "readthedocs.oauth",
            "readthedocs.redirects",
            "readthedocs.sso",
            "readthedocs.audit",
            "readthedocs.rtd_tests",
            "readthedocs.api.v2",
            "readthedocs.api.v3",
            "readthedocs.gold",
            "readthedocs.payments",
            "readthedocs.subscriptions",
            "readthedocs.notifications",
            "readthedocs.integrations",
            "readthedocs.analytics",
            "readthedocs.search",
            "readthedocs.embed",
            "readthedocs.telemetry",
            "readthedocs.domains",
            "readthedocs.invitations",
            # allauth
            "allauth",
            "allauth.account",
            "allauth.socialaccount",
            "allauth.socialaccount.providers.github",
            "readthedocs.allauth.providers.githubapp",
            "allauth.socialaccount.providers.gitlab",
            "allauth.socialaccount.providers.bitbucket_oauth2",
            "allauth.mfa",
            # Others
            # NOTE: impersonate functionality is only enabled when ALLOW_ADMIN is True,
            # but we still need to include it even when not enabled, since it has objects
            # related to the user model that Django needs to know about when deleting users.
            "impersonate",
        ]
        if ext:
            apps.append("readthedocsext.cdn")
            apps.append("readthedocsext.donate")
            apps.append("readthedocsext.spamfighting")
        if self.SHOW_DEBUG_TOOLBAR:
            apps.append("debug_toolbar")

        if ext_theme:
            apps.append("readthedocsext.theme")

        return apps

    @property
    def CRISPY_TEMPLATE_PACK(self):
        return "semantic-ui"

    @property
    def CRISPY_ALLOWED_TEMPLATE_PACKS(self):
        return ("semantic-ui",)

    @property
    def USE_PROMOS(self):  # noqa
        return "readthedocsext.donate" in self.INSTALLED_APPS

    @property
    def MIDDLEWARE(self):
        middlewares = [
            "readthedocs.core.middleware.NullCharactersMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.locale.LocaleMiddleware",
            "corsheaders.middleware.CorsMiddleware",
            "django.middleware.common.CommonMiddleware",
            "django.middleware.security.SecurityMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
            "django.middleware.clickjacking.XFrameOptionsMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
            "allauth.account.middleware.AccountMiddleware",
            "dj_pagination.middleware.PaginationMiddleware",
            "csp.middleware.CSPMiddleware",
            "readthedocs.core.middleware.UpdateCSPMiddleware",
            "simple_history.middleware.HistoryRequestMiddleware",
            "readthedocs.core.logs.ReadTheDocsRequestMiddleware",
            "django_structlog.middlewares.RequestMiddleware",
        ]
        if self.SHOW_DEBUG_TOOLBAR:
            middlewares.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
        if self.ALLOW_ADMIN:
            middlewares.append("impersonate.middleware.ImpersonateMiddleware")
        return middlewares

    AUTHENTICATION_BACKENDS = (
        # Needed to login by username in Django admin, regardless of `allauth`
        "django.contrib.auth.backends.ModelBackend",
        # `allauth` specific authentication methods, such as login by e-mail
        "allauth.account.auth_backends.AuthenticationBackend",
    )

    AUTH_PASSWORD_VALIDATORS = [
        {
            "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
            "OPTIONS": {
                "min_length": 9,
            },
        },
        {
            "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
        },
    ]

    # Explicitly set the password hashers to the default ones,
    # so we can change them in our test settings.
    PASSWORD_HASHERS = PASSWORD_HASHERS

    # Paths
    SITE_ROOT = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    TEMPLATE_ROOT = os.path.join(SITE_ROOT, "readthedocs", "templates")
    DOCROOT = os.path.join(SITE_ROOT, "user_builds")
    LOGS_ROOT = os.path.join(SITE_ROOT, "logs")
    PRODUCTION_ROOT = os.path.join(SITE_ROOT, "prod_artifacts")
    PRODUCTION_MEDIA_ARTIFACTS = os.path.join(PRODUCTION_ROOT, "media")

    # Assets and media
    STATIC_ROOT = os.path.join(SITE_ROOT, "static")
    STATIC_URL = "/static/"
    MEDIA_ROOT = os.path.join(SITE_ROOT, "media/")
    MEDIA_URL = "/media/"
    ADMIN_MEDIA_PREFIX = "/media/admin/"
    ADMIN_URL = "/admin"
    STATICFILES_DIRS = [
        os.path.join(SITE_ROOT, "media"),
    ]
    STATICFILES_FINDERS = [
        "readthedocs.core.static.SelectiveFileSystemFinder",
        "django.contrib.staticfiles.finders.AppDirectoriesFinder",
        "readthedocs.core.finders.DebugToolbarFinder",
    ]
    PYTHON_MEDIA = False

    # Content Security Policy
    # https://django-csp.readthedocs.io/
    CSP_FRAME_ANCESTORS = ("'none'",)
    CSP_REPORT_URI = None
    CSP_REPORT_ONLY = False

    # Default to disallow everything, and then allow specific sources on each directive.
    CSP_DEFAULT_SRC = ["'none'"]
    CSP_IMG_SRC = [
        "'self'",
        # Some of our styles include images as data URLs.
        "data:",
        # We load avatars from GitHub, GitLab, and Bitbucket,
        # and other services. They don't use a single specific domain,
        # so we just allow any https domain here.
        "https:",
    ]
    CSP_BASE_URI = ["'self'"]
    CSP_FRAME_SRC = [
        # Stripe (used for Gold subscriptions)
        "https://js.stripe.com/",
    ]
    RTD_CSP_UPDATE_HEADERS = {}

    @property
    def CSP_CONNECT_SRC(self):
        CSP_CONNECT_SRC = [
            "'self'",
            # Allow sentry to report errors.
            "https://*.ingest.us.sentry.io",
            # Allow fontawesome to load.
            "https://ka-p.fontawesome.com",
            "https://kit.fontawesome.com",
            # Plausible analytics
            "https://plausible.io/api/event",
        ]
        CSP_CONNECT_SRC.append(f"ws://{self.PRODUCTION_DOMAIN}:10001/ws")
        return CSP_CONNECT_SRC

    @property
    def CSP_SCRIPT_SRC(self):
        CSP_SCRIPT_SRC = [
            "'self'",
            # Some of our JS deps are using eval.
            "'unsafe-eval'",
            # Allow fontawesome to load.
            "https://kit.fontawesome.com",
            # Stripe (used for Gold subscriptions)
            "https://js.stripe.com/",
        ]
        CSP_SCRIPT_SRC.append(self.STATIC_URL)
        if self.RTD_EXT_THEME_DEV_SERVER:
            CSP_SCRIPT_SRC.append(self.RTD_EXT_THEME_DEV_SERVER)
        return CSP_SCRIPT_SRC

    @property
    def CSP_FONT_SRC(self):
        CSP_FONT_SRC = [
            "'self'",
            # Allow fontawesome to load.
            "data:",
            "https://ka-p.fontawesome.com",
        ]
        CSP_FONT_SRC.append(self.STATIC_URL)
        if self.RTD_EXT_THEME_DEV_SERVER:
            CSP_FONT_SRC.append(self.RTD_EXT_THEME_DEV_SERVER)
        return CSP_FONT_SRC

    @property
    def CSP_STYLE_SRC(self):
        CSP_STYLE_SRC = [
            "'self'",
            # We have lots of inline styles!
            # TODO: we should remove this.
            "'unsafe-inline'",
        ]
        CSP_STYLE_SRC.append(self.STATIC_URL)
        if self.RTD_EXT_THEME_DEV_SERVER:
            CSP_STYLE_SRC.append(self.RTD_EXT_THEME_DEV_SERVER)
        return CSP_STYLE_SRC

    @property
    def CSP_FORM_ACTION(self):
        CSP_FORM_ACTION = [
            "'self'",
            # Chrome and Safari block form submissions if it redirects to a different domain.
            # We redirect to external domains for some forms, like login.
            "https://github.com",
            "https://gitlab.com",
            "https://bitbucket.org",
            "https://id.atlassian.com",
            "https://accounts.google.com",
            # We also redirect to Stripe on subscription forms.
            "https://billing.stripe.com",
            "https://checkout.stripe.com",
        ]
        # Allow our support form to submit to external domains.
        if self.SUPPORT_FORM_ENDPOINT:
            CSP_FORM_ACTION.append(self.SUPPORT_FORM_ENDPOINT)
        return CSP_FORM_ACTION


    # Django Storage subclass used to write build artifacts to cloud or local storage
    # https://docs.readthedocs.io/page/development/settings.html#rtd-build-media-storage
    RTD_BUILD_MEDIA_STORAGE = "readthedocs.builds.storage.BuildMediaFileSystemStorage"
    RTD_BUILD_TOOLS_STORAGE = "readthedocs.builds.storage.BuildMediaFileSystemStorage"
    RTD_BUILD_COMMANDS_STORAGE = (
        "readthedocs.builds.storage.BuildMediaFileSystemStorage"
    )
    # This is for serving static files on proxito, not Django static files
    # https://github.com/readthedocs/readthedocs.org/pull/9237
    RTD_STATICFILES_STORAGE = "readthedocs.builds.storage.StaticFilesStorage"

    @property
    def TEMPLATES(self):
        dirs = [self.TEMPLATE_ROOT]

        if ext_theme:
            dirs.insert(
                0,
                os.path.join(
                    os.path.dirname(readthedocsext.theme.__file__),
                    "templates",
                ),
            )

        # Disable ``cached.Loader`` on development
        # https://docs.djangoproject.com/en/4.2/ref/templates/api/#django.template.loaders.cached.Loader
        default_loaders = [
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ]
        cached_loaders = [("django.template.loaders.cached.Loader", default_loaders)]

        return [
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "DIRS": dirs,
                "OPTIONS": {
                    "debug": self.DEBUG,
                    "loaders": default_loaders if self.DEBUG else cached_loaders,
                    "context_processors": [
                        "django.contrib.auth.context_processors.auth",
                        "django.contrib.messages.context_processors.messages",
                        "django.template.context_processors.debug",
                        "django.template.context_processors.i18n",
                        "django.template.context_processors.media",
                        "django.template.context_processors.request",
                        # Read the Docs processor
                        "readthedocs.core.context_processors.readthedocs_processor",
                        "readthedocs.core.context_processors.user_notifications",
                    ],
                },
            },
        ]

    # Cache
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "PREFIX": "docs",
        }
    }
    CACHE_MIDDLEWARE_SECONDS = 60

    # I18n
    TIME_ZONE = "UTC"
    USE_TZ = True
    LANGUAGE_CODE = "en-us"
    LANGUAGES = (
        ("ca", gettext("Catalan")),
        ("en", gettext("English")),
        ("es", gettext("Spanish")),
        ("pt-br", gettext("Brazilian Portuguese")),
        ("nb", gettext("Norwegian Bokmål")),
        ("fr", gettext("French")),
        ("ru", gettext("Russian")),
        ("de", gettext("German")),
        ("gl", gettext("Galician")),
        ("vi", gettext("Vietnamese")),
        ("zh-cn", gettext("Simplified Chinese")),
        ("zh-tw", gettext("Traditional Chinese")),
        ("ja", gettext("Japanese")),
        ("uk", gettext("Ukrainian")),
        ("it", gettext("Italian")),
        ("ko", gettext("Korean")),
    )
    LOCALE_PATHS = [
        os.path.join(SITE_ROOT, "readthedocs", "locale"),
    ]
    USE_I18N = True
    USE_L10N = True

    BUILD_TIME_LIMIT = 900  # seconds

    @property
    def BUILD_MEMORY_LIMIT(self):
        """
        Set build memory limit dynamically, if in production, based on system memory.

        We do this to avoid having separate build images. This assumes 1 build
        process per server, which will be allowed to consume all available
        memory.
        """
        # Our normal default
        default_memory_limit = "7g"

        # Only run on our servers
        if self.RTD_IS_PRODUCTION:
            total_memory, memory_limit = self._get_build_memory_limit()
            memory_limit = f"{memory_limit}m"
        else:
            memory_limit = default_memory_limit

        log.info(
            "Using dynamic build limits.",
            hostname=socket.gethostname(),
            memory=memory_limit,
        )
        return memory_limit


    # Celery
    CELERY_APP_NAME = "readthedocs"
    CELERY_ALWAYS_EAGER = True
    CELERYD_TASK_TIME_LIMIT = 60 * 60  # 60 minutes
    CELERY_SEND_TASK_ERROR_EMAILS = False
    CELERY_IGNORE_RESULT = True
    CELERYD_HIJACK_ROOT_LOGGER = False
    # This stops us from pre-fetching a task that then sits around on the builder
    CELERY_ACKS_LATE = True
    # Don't queue a bunch of tasks in the workers
    CELERYD_PREFETCH_MULTIPLIER = 1
    CELERY_CREATE_MISSING_QUEUES = True

    # https://github.com/readthedocs/readthedocs.org/issues/12317#issuecomment-3070950434
    # https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html#visibility-timeout
    BROKER_TRANSPORT_OPTIONS = {
        'visibility_timeout': 18000, # 5 hours
    }

    CELERY_DEFAULT_QUEUE = "celery"
    CELERYBEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
    CELERYBEAT_SCHEDULE = {
        "every-minute-finish-unhealthy-builds": {
            "task": "readthedocs.projects.tasks.utils.finish_unhealthy_builds",
            "schedule": crontab(minute="*"),
            "options": {"queue": "web"},
        },
        "every-day-delete-old-search-queries": {
            "task": "readthedocs.search.tasks.delete_old_search_queries_from_db",
            "schedule": crontab(minute=0, hour=0),
            "options": {"queue": "web"},
        },
        "every-day-delete-old-page-views": {
            "task": "readthedocs.analytics.tasks.delete_old_page_counts",
            "schedule": crontab(minute=27, hour="*/6"),
            "options": {"queue": "web"},
        },
        "every-day-delete-old-buildata-models": {
            "task": "readthedocs.telemetry.tasks.delete_old_build_data",
            "schedule": crontab(minute=0, hour=2),
            "options": {"queue": "web"},
        },
        "weekly-delete-old-personal-audit-logs": {
            "task": "readthedocs.audit.tasks.delete_old_personal_audit_logs",
            "schedule": crontab(day_of_week="wed", minute=0, hour=7),
            "options": {"queue": "web"},
        },
        "every-day-resync-repositories-from-sso-organizations": {
            "task": "readthedocs.oauth.tasks.sync_remote_repositories_from_sso_organizations",
            "schedule": crontab(minute=0, hour=4),
            "options": {"queue": "web"},
        },
        "quarter-archive-builds": {
            "task": "readthedocs.builds.tasks.archive_builds_task",
            "schedule": crontab(minute="*/15"),
            "options": {"queue": "web"},
            "kwargs": {
                "days": 1,
                "limit": 500,
                "delete": True,
            },
        },
        "every-30m-delete-inactive-external-versions": {
            "task": "readthedocs.builds.tasks.delete_closed_external_versions",
            # Increase the frequency because we have 255k closed versions and they keep growing.
            # It's better to increase this frequency than the `limit=` of the task.
            "schedule": crontab(minute="*/30", hour="*"),
            "options": {"queue": "web"},
        },
        "every-day-resync-remote-repositories": {
            "task": "readthedocs.oauth.tasks.sync_active_users_remote_repositories",
            "schedule": crontab(minute=30, hour=2),
            "options": {"queue": "web"},
        },
        "every-day-email-pending-custom-domains": {
            "task": "readthedocs.domains.tasks.email_pending_custom_domains",
            "schedule": crontab(minute=0, hour=3),
            "options": {"queue": "web"},
        },
        "every-15m-delete-pidbox-objects": {
            "task": "readthedocs.core.tasks.cleanup_pidbox_keys",
            "schedule": crontab(minute="*/15"),
            "options": {"queue": "web"},
        },
        "every-day-delete-old-revoked-build-api-keys": {
            "task": "readthedocs.api.v2.tasks.delete_old_revoked_build_api_keys",
            "schedule": crontab(minute=0, hour=4),
            "options": {"queue": "web"},
        },
    }

    # Sentry
    SENTRY_CELERY_IGNORE_EXPECTED = True

    DJANGO_STRUCTLOG_CELERY_ENABLED = True

    # Docker
    DOCKER_ENABLE = False
    DOCKER_SOCKET = "unix:///var/run/docker.sock"

    # User used to create the container.
    # In production we use the same user than the one defined by the
    # ``USER docs`` instruction inside the Dockerfile.
    # In development, we can use the "UID:GID" of the current user running the
    # instance to avoid file permissions issues.
    # https://docs.docker.com/engine/reference/run/#user
    RTD_DOCKER_USER = "docs:docs"
    RTD_DOCKER_SUPER_USER = "root:root"
    RTD_DOCKER_WORKDIR = "/home/docs/"

    RTD_DOCKER_COMPOSE = False

    DOCKER_VERSION = "auto"
    DOCKER_DEFAULT_VERSION = "ubuntu-22.04"
    DOCKER_IMAGE = "{}:{}".format(
        constants_docker.DOCKER_DEFAULT_IMAGE, DOCKER_DEFAULT_VERSION
    )

    # Additional binds for the build container
    RTD_DOCKER_ADDITIONAL_BINDS = {}
    RTD_DOCKER_BUILD_SETTINGS = constants_docker.RTD_DOCKER_BUILD_SETTINGS
    # This is used for the image used to clone the users repo,
    # since we can't read their config file image choice before cloning
    RTD_DOCKER_CLONE_IMAGE = RTD_DOCKER_BUILD_SETTINGS["os"]["ubuntu-22.04"]

    def _get_build_memory_limit(self):
        """
        Return the buld memory limit based on available system memory.

        We subtract ~1000Mb for overhead of processes and base system, and set
        the build time as proportional to the memory limit.
        """
        try:
            total_memory = int(
                subprocess.check_output(
                    "free -m | awk '/^Mem:/{print $2}'",
                    shell=True,
                )
            )
            return total_memory, round(total_memory - 1000, -2)
        except ValueError:
            # On systems without a `free` command it will return a string to
            # int and raise a ValueError
            log.exception("Failed to get memory size, using defaults Docker limits.")

    # Allauth
    ACCOUNT_ADAPTER = "readthedocs.core.adapters.AccountAdapter"
    SOCIALACCOUNT_ADAPTER = 'readthedocs.core.adapters.SocialAccountAdapter'
    ACCOUNT_SIGNUP_FIELDS = ['username*', 'email*', 'password1*', 'password2*']
    # By preventing enumeration, we will always send an email,
    # even if the email is not registered, that's hurting
    # our email reputation. We are okay with people knowing
    # if an email is registered or not.
    ACCOUNT_PREVENT_ENUMERATION = False

    # Make email verification mandatory.
    # Users won't be able to login until they verify the email address.
    ACCOUNT_EMAIL_VERIFICATION = "mandatory"
    ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True

    ACCOUNT_LOGIN_METHODS = ["username", "email"]
    ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 7
    SOCIALACCOUNT_AUTO_SIGNUP = False
    SOCIALACCOUNT_STORE_TOKENS = True

    _SOCIALACCOUNT_PROVIDERS = {
        "github": {
            "APPS": [
                {
                    "name": "GitHub OAuth",
                    "client_id": "123",
                    "secret": "456",
                    "key": "",
                    "settings": {
                        "hidden": False,
                        "hidden_on_login": False,
                        "hidden_on_connect": False,
                        "priority": 10,
                    },
                },
            ],
            "SCOPE": [
                "user:email",
                "read:org",
                "admin:repo_hook",
                "repo:status",
            ],
        },
        "githubapp": {
            "APPS": [
                {
                    "name": "GitHub App",
                    "client_id": "123",
                    "secret": "456",
                    "key": "",
                    "settings": {
                        "hidden": False,
                        "hidden_on_login": False,
                        "hidden_on_connect": False,
                        "priority": 20,
                    },
                },
            ],
            # Scope is determined by the GitHub App permissions.
            "SCOPE": [],
        },
        "gitlab": {
            "APPS": [
                {"client_id": "123", "secret": "456", "key": "", "settings": {"priority": 30}},
            ],
            # GitLab returns the primary email only, we can trust it's verified.
            "VERIFIED_EMAIL": True,
            "SCOPE": [
                "api",
                "read_user",
            ],
        },
        "bitbucket_oauth2": {
            "APPS": [
                {"client_id": "123", "secret": "456", "key": "", "settings": {"priority": 40}},
            ],
            # Bitbucket scope/permissions are determined by the Oauth consumer setup on bitbucket.org.
        },
    }

    @property
    def SOCIALACCOUNT_PROVIDERS(self):
        """
        This is useful to override in a subclass, mainly to add the secrets when deploying.

        Our ops repos have a complex (shared) inheritance structure, so it's easier this way.
        """
        return self._SOCIALACCOUNT_PROVIDERS

    ACCOUNT_FORMS = {
        "signup": "readthedocs.forms.SignupFormWithNewsletter",
    }

    GITHUB_APP_ID = 1234
    GITHUB_APP_NAME = "readthedocs"
    GITHUB_APP_PRIVATE_KEY = ""
    GITHUB_APP_WEBHOOK_SECRET = ""
    RTD_ALLOW_GITHUB_APP = True

    @property
    def GITHUB_APP_CLIENT_ID(self):
        return self.SOCIALACCOUNT_PROVIDERS["githubapp"]["APPS"][0]["client_id"]

    # CORS
    # Don't allow sending cookies in cross-domain requests, this is so we can
    # relax our CORS headers for more views, but at the same time not opening
    # users to CSRF attacks.
    CORS_ALLOW_CREDENTIALS = False

    # Allow cross-site requests from any origin,
    # all information from our allowed endpoits is public.
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOW_HEADERS = list(default_headers) + [
        "x-hoverxref-version",
    ]
    # Additional protection to allow only idempotent methods.
    CORS_ALLOW_METHODS = [
        "GET",
        "OPTIONS",
        "HEAD",
    ]

    # URLs to allow CORS to read from unauthed.
    CORS_URLS_REGEX = re.compile(
        r"""
        ^(
            /api/v2/search
            |/api/v2/docsearch
            |/api/v2/embed
            |/api/v3/embed
            |/api/v2/sustainability
        )
        """,
        re.VERBOSE,
    )

    # RTD Settings
    ALLOW_PRIVATE_REPOS = False
    DEFAULT_PRIVACY_LEVEL = "public"
    DEFAULT_VERSION_PRIVACY_LEVEL = "public"
    ALLOW_ADMIN = True

    # Organization settings
    RTD_ALLOW_ORGANIZATIONS = False
    RTD_ORG_DEFAULT_STRIPE_SUBSCRIPTION_PRICE = "trial-v2-monthly"
    RTD_ORG_TRIAL_PERIOD_DAYS = 30

    # Elasticsearch settings.
    ELASTICSEARCH_DSL = {
        "default": {
            "hosts": "http://elastic:password@search:9200",
        },
    }
    # Chunk size for elasticsearch reindex celery tasks
    ES_TASK_CHUNK_SIZE = 500

    # Info from Honza about this:
    # The key to determine shard number is actually usually not the node count,
    # but the size of your data.
    # There are advantages to just having a single shard in an index since
    # you don't have to do the distribute/collect steps when executing a search.
    # If your data will allow it (not significantly larger than 40GB)
    # I would recommend going to a single shard and one replica meaning
    # any of the two nodes will be able to serve any search without talking to the other one.
    # Scaling to more searches will then just mean adding a third node
    # and a second replica resulting in immediate 50% bump in max search throughput.

    ES_INDEXES = {
        "project": {
            "name": "project_index",
            "settings": {"number_of_shards": 1, "number_of_replicas": 1},
        },
        "page": {
            "name": "page_index",
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1,
            },
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

    ALLOWED_HOSTS = ["*"]

    ABSOLUTE_URL_OVERRIDES = {"auth.user": lambda o: "/profiles/{}/".format(o.username)}

    INTERNAL_IPS = ("127.0.0.1",)

    # django-impersonate.
    IMPERSONATE = {
        # By default, only staff users can impersonate.
        "REQUIRE_SUPERUSER": True,
    }

    # Taggit
    # https://django-taggit.readthedocs.io
    TAGGIT_TAGS_FROM_STRING = "readthedocs.projects.tag_utils.rtd_parse_tags"

    # DJStripe values -- **CHANGE THESE IN PRODUCTION**
    STRIPE_LIVE_MODE = False  # Change to True in production

    # These values shouldn't need to change..
    DJSTRIPE_FOREIGN_KEY_TO_FIELD = "id"
    DJSTRIPE_USE_NATIVE_JSONFIELD = (
        True  # We recommend setting to True for new installations
    )

    # Disable adding djstripe metadata to the Customer objects.
    # We are managing the subscriber relationship by ourselves,
    # since we have subscriptions attached to an organization or gold user
    # we can't make use of the DJSTRIPE_SUBSCRIBER_MODEL setting.
    DJSTRIPE_SUBSCRIBER_CUSTOMER_KEY = None

    # Webhook URL for BotDog to post messages in Slack #sales channel:
    # https://api.slack.com/apps/A01ML7J7N4T/incoming-webhooks
    SLACK_WEBHOOK_RTD_NOTIFICATIONS_CHANNEL = None  # https://hooks.slack.com/services/...

    # Do Not Track support
    DO_NOT_TRACK_ENABLED = False

    # Advertising configuration defaults
    ADSERVER_API_BASE = None
    ADSERVER_API_KEY = None
    ADSERVER_API_TIMEOUT = 0.35  # seconds

    # Misc application settings
    GLOBAL_ANALYTICS_CODE = None
    DASHBOARD_ANALYTICS_CODE = None  # For the dashboard, not docs
    GRAVATAR_DEFAULT_IMAGE = (
        "https://assets.readthedocs.org/static/images/silhouette.png"  # NOQA
    )
    OAUTH_AVATAR_USER_DEFAULT_URL = GRAVATAR_DEFAULT_IMAGE
    OAUTH_AVATAR_ORG_DEFAULT_URL = GRAVATAR_DEFAULT_IMAGE
    REST_FRAMEWORK = {
        "DEFAULT_FILTER_BACKENDS": (
            "django_filters.rest_framework.DjangoFilterBackend",
        ),
        "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",  # NOQA
        "DEFAULT_THROTTLE_RATES": {
            "anon": "5/minute",
            "user": "60/minute",
        },
        "PAGE_SIZE": 10,
        "TEST_REQUEST_DEFAULT_FORMAT": "json",
    }
    REST_FLEX_FIELDS = {
        "RECURSIVE_EXPANSION_PERMITTED": False,
    }

    SILENCED_SYSTEM_CHECKS = ["fields.W342"]

    # Logging
    LOG_FORMAT = "%(name)s:%(lineno)s[%(process)d]: %(levelname)s %(message)s"
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "default": {
                "format": LOG_FORMAT,
                "datefmt": "%d/%b/%Y %H:%M:%S",
            },
            # structlog
            "plain_console": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.dev.ConsoleRenderer(colors=False),
                ],
                # Allows to add extra data to log entries generated via ``logging`` module
                # See https://www.structlog.org/en/stable/standard-library.html#rendering-using-structlog-based-formatters-within-logging
                "foreign_pre_chain": shared_processors,
            },
            "colored_console": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.dev.ConsoleRenderer(colors=True),
                ],
                # Allows to add extra data to log entries generated via ``logging`` module
                # See https://www.structlog.org/en/stable/standard-library.html#rendering-using-structlog-based-formatters-within-logging
                "foreign_pre_chain": shared_processors,
            },
            "key_value": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.processors.KeyValueRenderer(
                        key_order=["timestamp", "level", "event", "logger"]
                    ),
                ],
                # Allows to add extra data to log entries generated via ``logging`` module
                # See https://www.structlog.org/en/stable/standard-library.html#rendering-using-structlog-based-formatters-within-logging
                "foreign_pre_chain": shared_processors,
            },
        },
        "handlers": {
            "console": {
                "level": "INFO",
                "class": "logging.StreamHandler",
                "formatter": "plain_console",
            },
            "debug": {
                "level": "DEBUG",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": os.path.join(LOGS_ROOT, "debug.log"),
                "formatter": "key_value",
            },
            "null": {
                "class": "logging.NullHandler",
            },
        },
        "loggers": {
            "": {  # root logger
                "handlers": ["debug", "console"],
                # Always send from the root, handlers can filter levels
                "level": "INFO",
            },
            "docker.utils.config": {
                "handlers": ["null"],
                # Don't double log at the root logger for these.
                "propagate": False,
            },
            "django_structlog.middlewares.request": {
                "handlers": ["null"],
                # Don't double log at the root logger for these.
                "propagate": False,
            },
            "readthedocs": {
                "handlers": ["debug", "console"],
                "level": "DEBUG",
                # Don't double log at the root logger for these.
                "propagate": False,
            },
            "django.security.DisallowedHost": {
                "handlers": ["null"],
                "propagate": False,
            },
            "django.security.DisallowedRedirect": {
                "handlers": ["null"],
                "propagate": False,
            },
            "elastic_transport.transport": {
                "handlers": ["null"],
                "propagate": False,
            },
            "celery.worker.consumer.gossip": {
                "handlers": ["null"],
                "propagate": False,
            },
        },
    }

    # MailerLite API for newsletter signups
    MAILERLITE_API_SUBSCRIBERS_URL = "https://api.mailerlite.com/api/v2/subscribers"
    MAILERLITE_API_ONBOARDING_GROUP_ID = None
    MAILERLITE_API_ONBOARDING_GROUP_URL = None
    MAILERLITE_API_KEY = None

    RTD_EMBED_API_EXTERNAL_DOMAINS = [
        r"^docs\.python\.org$",
        r"^docs\.scipy\.org$",
        r"^docs\.sympy\.org$",
        r"^numpy\.org$",
    ]
    RTD_EMBED_API_PAGE_CACHE_TIMEOUT = 5 * 10
    RTD_EMBED_API_DEFAULT_REQUEST_TIMEOUT = 1
    RTD_EMBED_API_DOMAIN_RATE_LIMIT = 50
    RTD_EMBED_API_DOMAIN_RATE_LIMIT_TIMEOUT = 60

    RTD_SPAM_THRESHOLD_DONT_SHOW_ADS = 100
    RTD_SPAM_THRESHOLD_DENY_ON_ROBOTS = 200
    RTD_SPAM_THRESHOLD_DONT_SHOW_DASHBOARD = 300
    RTD_SPAM_THRESHOLD_DONT_SERVE_DOCS = 500
    RTD_SPAM_THRESHOLD_REMOVE_FROM_SEARCH_INDEX = 500
    RTD_SPAM_THRESHOLD_DELETE_PROJECT = 1000
    RTD_SPAM_MAX_SCORE = 9999

    S3_PROVIDER = "AWS"
    # Used by readthedocs.aws.security_token_service.
    AWS_STS_ASSUME_ROLE_ARN = "arn:aws:iam::1234:role/SomeRole"

    @property
    def STORAGES(self):
        # https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html
        return {
            "staticfiles": {
                "BACKEND": "readthedocs.storage.s3_storage.S3StaticStorage"
            },
            "usercontent": {
                "BACKEND": "django.core.files.storage.FileSystemStorage",
                "OPTIONS": {
                    "location": Path(self.MEDIA_ROOT) / "usercontent",
                    "allow_overwrite": True,
                }
            },
        }

    @property
    def USING_AWS(self):
        """Return True if we are using AWS as our storage/cloud provider."""
        return self.S3_PROVIDER == "AWS"
