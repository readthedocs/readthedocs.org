from .docker_compose import DockerBaseSettings


class CeleryDevSettings(DockerBaseSettings):
    pass

CeleryDevSettings.load_settings(__name__)
