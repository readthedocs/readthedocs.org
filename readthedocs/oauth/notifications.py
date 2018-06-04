# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals

from readthedocs.notifications import Notification
from readthedocs.notifications.constants import HTML, WARNING


class PermissionRevokedNotification(Notification):

    name = 'permission_revoked'
    context_object_name = 'socialaccount'
    subject = 'OAuth permission revoked'

    # FIXME: we should use ERROR here, but at this moment the user will see the
    # notification on site but also will receive an email
    level = WARNING

    def get_template_names(self, backend_name, source_format=HTML):
        return 'oauth/notifications/{name}_{backend}.{source_format}'.format(
            name=self.name,
            backend=backend_name,
            source_format=source_format,
        )
