from django.contrib.staticfiles.storage import StaticFilesStorage as BaseStaticFilesStorage

from readthedocs.storage.filesystem import RTDFileSystemStorage


class BuildMediaFileSystemStorage(RTDFileSystemStorage):
    # Root path of the nginx internal redirect
    # that will serve files from this storage.
    internal_redirect_root_path = "proxito"


class StaticFilesStorage(BaseStaticFilesStorage):
    # Root path of the nginx internal redirect
    # that will serve files from this storage.
    internal_redirect_root_path = "proxito-static"
