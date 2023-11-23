from django.utils.translation import gettext_noop as _

from .constants import ERROR, SOLID, TIP, WARNING


class Message:
    def __init__(self, header, body, type, icon=None, icon_style=SOLID):
        self.header = header
        self.body = body
        self.type = type  # (ERROR, WARNING, INFO, NOTE, TIP)
        self.icon = icon
        self.icon_style = icon_style  # (SOLID, DUOTONE)

    def get_display_icon(self):
        if self.icon:
            return self.icon

        if self.type == ERROR:
            return "fa-exclamation"
        if self.type == WARNING:
            return "fa-triangle-exclamation"


NOTIFICATION_MESSAGES = {
    "generic-with-build-id": Message(
        header=_("Unknown problem"),
        # Note the message receives the instance it's attached to
        # and could be use it to inject related data
        body=_(
            """
        There was a problem with Read the Docs while building your documentation.
        Please try again later.
        If this problem persists,
        report this error to us with your build id ({instance[pk]}).
    """
        ),
        type=ERROR,
    ),
    "build-os-required": Message(
        header=_("Invalid configuration"),
        body=_(
            """
        The configuration key "build.os" is required to build your documentation.
        <a href='https://docs.readthedocs.io/en/stable/config-file/v2.html#build-os'>Read more.</a>
    """
        ),
        type=ERROR,
    ),
    "cancelled-by-user": Message(
        header=_("User action"),
        body=_(
            """
        Build cancelled by the user.
    """
        ),
        type=ERROR,
    ),
    "os-ubuntu-18.04-deprecated": Message(
        header=_("Deprecated OS selected"),
        body=_(
            """
        Ubuntu 18.04 is deprecated and will be removed soon.
        Update your <code>.readthedocs.yaml</code> to use a newer image.
    """
        ),
        type=TIP,
    ),
}
