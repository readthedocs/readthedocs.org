"""Project app config."""

import socket

from django.apps import AppConfig
from django.conf import settings
from django.core.checks.registry import registry


class ProjectsConfig(AppConfig):
    name = "readthedocs.projects"

    def ready(self):
        # Load and register notification messages for this application
        import readthedocs.projects.notifications  # noqa
        import readthedocs.projects.signals  # noqa
        import readthedocs.projects.tasks.builds  # noqa
        import readthedocs.projects.tasks.search  # noqa
        import readthedocs.projects.tasks.utils  # noqa

        # HACK: remove djstripe initial checks.
        # It performs checks that require access to the database, which make the builders to fail.
        # Note this is placed in the `projects` app, since it's listed after `djstripe` in `INSTALLED_APPS`, as this code has to be executed _after_ djstripe has been initialized.
        #
        # https://github.com/dj-stripe/dj-stripe/blob/8e536409b815b2a393ef1ba8eac3d27bd69a5664/djstripe/checks.py#L20
        if settings.DEBUG or socket.gethostname().startswith("build-"):
            registry.registered_checks = {
                item for item in registry.registered_checks if "djstripe" not in item.tags
            }
