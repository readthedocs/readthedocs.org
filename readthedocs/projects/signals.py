"""Project signals"""

import logging

import django.dispatch
from django.contrib import messages
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from readthedocs.oauth.services import registry


before_vcs = django.dispatch.Signal(providing_args=["version"])
after_vcs = django.dispatch.Signal(providing_args=["version"])

before_build = django.dispatch.Signal(providing_args=["version"])
after_build = django.dispatch.Signal(providing_args=["version"])

project_import = django.dispatch.Signal(providing_args=["project"])


log = logging.getLogger(__name__)


@receiver(project_import)
def handle_project_import(sender, **kwargs):
    """Add post-commit hook on project import"""
    project = sender
    request = kwargs.get('request')

    for service_cls in registry:
        if service_cls.is_project_service(project):
            service = service_cls.for_user(request.user)
            if service is not None:
                if service.setup_webhook(project):
                    messages.success(request, _('Webhook activated'))
                else:
                    messages.error(request, _('Webhook configuration failed'))

