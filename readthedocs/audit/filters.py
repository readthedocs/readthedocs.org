"""Filters used in our views."""

from django_filters import CharFilter, ChoiceFilter, DateFromToRangeFilter, FilterSet

from readthedocs.audit.models import AuditLog


class UserSecurityLogFilter(FilterSet):

    allowed_actions = [
        AuditLog.AUTHN,
        AuditLog.AUTHN_FAILURE,
        AuditLog.INVITATION_SENT,
        AuditLog.INVITATION_REVOKED,
        AuditLog.INVITATION_ACCEPTED,
        AuditLog.INVITATION_DECLINED,
    ]

    ip = CharFilter(field_name='ip', lookup_expr='exact')
    project = CharFilter(field_name='log_project_slug', lookup_expr='exact')
    action = ChoiceFilter(
        field_name='action',
        lookup_expr='exact',
        choices=[],
    )
    date = DateFromToRangeFilter(field_name='created')

    class Meta:
        model = AuditLog
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters["action"].field.choices = [
            (action.value, action.label) for action in self.allowed_actions
        ]


class OrganizationSecurityLogFilter(UserSecurityLogFilter):

    allowed_actions = [
        AuditLog.AUTHN,
        AuditLog.AUTHN_FAILURE,
        AuditLog.PAGEVIEW,
        AuditLog.DOWNLOAD,
        AuditLog.INVITATION_SENT,
        AuditLog.INVITATION_REVOKED,
        AuditLog.INVITATION_ACCEPTED,
    ]
    user = CharFilter(field_name='log_user_username', lookup_expr='exact')
