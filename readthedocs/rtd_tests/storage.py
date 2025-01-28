from readthedocs.builds.storage import BuildMediaFileSystemStorage


class BuildMediaFileSystemStorageTest(BuildMediaFileSystemStorage):
    internal_redirect_root_path = "proxito"

    def exists(self, *args, **kargs):
        return True


class StaticFileSystemStorageTest(BuildMediaFileSystemStorageTest):
    internal_redirect_root_path = "proxito-static"
