from builds.models import Version
from django.core.management.base import BaseCommand
from optparse import make_option
from projects.tasks import update_docs


class Command(BaseCommand):
    """Custom management command to rebuild documentation for all projects on
    the site. Invoked via ``./manage.py update_repos``.
    """
    option_list = BaseCommand.option_list + (
        make_option('-p',
                    action='store_true',
                    dest='pdf',
                    default=False,
                    help='Make a pdf'),
    )

    def handle(self, *args, **options):
        make_pdf = options['pdf']
        for version in Version.objects.filter(active=True, built=False):
            update_docs(version.project_id, pdf=make_pdf, record=False,
                        version_pk=version.pk)
