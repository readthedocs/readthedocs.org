"""Filters used in our views."""

from django import forms
from django.utils.translation import ugettext_lazy as _
from django_filters import CharFilter, ChoiceFilter, FilterSet

from readthedocs.audit.models import AuditLog


class _UserSecurityLogForm(forms.ModelForm):

    """
    Form to be used in the filters.

    As we use an ``IPAddressField`` in our model,
    django will complaint if we try to use anything that isn't a valid IP.
    Using a form allows us to check for ``filter.is_valid()`` first.
    """

    class Meta:
        model = AuditLog
        fields = ['ip']


class UserSecurityLogFilter(FilterSet):

    ip = CharFilter(field_name='ip', lookup_expr='exact')
    project = CharFilter(field_name='log_project_slug', lookup_expr='exact')
    action = ChoiceFilter(
        field_name='action',
        lookup_expr='exact',
        choices=[
            (AuditLog.AUTHN, _('Authentication success')),
            (AuditLog.AUTHN_FAILURE, _('Authentication failure')),
        ],
    )

    class Meta:
        model = AuditLog
        form = _UserSecurityLogForm
        fields = ['ip', 'project', 'action']
