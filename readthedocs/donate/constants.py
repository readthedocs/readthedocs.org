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
