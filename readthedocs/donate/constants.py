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

DOLLAR_AMOUNTS = [
    ('custom', "Custom amount"),
    (5, "$5"),
    (10, "$10"),
    (25, "$25"),
    (50, "1 Hour ($50)"),
    (100, "2 Hours ($100)"),
    (200, "4 Hours ($200)"),
    (400, "1 Day ($400)"),
    (800, "2 Days ($800)"),
    (1200, "3 Days ($1200)"),
    (1600, "4 Days ($1600)"),
    (2000, "5 Days ($2000)"),
    (4000, "2 Weeks ($4000)"),
    (6000, "3 Weeks ($6000)"),
    (8000, "4 Weeks ($8000)"),
]
