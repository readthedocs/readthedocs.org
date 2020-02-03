from ..test import CommunityTestSettings
from .base import ProxitoSettingsMixin


class CommunityProxitoTestSettings(
        ProxitoSettingsMixin,
        CommunityTestSettings
):

    pass


CommunityProxitoTestSettings.load_settings(__name__)
