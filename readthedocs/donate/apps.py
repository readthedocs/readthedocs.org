from django.apps import AppConfig


class DonateAppConfig(AppConfig):
    name = 'readthedocs.donate'
    verbose_name = 'Donate'

    def ready(self):
        import readthedocs.donate.signals  # noqa
