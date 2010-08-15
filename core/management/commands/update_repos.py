from django.core.management.base import BaseCommand
from projects import tasks

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        tasks.update_docs_pull()

