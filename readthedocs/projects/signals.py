"""Project signals"""

from __future__ import absolute_import
import django.dispatch
from django.db.models.signals import pre_save
from django.dispatch import receiver

from readthedocs.oauth.utils import attach_webhook
from .models import HTMLFile

before_vcs = django.dispatch.Signal(providing_args=["version"])
after_vcs = django.dispatch.Signal(providing_args=["version"])

before_build = django.dispatch.Signal(providing_args=["version"])
after_build = django.dispatch.Signal(providing_args=["version"])

project_import = django.dispatch.Signal(providing_args=["project"])

files_changed = django.dispatch.Signal(providing_args=["project", "files"])


@receiver(project_import)
def handle_project_import(sender, **kwargs):
    """Add post-commit hook on project import"""
    project = sender
    request = kwargs.get('request')

    attach_webhook(project=project, request=request)


@receiver(pre_save, sender=HTMLFile)
def pre_save_html_file(sender, instance, *args, **kwargs):
    instance.is_html = True
