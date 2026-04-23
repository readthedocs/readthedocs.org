from readthedocs.settings.proxito.base import CommunityProxitoSettingsMixin

from .docker_compose import DockerBaseSettings


class ProxitoDevSettings(CommunityProxitoSettingsMixin, DockerBaseSettings):
    DONT_HIT_DB = False

    # El Proxito does not have django-debug-toolbar installed
    @property
    def DEBUG_TOOLBAR_CONFIG(self):
        return {
            "SHOW_TOOLBAR_CALLBACK": lambda request: False,
        }

    # Override the setting from base.py only in proxito.
    # Cookies with samesite=none are allowed over https only.
    # On development we use http, the cookie will be rejected
    # and produce an infinite redirect.
    SESSION_COOKIE_SAMESITE = "Lax"


ProxitoDevSettings.load_settings(__name__)
