from builds.models import Version
from django.core.management.base import BaseCommand
from projects.tasks import update_docs


class Command(BaseCommand):
    """Custom management command to rebuild documentation for all projects on
    the site. Invoked via ``./manage.py update_repos``.
    """

    def handle(self, *args, **options):
        for version in Version.objects.filter(active=True, built=False):
            update_docs(version.project_id, record=False,
                        version_pk=version.pk)
