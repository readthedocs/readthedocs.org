from readthedocs.api.v2.views.footer_views import BaseFooterHTML
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.embed.views import EmbedAPIBase


class BaseProxiedFooterHTML(BaseFooterHTML):

    # DRF has BasicAuthentication and SessionAuthentication as default classes.
    # We don't support neither in the community site.
    authentication_classes = []


class ProxiedFooterHTML(SettingsOverrideObject):

    _default_class = BaseProxiedFooterHTML


class ProxiedEmbedAPIBase(EmbedAPIBase):

    # DRF has BasicAuthentication and SessionAuthentication as default classes.
    # We don't support neither in the community site.
    authentication_classes = []


class ProxiedEmbedAPI(SettingsOverrideObject):

    _default_class = ProxiedEmbedAPIBase
