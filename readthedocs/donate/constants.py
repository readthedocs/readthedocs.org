"""Constants used by the donate app."""

DISPLAY_CHOICES = (
    ('doc', 'Documentation Pages'),
    ('site-footer', 'Site Footer'),
    ('search', 'Search Pages'),
    ('error', 'Error Pages'),
)

INCLUDE = 'include'
EXCLUDE = 'exclude'

FILTER_CHOICES = (
    (EXCLUDE, 'Exclude'),
    (INCLUDE, 'Include'),
)

OFFERS = 'offers'
VIEWS = 'views'
CLICKS = 'clicks'

IMPRESSION_TYPES = (
    OFFERS,
    VIEWS,
    CLICKS
)

ANY = 'any'
READTHEDOCS_THEME = 'sphinx_rtd_theme'
ALABASTER_THEME = 'alabaster'

THEMES = (
    (ANY, 'Any'),
    (ALABASTER_THEME, 'Alabaster Theme'),
    (READTHEDOCS_THEME, 'Read the Docs Sphinx Theme'),
)
