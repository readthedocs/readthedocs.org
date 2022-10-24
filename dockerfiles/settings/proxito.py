from readthedocs.settings.proxito.base import CommunityProxitoSettingsMixin

from .docker_compose import DockerBaseSettings


class ProxitoDevSettings(CommunityProxitoSettingsMixin, DockerBaseSettings):

    # El Proxito does not have django-debug-toolbar installed
    @property
    def DEBUG_TOOLBAR_CONFIG(self):
        return {
            'SHOW_TOOLBAR_CALLBACK': lambda request: False,
        }


ProxitoDevSettings.load_settings(__name__)
