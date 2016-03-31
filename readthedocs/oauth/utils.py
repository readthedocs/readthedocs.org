import logging

from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from readthedocs.oauth.services import registry

log = logging.getLogger(__name__)


def attach_webhook(project, request=None):
    """Add post-commit hook on project import"""

    for service_cls in registry:
        if service_cls.is_project_service(project):
            service = service_cls
            break
    else:
        return None

    user_accounts = service.for_user(request.user)
    for account in user_accounts:
        success, resp = account.setup_webhook(project)
        if success:
            messages.success(request, _('Webhook activated'))
            project.has_valid_webhook = True
            project.save()
            break
    else:
        if user_accounts:
            messages.error(
                request,
                _('Webhook activation failed. Make sure you have permissions to set it.')
            )
        else:
            messages.error(
                request,
                _('No accounts available to set webhook on. '
                  'Please connect your {network} account.'.format(
                      network=service.adapter().get_provider().name
                  ))
            )
