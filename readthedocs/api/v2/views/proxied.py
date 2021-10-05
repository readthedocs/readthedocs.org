from readthedocs.api.v2.views.footer_views import BaseFooterHTML
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.embed.views import EmbedAPIBase
from readthedocs.core.mixins import AuthenticatedClassesMixin


class BaseProxiedFooterHTML(BaseFooterHTML, AuthenticatedClassesMixin):
    
    pass

class ProxiedFooterHTML(SettingsOverrideObject):

    _default_class = BaseProxiedFooterHTML

class ProxiedEmbedAPIBase(EmbedAPIBase, AuthenticatedClassesMixin):

    pass

class ProxiedEmbedAPI(SettingsOverrideObject):

    _default_class = ProxiedEmbedAPIBase
