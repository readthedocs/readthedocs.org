from django.contrib.staticfiles.storage import StaticFilesStorage as BaseStaticFilesStorage

from readthedocs.storage.filesystem import RTDFileSystemStorage


class BuildMediaFileSystemStorage(RTDFileSystemStorage):
    """Storage subclass that writes build artifacts in PRODUCTION_MEDIA_ARTIFACTS or MEDIA_ROOT."""

    # Root path of the nginx internal redirect
    # that will serve files from this storage.
    internal_redirect_root_path = "proxito"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class StaticFilesStorage(BaseStaticFilesStorage):
    # Root path of the nginx internal redirect
    # that will serve files from this storage.
    internal_redirect_root_path = "proxito-static"
