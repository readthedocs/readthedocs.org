from readthedocs.notifications.library import Notification
from readthedocs.notifications.constants import REQUIREMENT


class BuildFailedNotification(Notification):

    name = 'build_failure'
    subject = 'Your build for {{ build.id }} has failed'
    context_object_name = 'build'
    level = REQUIREMENT
