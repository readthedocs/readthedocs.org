"""Project signals"""

from __future__ import absolute_import
import django.dispatch
from django.dispatch import receiver

from readthedocs.oauth.utils import attach_webhook


before_vcs = django.dispatch.Signal(providing_args=["version"])
after_vcs = django.dispatch.Signal(providing_args=["version"])

before_build = django.dispatch.Signal(providing_args=["version"])
after_build = django.dispatch.Signal(providing_args=["version"])

project_import = django.dispatch.Signal(providing_args=["project"])


@receiver(project_import)
def handle_project_import(sender, **kwargs):
    """Add post-commit hook on project import"""
    project = sender
    request = kwargs.get('request')

    attach_webhook(project=project, request=request)
