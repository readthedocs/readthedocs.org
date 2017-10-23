from django.core.management.base import BaseCommand

from readthedocs.projects.models import Project


class Command(BaseCommand):

    def handle(self, *args, **options):
        projects = Project.objects.filter(
            slug__contains='customer').filter(
            slug__contains='support').filter(
            slug__contains='number')
        for project in projects:
            if not project.has_good_build:
                project.delete()
