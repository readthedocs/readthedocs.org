"""Extensions to Django messages to support notifications to users.

Notifications are important communications to users that need to be as visible
as possible. We support different backends to make notifications visible in
different ways. For example, they might be e-mailed to users as well as
displayed on the site.

This app builds on `django-messages-extends`_ to provide persistent messages
on the site.

.. _`django-messages-extends`: https://github.com
                               /AliLozano/django-messages-extends/

"""
from .notification import Notification
from .backends import send_notification

__all__ = (
    'Notification',
    'send_notification'
)


default_app_config = 'readthedocs.notifications.apps.NotificationsAppConfig'
