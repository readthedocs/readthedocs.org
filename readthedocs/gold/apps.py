from django.apps import AppConfig


class GoldAppConfig(AppConfig):
    name = 'readthedocs.gold'
    verbose_name = 'Gold'

    def ready(self):
        if hasattr(self, 'already_run'):
            return
        self.already_run = True
        import readthedocs.gold.signals  # noqa
