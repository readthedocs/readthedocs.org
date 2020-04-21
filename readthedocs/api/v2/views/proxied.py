from readthedocs.core.utils.extend import SettingsOverrideObject

from .footer_views import BaseFooterHTML


class BaseProxiedFooterHTML(BaseFooterHTML):

    # DRF has BasicAuthentication and SessionAuthentication as default classes.
    # We don't support neither in the community site.
    authentication_classes = []


class ProxiedFooterHTML(SettingsOverrideObject):

    _default_class = BaseProxiedFooterHTML
