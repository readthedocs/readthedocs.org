from readthedocs.notifications.library import NotificationSource


class BuildFailedNotification(NotificationSource):

    name = 'build_failure'
    subject = 'Your build for {{ build.id }} has failed'
    context_object_name = 'build'
