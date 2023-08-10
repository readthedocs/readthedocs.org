from .docker_compose import DockerBaseSettings


class CeleryDevSettings(DockerBaseSettings):
    DONT_HIT_DB = False

    # TODO: review this since it may not be needed with MinIO (S3). For now,
    # this is still required, but the CORS issue may have disappeared in MinIO.

    # Since we can't properly set CORS on storage container
    # trying to fetch ``objects.inv`` from celery container fails because the
    # URL is like http://devthedocs.org/... and it should be
    # http://storage:9000/... This setting fixes that.
    # Once we can use CORS, we should define this setting in the
    # ``docker_compose.py`` file instead.
    S3_MEDIA_STORAGE_OVERRIDE_HOSTNAME = "storage:9000"


CeleryDevSettings.load_settings(__name__)
