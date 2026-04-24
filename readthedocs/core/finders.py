import os

from debug_toolbar.apps import DebugToolbarConfig
from django.contrib.staticfiles.finders import AppDirectoriesFinder


class DebugToolbarFinder(AppDirectoriesFinder):
    """
    Finder to copy the static files for `debug_toolbar` even if it's not installed.

    We want to do this because we run `collectstatic` from `web` instance
    which does not have `debug_toolbar` installed.
    Then, when running the `admin` instance from `web-extra` with `debug_toolbar` installed,
    if fails because it does not find the static files.

    By forcing collecting these static files even when `debug_toolbar` is not installed,
    we avoid this issue when running the `admin` instance.
    """

    def __init__(self, *args, app_names=None, **kwargs):
        app_config = DebugToolbarConfig.create("debug_toolbar")
        self.apps = [app_config.name]
        self.storages = {
            app_config.name: self.storage_class(
                os.path.join(
                    app_config.path,
                    self.source_dir,
                )
            )
        }
