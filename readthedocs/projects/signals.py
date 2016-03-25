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

files_changed = django.dispatch.Signal(providing_args=["project", "files"])

log = logging.getLogger(__name__)


@receiver(project_import)
def handle_project_import(sender, **kwargs):
    """Add post-commit hook on project import"""
    project = sender
    request = kwargs.get('request')
    _set = False
    _service = None

    for service_cls in registry:
        if service_cls.is_project_service(project):
            for service in service_cls.for_user(request.user):
                _service = service
                if service.setup_webhook(project):
                    messages.success(request, _('Webhook activated'))
                    _set = True
                else:
                    messages.error(request, _('Webhook configuration failed'))
    if not _set and _service:
        messages.error(
            request,
            _('No accounts available to set webhook on. '
              'Please connect your %s account.' % _service.get_adapter()().get_provider().name)
        )
