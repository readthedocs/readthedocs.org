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
    # With `None` the browser redirects infinitely.
    SESSION_COOKIE_SAMESITE = "Lax"


ProxitoDevSettings.load_settings(__name__)
