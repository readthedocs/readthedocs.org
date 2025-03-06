"""Filters used in our views."""

from django_filters import CharFilter
from django_filters import ChoiceFilter
from django_filters import DateFromToRangeFilter
from django_filters import FilterSet

from readthedocs.audit.models import AuditLog


class UserSecurityLogFilter(FilterSet):
    """Filter for user security logs."""

    allowed_actions = [
        (AuditLog.AUTHN, AuditLog.AUTHN_TEXT),
        (AuditLog.AUTHN_FAILURE, AuditLog.AUTHN_FAILURE_TEXT),
        (AuditLog.LOGOUT, AuditLog.LOGOUT_TEXT),
        (AuditLog.INVITATION_SENT, AuditLog.INVITATION_SENT_TEXT),
        (AuditLog.INVITATION_REVOKED, AuditLog.INVITATION_REVOKED_TEXT),
        (AuditLog.INVITATION_ACCEPTED, AuditLog.INVITATION_ACCEPTED_TEXT),
        (AuditLog.INVITATION_DECLINED, AuditLog.INVITATION_DECLINED_TEXT),
    ]

    ip = CharFilter(field_name="ip", lookup_expr="exact")
    project = CharFilter(field_name="log_project_slug", lookup_expr="exact")
    action = ChoiceFilter(
        field_name="action",
        lookup_expr="exact",
        # Choices are filled at runtime,
        # using the list from `allowed_actions`.
        choices=[],
    )
    date = DateFromToRangeFilter(field_name="created")

    class Meta:
        model = AuditLog
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters["action"].field.choices = self.allowed_actions


class OrganizationSecurityLogFilter(UserSecurityLogFilter):
    """Filter for organization security logs."""

    allowed_actions = [
        (AuditLog.AUTHN, AuditLog.AUTHN_TEXT),
        (AuditLog.AUTHN_FAILURE, AuditLog.AUTHN_FAILURE_TEXT),
        (AuditLog.LOGOUT, AuditLog.LOGOUT_TEXT),
        (AuditLog.INVITATION_SENT, AuditLog.INVITATION_SENT_TEXT),
        (AuditLog.INVITATION_REVOKED, AuditLog.INVITATION_REVOKED_TEXT),
        (AuditLog.INVITATION_ACCEPTED, AuditLog.INVITATION_ACCEPTED_TEXT),
        # NOTE: We don't allow organization owners to see information about declined
        # invitations, since those users aren't part of the organization yet.
        # (AuditLog.INVITATION_DECLINED, AuditLog.INVITATION_DECLINED_TEXT),
        (AuditLog.PAGEVIEW, AuditLog.PAGEVIEW_TEXT),
        (AuditLog.DOWNLOAD, AuditLog.DOWNLOAD_TEXT),
    ]
    user = CharFilter(field_name="log_user_username", lookup_expr="exact")
