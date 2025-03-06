"""Audit models."""

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel

from readthedocs.acl.utils import get_auth_backend
from readthedocs.analytics.utils import get_client_ip


class AuditLogManager(models.Manager):
    """AuditLog manager."""

    def new(self, action, user=None, request=None, **kwargs):
        """
        Create an audit log for `action`.

        If user or request are given,
        other fields will be auto-populated from that information.
        """

        actions_requiring_user = (
            AuditLog.PAGEVIEW,
            AuditLog.DOWNLOAD,
            AuditLog.AUTHN,
            AuditLog.LOGOUT,
            AuditLog.INVITATION_SENT,
            AuditLog.INVITATION_ACCEPTED,
            AuditLog.INVITATION_REVOKED,
        )
        if action in actions_requiring_user and (not user or not request):
            raise TypeError(f"A user and a request are required for the {action} action.")
        if action in (AuditLog.PAGEVIEW, AuditLog.DOWNLOAD) and "project" not in kwargs:
            raise TypeError(f"A project is required for the {action} action.")

        # Don't save anonymous users.
        if user and user.is_anonymous:
            user = None

        if request:
            kwargs["ip"] = get_client_ip(request)
            kwargs["browser"] = request.headers.get("User-Agent")
            kwargs.setdefault("resource", request.path_info)
            kwargs.setdefault("auth_backend", get_auth_backend(request))

            # Fill the project from the request if available.
            # This is frequently on actions generated from a subdomain.
            unresolved_domain = getattr(request, "unresolved_domain", None)
            if "project" not in kwargs and unresolved_domain:
                kwargs["project"] = unresolved_domain.project

        return self.create(
            user=user,
            action=action,
            **kwargs,
        )


class AuditLog(TimeStampedModel):
    """
    Track user actions for audit purposes.

    A log can be attached to a user and/or project and organization.
    If the user, project or organization are deleted the log will be preserved,
    and the deleted user/project/organization can be accessed via the ``log_*`` attributes.
    """

    # pylint: disable=too-many-instance-attributes

    PAGEVIEW = "pageview"
    PAGEVIEW_TEXT = _("Page view")

    DOWNLOAD = "download"
    DOWNLOAD_TEXT = _("Download")

    AUTHN = "authentication"
    AUTHN_TEXT = _("Authentication")

    AUTHN_FAILURE = "authentication-failure"
    AUTHN_FAILURE_TEXT = _("Authentication failure")

    LOGOUT = "log-out"
    LOGOUT_TEXT = _("Log out")

    INVITATION_SENT = "invitation-sent"
    INVITATION_SENT_TEXT = _("Invitation sent")

    INVITATION_REVOKED = "invitation-revoked"
    INVITATION_REVOKED_TEXT = _("Invitation revoked")

    INVITATION_ACCEPTED = "invitation-accepted"
    INVITATION_ACCEPTED_TEXT = _("Invitation accepted")

    INVITATION_DECLINED = "invitation-declined"
    INVITATION_DECLINED_TEXT = _("Invitation declined")

    CHOICES = (
        (PAGEVIEW, PAGEVIEW_TEXT),
        (DOWNLOAD, DOWNLOAD_TEXT),
        (AUTHN, AUTHN_TEXT),
        (AUTHN_FAILURE, AUTHN_FAILURE_TEXT),
        (LOGOUT, LOGOUT_TEXT),
        (INVITATION_SENT, INVITATION_SENT_TEXT),
        (INVITATION_REVOKED, INVITATION_REVOKED_TEXT),
        (INVITATION_ACCEPTED, INVITATION_ACCEPTED_TEXT),
        (INVITATION_DECLINED, INVITATION_DECLINED_TEXT),
    )

    user = models.ForeignKey(
        User,
        verbose_name=_("User"),
        null=True,
        on_delete=models.SET_NULL,
        db_index=True,
    )
    # Extra information in case the user is deleted.
    log_user_id = models.IntegerField(
        _("User ID"),
        blank=True,
        null=True,
        db_index=True,
    )
    log_user_username = models.CharField(
        _("Username"),
        max_length=150,
        blank=True,
        null=True,
        db_index=True,
    )

    project = models.ForeignKey(
        "projects.Project",
        verbose_name=_("Project"),
        null=True,
        db_index=True,
        on_delete=models.SET_NULL,
    )
    # Extra information in case the project is deleted.
    log_project_id = models.IntegerField(
        _("Project ID"),
        blank=True,
        null=True,
        db_index=True,
    )
    log_project_slug = models.CharField(
        _("Project slug"),
        max_length=63,
        blank=True,
        null=True,
        db_index=True,
    )

    organization = models.ForeignKey(
        "organizations.Organization",
        verbose_name=_("Organization"),
        null=True,
        db_index=True,
        on_delete=models.SET_NULL,
    )
    log_organization_id = models.IntegerField(
        _("Organization ID"),
        blank=True,
        null=True,
        db_index=True,
    )
    log_organization_slug = models.CharField(
        _("Organization slug"),
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
    )

    action = models.CharField(
        _("Action"),
        max_length=150,
        choices=CHOICES,
    )
    auth_backend = models.CharField(
        _("Auth backend"),
        max_length=250,
        blank=True,
        null=True,
    )
    ip = models.CharField(
        _("IP address"),
        blank=True,
        null=True,
        max_length=250,
    )
    browser = models.CharField(
        _("Browser user-agent"),
        max_length=250,
        blank=True,
        null=True,
    )
    # Resource can be a path,
    # set it slightly greater than ``HTMLFile.path``.
    resource = models.CharField(
        _("Resource"),
        max_length=5500,
        blank=True,
        null=True,
    )
    data = models.JSONField(
        null=True,
        blank=True,
        help_text=_(
            "Extra data about the log entry. Its structure depends on the type of log entry."
        ),
    )

    objects = AuditLogManager()

    class Meta:
        ordering = ["-created"]

    def save(self, **kwargs):
        if self.user:
            self.log_user_id = self.user.id
            self.log_user_username = self.user.username
        if self.project:
            self.log_project_id = self.project.id
            self.log_project_slug = self.project.slug
            organization = self.project.organizations.first()
            if organization:
                self.organization = organization
        if self.organization:
            self.log_organization_id = self.organization.id
            self.log_organization_slug = self.organization.slug

        self._truncate_browser()

        super().save(**kwargs)

    def _truncate_browser(self):
        browser_max_length = self._meta.get_field("browser").max_length
        if self.browser and len(self.browser) > browser_max_length:
            suffix = " - Truncated"
            truncated_at = browser_max_length - len(suffix)
            self.browser = self.browser[:truncated_at] + suffix

    def auth_backend_display(self):
        """
        Get a string representation for backends that aren't part of the normal login.

        .. note::

           The backends listed here are implemented on .com only.
        """
        backend = self.auth_backend or ""
        backend_displays = {
            "TemporaryAccessTokenBackend": _("shared link"),
            "TemporaryAccessPasswordBackend": _("shared password"),
        }
        for name, display in backend_displays.items():
            if name in backend:
                return display
        return ""

    def __str__(self):
        return self.action
