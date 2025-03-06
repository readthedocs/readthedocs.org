from django.utils.translation import gettext_lazy as _


class NotificationBaseException(Exception):
    """
    The base exception class for notification and messages.

    This provides the additional ``message_id`` and ``format_values`` attributes
    that are used for message display and registry lookup.
    """

    default_message = _("Undefined error")

    def __init__(self, message_id, format_values=None, exception_message=None, **kwargs):
        self.message_id = message_id
        self.format_values = format_values
        super().__init__(exception_message or self.default_message, **kwargs)
