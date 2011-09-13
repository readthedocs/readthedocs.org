import imp
import sys
import traceback

class ErrorlessImport(object):
    def find_module(self, name, path):
        try:
            return imp.find_module(name, path)
        except ImportError:
            #raise
            return FreeLoader()


class Mock(object):
    def __repr__(self):
        return "<Silly Human, I'm not real>"

    def __eq__(self, b):
        return True

    def __getattr__(self, *args, **kwargs):
        return Mock()

    def __call__(self, *args, **kwargs):
        return Mock()


class FreeLoader:
    def load_module(self, fullname):
        return Mock()


def patch_meta_path():
    FreeLoader._class = ErrorlessImport()
    sys.meta_path += [FreeLoader._class]

def unpatch_meta_path():
    sys.meta_path.remove(FreeLoader._class)
    #sys.meta_path = []
