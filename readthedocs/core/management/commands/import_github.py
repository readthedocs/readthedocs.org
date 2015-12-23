from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from readthedocs.oauth.services import GitHubService


class Command(BaseCommand):

    def handle(self, *args, **options):
        if len(args):
            for slug in args:
                service = GitHubService.for_user(User.objects.get(username=slug))
                if service is not None:
                    service.sync(sync=True)
