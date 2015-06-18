from django.utils.translation import ugettext_lazy as _

BUILD_STATE = (
    ('triggered', _('Triggered')),
    ('cloning', _('Cloning')),
    ('installing', _('Installing')),
    ('building', _('Building')),
    ('finished', _('Finished')),
)

BUILD_TYPES = (
    ('html', _('HTML')),
    ('pdf', _('PDF')),
    ('epub', _('Epub')),
    # There is currently no support for building man/dash formats, but we keep
    # it there since the DB might still contain those values for legacy
    # projects.
    ('man', _('Manpage')),
    ('dash', _('Dash')),
)

VERSION_TYPES = (
    ('branch', _('Branch')),
    ('tag', _('Tag')),
    ('unknown', _('Unknown')),
)
