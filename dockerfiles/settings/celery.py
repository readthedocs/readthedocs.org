from .docker_compose import DockerBaseSettings


class CeleryDevSettings(DockerBaseSettings):
    # Since we can't properly set CORS on Azurite container
    # (see https://github.com/Azure/Azurite/issues/55#issuecomment-503380561)
    # trying to fetch ``objects.inv`` from celery container fails because the
    # URL is like http://community.dev.readthedocs.io/... and it should be
    # http://storage:10000/... This setting fixes that.
    # Once we can use CORS, we should define this setting in the
    # ``docker_compose.py`` file instead.
    AZURE_MEDIA_STORAGE_HOSTNAME = 'storage:10000'


CeleryDevSettings.load_settings(__name__)
