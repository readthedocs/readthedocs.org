from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.embed.v3.views import EmbedAPIBase


class ProxiedEmbedAPIBase(EmbedAPIBase):

    # DRF has BasicAuthentication and SessionAuthentication as default classes.
    # We don't support neither in the community site.
    authentication_classes = []


class ProxiedEmbedAPI(SettingsOverrideObject):

    _default_class = ProxiedEmbedAPIBase
