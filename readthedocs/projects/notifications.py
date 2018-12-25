"""Project notifications"""

from __future__ import absolute_import

from django.conf import settings
from messages_extends.constants import ERROR_PERSISTENT
from django.utils.translation import ugettext_lazy as _

from readthedocs.notifications import Notification, SiteNotification
from readthedocs.notifications.constants import REQUIREMENT


class ResourceUsageNotification(Notification):

    name = 'resource_usage'
    context_object_name = 'project'
    subject = 'Builds for {{ project.name }} are using too many resources'
    level = REQUIREMENT


class AbandonedProjectNotification(SiteNotification):

    level = REQUIREMENT
    send_email = True
    failure_level = ERROR_PERSISTENT
    subject = 'Abandoned project {{ proj_name }}'
    failure_message = _(
        'Your project {{ proj_name }} is marked as abandoned. Update link '
        'for the project docs is <a href="{{ proj_url }}">{{ proj_url }}</a>.'
    )

    def get_context_data(self):
        context = super(AbandonedProjectNotification, self).get_context_data()
        project = self.extra_context.get('project')
        proj_url = '{base}{url}'.format(
            base=settings.PRODUCTION_DOMAIN,
            url=project.get_absolute_url()
        )
        context.update({
            'proj_name': project.name,
            'proj_url': proj_url
        })
        return context
