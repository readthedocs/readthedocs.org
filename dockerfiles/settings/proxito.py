from readthedocs.settings.proxito.base import CommunityProxitoSettingsMixin

from .docker_compose import DockerBaseSettings


class ProxitoDevSettings(CommunityProxitoSettingsMixin, DockerBaseSettings):
    DONT_HIT_DB = False

    # Disabled because of issues like
    # ResponseError: Error running script (call to f_1880dea5c524f6a37a650f715fa630416a2fe1fd):
    # @user_script:50: @user_script: 50: Wrong number of args calling Redis command From Lua script
    # (this issue goes away after a few reloads)
    CACHEOPS_ENABLED = False

    # El Proxito does not have django-debug-toolbar installed
    @property
    def DEBUG_TOOLBAR_CONFIG(self):
        return {
            "SHOW_TOOLBAR_CALLBACK": lambda request: False,
        }


ProxitoDevSettings.load_settings(__name__)
