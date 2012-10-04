from django.utils.translation import ugettext_lazy as _

BUILD_STATE = (
    ('triggered', _('Triggered')),
    ('building', _('Building')),
    ('finished', _('Finished')),
)

BUILD_TYPES = (
    ('html', _('HTML')),
    ('pdf', _('PDF')),
    ('epub', _('Epub')),
    ('man', _('Manpage')),
)
