from .docker_compose import DockerBaseSettings


class WebDevSettings(DockerBaseSettings):
    DONT_HIT_DB = False

WebDevSettings.load_settings(__name__)
