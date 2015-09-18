"""Constants used for OAuth services"""

from django.utils.translation import ugettext_lazy as _


OAUTH_SOURCE_GITHUB = 'github'
OAUTH_SOURCE_BITBUCKET = 'bitbucket'

OAUTH_SOURCE = (
    (OAUTH_SOURCE_GITHUB, _('GitHub')),
    (OAUTH_SOURCE_BITBUCKET, _('Bitbucket')),
)
