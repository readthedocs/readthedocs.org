THEME_DEFAULT = 'default'
THEME_SPHINX = 'sphinxdoc'
THEME_SCROLLS = 'scrolls'
THEME_AGOGO = 'agogo'
THEME_TRADITIONAL = 'traditional'
THEME_NATURE = 'nature'
THEME_HAIKU = 'haiku'

DEFAULT_THEME_CHOICES = (
    (THEME_DEFAULT, 'Default'),
    (THEME_SPHINX, 'Sphinx Docs'),
    #(THEME_SCROLLS, 'Scrolls'),
    #(THEME_AGOGO, 'Agogo'),
    (THEME_TRADITIONAL, 'Traditional'),
    (THEME_NATURE, 'Nature'),
    (THEME_HAIKU, 'Haiku'),
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
    (LIVE_STATUS, 'Live'),
    (DELETED_STATUS, 'Deleted'),
)

REPO_CHOICES = (
    ('git', 'Git'),
    ('svn', 'Subversion'),
    ('hg', 'Mercurial'),
    ('bzr', 'Bazaar'),
)

