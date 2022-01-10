import structlog

from django.forms.widgets import HiddenInput
from django.utils.translation import ugettext_lazy as _
from django_filters import CharFilter, ChoiceFilter, FilterSet

from readthedocs.builds.constants import BUILD_STATE_FINISHED

log = structlog.get_logger(__name__)


class BuildListFilter(FilterSet):

    STATE_ACTIVE = 'active'
    STATE_SUCCESS = 'succeeded'
    STATE_FAILED = 'failed'

    STATE_CHOICES = (
        (STATE_ACTIVE, _('Active')),
        (STATE_SUCCESS, _('Build finished')),
        (STATE_FAILED, _('Build failed')),
    )

    # Attribute filter fields
    version = CharFilter(field_name='version__slug', widget=HiddenInput)
    state = ChoiceFilter(
        label=_('State'),
        choices=STATE_CHOICES,
        empty_label=_('Any'),
        method='get_state',
    )

    def get_state(self, queryset, name, value):
        if value == self.STATE_ACTIVE:
            queryset = queryset.exclude(state=BUILD_STATE_FINISHED)
        elif value == self.STATE_SUCCESS:
            queryset = queryset.filter(state=BUILD_STATE_FINISHED, success=True)
        elif value == self.STATE_FAILED:
            queryset = queryset.filter(
                state=BUILD_STATE_FINISHED,
                success=False,
            )
        return queryset
