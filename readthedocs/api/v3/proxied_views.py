from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.embed.v3.views import EmbedAPIBase
from readthedocs.core.mixins import AuthenticatedClassesMixin


class ProxiedEmbedAPIBase(EmbedAPIBase, AuthenticatedClassesMixin):
    
    pass

class ProxiedEmbedAPI(SettingsOverrideObject):

    _default_class = ProxiedEmbedAPIBase
