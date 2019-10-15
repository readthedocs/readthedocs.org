from .docker import DockerBaseSettings


class BuildDevSettings(DockerBaseSettings):

    @property
    def DATABASES(self):  # noqa
        return {}

    DONT_HIT_DB = True

BuildDevSettings.load_settings(__name__)
