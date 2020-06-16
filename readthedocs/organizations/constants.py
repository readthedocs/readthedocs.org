"""Constants for ACL."""

from django.utils.translation import ugettext_lazy as _

READ_ONLY_ACCESS = 'readonly'
ADMIN_ACCESS = 'admin'

ACCESS_LEVELS = (
    (READ_ONLY_ACCESS, _('Read-only')),
    (ADMIN_ACCESS, _('Admin')),
)
