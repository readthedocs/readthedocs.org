from .docker_compose import DockerBaseSettings


class WebDevSettings(DockerBaseSettings):
    pass


WebDevSettings.load_settings(__name__)
