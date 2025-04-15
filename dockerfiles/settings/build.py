from .docker_compose import DockerBaseSettings


class BuildDevSettings(DockerBaseSettings):
    @property
    def DATABASES(self):  # noqa
        return {}

    DONT_HIT_DB = True
    SHOW_DEBUG_TOOLBAR = False
    # The secret key is not needed from the builders.
    # If you get an error about it missing, you may be doing
    # something that shouldn't be done from the builders.
    SECRET_KEY = None

BuildDevSettings.load_settings(__name__)
