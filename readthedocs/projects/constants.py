"""Default values and other various configuration for projects,
including available theme names and repository types.
"""

from django.utils.translation import ugettext_lazy as _

THEME_DEFAULT = 'default'
THEME_SPHINX = 'sphinxdoc'
THEME_SCROLLS = 'scrolls'
THEME_AGOGO = 'agogo'
THEME_TRADITIONAL = 'traditional'
THEME_NATURE = 'nature'
THEME_HAIKU = 'haiku'

DOCUMENTATION_CHOICES = (
    ('sphinx', _('Sphinx Html')),
    ('sphinx_htmldir', _('Sphinx HtmlDir')),
    #('sphinx_man', 'Sphinx Man'),
    #('rdoc', 'Rdoc'),
)

DEFAULT_THEME_CHOICES = (
    # Translators: This is a name of a Sphinx theme.
    (THEME_DEFAULT, _('Default')),
    # Translators: This is a name of a Sphinx theme.
    (THEME_SPHINX, _('Sphinx Docs')),
    #(THEME_SCROLLS, 'Scrolls'),
    #(THEME_AGOGO, 'Agogo'),
    # Translators: This is a name of a Sphinx theme.
    (THEME_TRADITIONAL, _('Traditional')),
    # Translators: This is a name of a Sphinx theme.
    (THEME_NATURE, _('Nature')),
    # Translators: This is a name of a Sphinx theme.
    (THEME_HAIKU, _('Haiku')),
)

SAMPLE_FILES = (
    ('Installation', 'projects/samples/installation.rst.html'),
    ('Getting started', 'projects/samples/getting_started.rst.html'),
)

SCRAPE_CONF_SETTINGS = [
    'copyright',
    'project',
    'version',
    'release',
    'source_suffix',
    'html_theme',
    'extensions',
]

HEADING_MARKUP = (
    (1, '='),
    (2, '-'),
    (3, '^'),
    (4, '"'),
)

LIVE_STATUS = 1
DELETED_STATUS = 99

STATUS_CHOICES = (
    (LIVE_STATUS, _('Live')),
    (DELETED_STATUS, _('Deleted')),
)

REPO_CHOICES = (
    ('git', _('Git')),
    ('svn', _('Subversion')),
    ('hg', _('Mercurial')),
    ('bzr', _('Bazaar')),
)

PUBLIC = 'public'
PROTECTED = 'protected'
PRIVATE = 'private'

PRIVACY_CHOICES = (
    (PUBLIC, _('Public')),
    (PROTECTED, _('Protected')),
    (PRIVATE, _('Private')),
)

IMPORTANT_VERSION_FILTERS = {
    'slug': 'important'
}
