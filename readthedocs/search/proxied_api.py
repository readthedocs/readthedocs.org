from readthedocs.core.utils.extend import SettingsOverrideObject
from .api import PageSearchAPIView


class BaseProxiedPageSearchAPIView(PageSearchAPIView):

    pass


class ProxiedPageSearchAPIView(SettingsOverrideObject):

    _default_class = BaseProxiedPageSearchAPIView
