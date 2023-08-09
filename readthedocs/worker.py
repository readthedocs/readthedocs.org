"""Celery worker application instantiation."""

import os

from celery import Celery
from django.conf import settings
from django_structlog.celery.steps import DjangoStructLogInitStep


def create_application():
    """Create a Celery application using Django settings."""
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        "readthedocs.settings.docker_compose",
    )

    application = Celery(settings.CELERY_APP_NAME)
    application.config_from_object("django.conf:settings")
    application.autodiscover_tasks(None)

    # A step to initialize django-structlog
    application.steps["worker"].add(DjangoStructLogInitStep)

    return application


def register_renamed_tasks(application, renamed_tasks):
    """
    Register renamed tasks into Celery registry.

    When a task is renamed (changing the function's name or moving it to a
    different module) and there are old instances running in production, they
    will trigger tasks using the old name. However, the new instances won't
    have those tasks registered.

    This function re-register the new tasks under the old name to workaround
    this problem. New instances will then executed the code for the new task,
    but when called under the old name.

    This function *must be called after renamed tasks with new names were
    already registered/load by Celery*.

    When using this function, think about the order the ASG will be deployed.
    Deploying webs first will require some type of re-register and deploying
    builds may require a different one.

    A good way to test this locally is with a code similar to the following:

    In [1]: # Register a task with the old name
    In [2]: @app.task(name='readthedocs.projects.tasks.update_docs_task')
       ...: def mytask(*args, **kwargs):
       ...: return True
       ...:
    In [3]: # Trigger the task
    In [4]: mytask.apply_async([99], queue='build:default')
    In [5]: # Check it's executed by the worker with the new code


    :param application: Celery Application
    :param renamed_tasks: Mapping containing the old name of the task as its
                          and the new name as its value.
    :type renamed_tasks: dict
    :type application: celery.Celery
    :returns: Celery Application

    """

    for oldname, newname in renamed_tasks.items():
        application.tasks[oldname] = application.tasks[newname]

    return application


app = create_application()
