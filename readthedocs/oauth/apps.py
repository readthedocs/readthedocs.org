"""OAuth app config"""

from django.apps import AppConfig


class OAuthConfig(AppConfig):
    name = 'readthedocs.oauth'

    def ready(self):
        from .tasks import SyncRemoteRepositories
        from readthedocs.worker import app
        app.tasks.register(SyncRemoteRepositories)
