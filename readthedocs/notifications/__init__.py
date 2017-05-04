from __future__ import absolute_import, division, print_function

from .notification import Notification
from .backends import send_notification

default_app_config = 'readthedocs.notifications.apps.NotificationsAppConfig'
