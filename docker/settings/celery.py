from .docker import DockerBaseSettings


class CeleryDevSettings(DockerBaseSettings):
    pass

CeleryDevSettings.load_settings(__name__)
