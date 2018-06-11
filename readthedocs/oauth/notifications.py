# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals

from readthedocs.notifications import Notification
from readthedocs.notifications.constants import HTML, WARNING, INFO


class AttachWebhookNotification(Notification):

    name = 'attach_webhook'
    context_object_name = 'socialaccount'
    subject_success = 'Attach webhook success'
    subject_fail = 'Attach webhook failed'

    def __init__(self, context_object, request, user, success, reason=None):
        self.success = success
        self.reason = reason
        if self.success:
            self.level = INFO
            self.subject = self.subject_success
        else:
            self.level = WARNING
            self.subject = self.subject_fail

        super(AttachWebhookNotification, self).__init__(context_object, request, user)

    def get_context_data(self):
        context = super(AttachWebhookNotification, self).get_context_data()
        context.update({'reason': self.reason})
        return context

    def get_template_names(self, backend_name, source_format=HTML):
        return 'oauth/notifications/{name}_{status}_{backend}.{source_format}'.format(
            name=self.name,
            status='success' if self.success else 'failed',
            backend=backend_name,
            source_format=source_format,
        )
