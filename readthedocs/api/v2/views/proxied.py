from readthedocs.core.mixins import ProxiedAPIMixin
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.embed.views import EmbedAPI


class ProxiedEmbedAPIBase(ProxiedAPIMixin, EmbedAPI):
    pass


class ProxiedEmbedAPI(SettingsOverrideObject):
    _default_class = ProxiedEmbedAPIBase
