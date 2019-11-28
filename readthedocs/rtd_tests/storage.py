from readthedocs.builds.storage import BuildMediaFileSystemStorage

class BuildMediaFileSystemStorageTest(BuildMediaFileSystemStorage):

    def exists(self, *args, **kargs):
        return True
