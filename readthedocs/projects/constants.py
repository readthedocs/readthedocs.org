"""Default values and other various configuration for projects,
including available theme names and repository types.
"""

import re

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
    ('sphinx_singlehtml', _('Sphinx Single Page HTML')),
    ('mkdocs', _('Mkdocs')),
    #('sphinx_websupport2', _('Sphinx Websupport')),
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

# in the future this constant can be replaced with a implementation that
# detect all available Python interpreters in the fly (Maybe using
# update-alternatives linux tool family?).
PYTHON_CHOICES = (
    ('python', _('CPython 2.x')),
    ('python3', _('CPython 3.x')),
)

# Via http://sphinx-doc.org/latest/config.html#confval-language
LANGUAGES = (
    ("bn", "Bengali"),
    ("ca", "Catalan"),
    ("cs", "Czech"),
    ("da", "Danish"),
    ("de", "German"),
    ("en", "English"),
    ("es", "Spanish"),
    ("et", "Estonian"),
    ("eu", "Basque"),
    ("fa", "Iranian"),
    ("fi", "Finnish"),
    ("fr", "French"),
    ("hr", "Croatian"),
    ("hu", "Hungarian"),
    ("id", "Indonesian"),
    ("it", "Italian"),
    ("ja", "Japanese"),
    ("ko", "Korean"),
    ("lt", "Lithuanian"),
    ("lv", "Latvian"),
    ("mk", "Macedonian"),
    ("ne", "Nepali"),
    ("nl", "Dutch"),
    ("pl", "Polish"),
    ("ru", "Russian"),
    ("si", "Sinhala"),
    ("sk", "Slovak"),
    ("sl", "Slovenian"),
    ("sv", "Swedish"),
    ("tr", "Turkish"),
    ("vi", "Vietnamese"),
    # Try these to test our non-2 letter language support
    ("nb_NO", "Norwegian Bokmal"),
    ("pt_BR", "Brazilian Portuguese"),
    ("uk_UA", "Ukrainian"),
    ("zh_CN", "Simplified Chinese"),
    ("zh_TW", "Traditional Chinese"),
)

LANGUAGES_REGEX = "|".join(
    [re.escape(code[0]) for code in LANGUAGES]
)

LOG_TEMPLATE = u"(Build) [{project}:{version}] {msg}"
