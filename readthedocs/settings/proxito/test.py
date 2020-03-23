from ..test import CommunityTestSettings
from .base import CommunityProxitoSettingsMixin


class CommunityProxitoTestSettings(
        CommunityProxitoSettingsMixin,
        CommunityTestSettings
):

    PUBLIC_DOMAIN = 'dev.readthedocs.io'
    RTD_BUILD_MEDIA_STORAGE = 'readthedocs.proxito.tests.storage.BuildMediaStorageTest'

CommunityProxitoTestSettings.load_settings(__name__)
