from readthedocs.core.mixins import ProxiedAPIMixin
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.embed.v3.views import EmbedAPIBase


class ProxiedEmbedAPIBase(ProxiedAPIMixin, EmbedAPIBase):
    pass


class ProxiedEmbedAPI(SettingsOverrideObject):
    _default_class = ProxiedEmbedAPIBase
