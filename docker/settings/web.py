from .docker_compose import DockerBaseSettings

class WebDevSettings(DockerBaseSettings):

    # Needed to serve 404 pages properly
    # NOTE: it may introduce some strange behavior
    DEBUG = False

WebDevSettings.load_settings(__name__)
