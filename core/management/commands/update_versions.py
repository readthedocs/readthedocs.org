from django.core.management.base import BaseCommand
from projects import tasks
from projects.models import Project
from optparse import make_option



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
        if not len(args):
            tasks.update_docs_pull(pdf=make_pdf)
        else:
            for slug in args:
                p = Project.objects.get(slug=slug)
                print "Building %s" % p
                tasks.update_docs(p.pk, pdf=make_pdf)
