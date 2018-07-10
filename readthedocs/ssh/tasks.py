# -*- coding: utf-8 -*-
"""
Async tasks around SSH management.

Generation and upload/delete ssh deploy keys to VCS services.

.. note::

    This functionality is not enabled by default. Views and models from this
    application are not exposed to the user.
"""
from __future__ import division, print_function, unicode_literals

from django.contrib.auth.models import User

from readthedocs.oauth.services import registry
from readthedocs.projects.models import Project
from readthedocs.worker import app


from .models import SSHKey
from .notifications import DeployKeyAddedNotification, DeployKeyDeletedNotification


@app.task(queue='web')
def generate_project_ssh_pair_keys(project_pk):
    """
    Generate a SSHKey for the project.

    This task is used in ``trigger_initial_build`` to auto-generate the SSH key
    for this project.

    :param project_pk: pk of the Project

    :returns: None
    """
    project = Project.objects.get(pk=project_pk)
    SSHKey.objects.create(project=project)


@app.task(queue='web')
def connect_oauth_to_project(project_pk, user_pk=None):
    """Add ssh deploy key on project import"""
    project = Project.objects.get(pk=project_pk)
    _set = False
    _service = None
    user = None
    if user_pk is not None:
        user = User.objects.get(pk=user_pk)

    for service_cls in registry:
        for service in service_cls.for_project(project, user):
            _service = service
            if service.is_project_service(project):
                success = service.attach_project(project)
                if success:
                    _set = True
                    break

    if user and _service:
        _service.message_user(DeployKeyAddedNotification, user, _set)


# TODO: maybe it's not needed to be a task, but just following the pattern
@app.task(queue='web')
def disconnect_oauth_from_project(key_pk, user_pk=None):
    """Remove SSH deploy key from project service."""
    key = SSHKey.objects.get(pk=key_pk)
    _set = False
    _service = None
    user = None
    if user_pk is not None:
        user = User.objects.get(pk=user_pk)

    for service_cls in registry:
        for service in service_cls.for_project(key.project, user):
            _service = service
            if service.is_project_service(key.project):
                success = service.remove_key(key)
                if success:
                    _set = True
                    break

    if user and _service:
        _service.message_user(DeployKeyDeletedNotification, user, _set)
