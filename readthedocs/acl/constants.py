"""Constants for ACL"""

from django.utils.translation import ugettext_lazy as _

ACCESS_READONLY = 'readonly'

ACCESS_LEVELS = (
    (ACCESS_READONLY, _('Read-only')),
)
