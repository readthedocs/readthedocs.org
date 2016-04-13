"""Read the Docs constants for common settings and application level pieces"""

from django.conf import settings


# Domains
PRODUCTION_DOMAIN = getattr(settings, 'PRODUCTION_DOMAIN', 'readthedocs.org')
PUBLIC_DOMAIN = getattr(settings, 'PUBLIC_DOMAIN')

# URLs
PUBLIC_API_URL = getattr(settings, 'PUBLIC_API_URL',
                         'https://{0}'.format(PRODUCTION_DOMAIN))

# Configuration
USE_SUBDOMAIN = getattr(settings, 'USE_SUBDOMAIN', False)

# Secondary URLconfs
SUBDOMAIN_URLCONF = getattr(
    settings,
    'SUBDOMAIN_URLCONF',
    'readthedocs.core.subdomain_urls'
)
SINGLE_VERSION_URLCONF = getattr(
    settings,
    'SINGLE_VERSION_URLCONF',
    'readthedocs.core.single_version_urls'
)
