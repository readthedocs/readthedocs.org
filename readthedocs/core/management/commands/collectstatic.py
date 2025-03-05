"""
Override to send ``pre_collectstatic`` and ``post_collectstatic`` signal.

``post_collectstatic`` is used to purge the CDN of static files.
"""

from django.contrib.staticfiles.management.commands import collectstatic

from readthedocs.core.signals import post_collectstatic
from readthedocs.core.signals import pre_collectstatic


class Command(collectstatic.Command):
    def handle(self, **options):
        pre_collectstatic.send(sender=self.__class__)
        response = super().handle(**options)
        post_collectstatic.send(sender=self.__class__)
        return response
