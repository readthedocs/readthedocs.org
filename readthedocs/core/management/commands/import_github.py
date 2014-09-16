from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from oauth.utils import import_github


class Command(BaseCommand):

    def handle(self, *args, **options):
        if len(args):
            for slug in args:
                import_github(user=User.objects.get(username=slug), sync=True)
