from django.core.management.base import BaseCommand
from optparse import make_option
from projects import tasks
from projects.models import Project

class Command(BaseCommand):
    """Custom management command to rebuild documentation for all projects on
    the site. Invoked via ``./manage.py update_repos``.
    """
    option_list = BaseCommand.option_list + (
        make_option('-p',
            action='store_true',
            dest='pdf',
            default=False,
            help='Make a pdf'
            ),
        make_option('-r',
            action='store_true',
            dest='record',
            default=False,
            help='Make a Build'
            ),
        make_option('-t',
            action='store_true',
            dest='touch',
            default=False,
            help='Touch the files'
            )
        )

    def handle(self, *args, **options):
        make_pdf = options['pdf']
        record = options['record']
        touch = options['touch']
        if not len(args):
            tasks.update_docs_pull(pdf=make_pdf, record=record, touch=touch)
        else:
            for slug in args:
                p = Project.objects.get(slug=slug)
                print "Building %s" % p
                tasks.update_docs(p.pk, pdf=make_pdf, touch=touch)
