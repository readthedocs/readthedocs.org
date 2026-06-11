import structlog
from django.core.management.base import BaseCommand, CommandError

from readthedocs.builds.constants import EXTERNAL
from readthedocs.core.utils import trigger_build
from readthedocs.projects.models import Project

log = structlog.get_logger(__name__)


class Command(BaseCommand):
    help = "Trigger builds for all active versions of a project."

    def add_arguments(self, parser):
        parser.add_argument(
            "project_slug",
            type=str,
            help="Slug of the project to rebuild.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List versions that would be rebuilt without triggering builds.",
        )

    def handle(self, *args, **options):
        project_slug = options["project_slug"]
        dry_run = options["dry_run"]

        try:
            project = Project.objects.get(slug=project_slug)
        except Project.DoesNotExist:
            raise CommandError(f"Project with slug '{project_slug}' not found.")

        versions = project.versions.filter(active=True).exclude(type=EXTERNAL)

        if not versions.exists():
            self.stdout.write(f"No active versions found for '{project_slug}'.")
            return

        self.stdout.write(
            f"Found {versions.count()} active version(s) for '{project_slug}':"
        )
        for version in versions:
            self.stdout.write(f"  - {version.verbose_name} ({version.slug})")

        if dry_run:
            self.stdout.write("Dry run, no builds triggered.")
            return

        triggered = 0
        for version in versions:
            _, build = trigger_build(project=project, version=version)
            if build is not None:
                self.stdout.write(
                    f"  Triggered build #{build.pk} for {version.verbose_name}"
                )
                triggered += 1
            else:
                self.stdout.write(
                    f"  Skipped {version.verbose_name} (build not created)"
                )

        self.stdout.write(f"Done. Triggered {triggered} build(s).")
