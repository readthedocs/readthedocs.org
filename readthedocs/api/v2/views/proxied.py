from readthedocs.api.v2.views.footer_views import BaseFooterHTML
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.embed.views import EmbedAPIBase
from readthedocs.core.mixins import ProxiedAPIMixin


class BaseProxiedFooterHTML(ProxiedAPIMixin, BaseFooterHTML):

    pass


class ProxiedFooterHTML(SettingsOverrideObject):

    _default_class = BaseProxiedFooterHTML


class ProxiedEmbedAPIBase(ProxiedAPIMixin, EmbedAPIBase):

    pass


class ProxiedEmbedAPI(SettingsOverrideObject):

    _default_class = ProxiedEmbedAPIBase
