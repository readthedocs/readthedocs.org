"""Resync GitHub project for user"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from readthedocs.oauth.services import GitHubService


class Command(BaseCommand):

    help = __doc__

    def handle(self, *args, **options):
        if len(args):
            for slug in args:
                for service in GitHubService.for_user(
                    User.objects.get(username=slug)
                ):
                    service.sync()
