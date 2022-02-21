from django.utils.translation import gettext_noop


class ReadTheDocsBaseException(Exception):
    message = None
    status_code = None

    def __init__(self, message=None, **kwargs):
        self.status_code = kwargs.pop(
            'status_code',
            None,
        ) or self.status_code or 1
        self.message = message or self.message or self.get_default_message()
        super().__init__(message, **kwargs)

    def get_default_message(self):
        return self.message


class AppUserError(ReadTheDocsBaseException):
    SOCIAL_CONNECTION_REVOKED = gettext_noop(
        'Our access to your following accounts was revoked: {providers}. '
        'Please, reconnect them from your social account connections.'
    )
