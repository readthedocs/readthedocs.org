from .docker_compose import DockerBaseSettings


class WebDevSettings(DockerBaseSettings):
    DONT_HIT_DB = False

    # Router is useful from webs only because they have access to the database.
    # Builders will use the same queue that was assigned the first time on retry
    CELERY_ROUTES = ("readthedocs.builds.tasks.TaskRouter",)


WebDevSettings.load_settings(__name__)
