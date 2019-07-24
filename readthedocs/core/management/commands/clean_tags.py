"""
Cleanup project tags.

This specifically aims to cleanup:

- Differences only in lowercase/uppercase
- Slugify all tags
- Remove tags with no projects (old & spam mostly)
"""

from django.core.management.base import BaseCommand
from django.db.models import Count
from taggit.models import Tag
from taggit.utils import parse_tags, edit_string_for_tags

from readthedocs.projects.models import Project


class Command(BaseCommand):

    help = __doc__
    dry_run = False

    def reprocess_tags(self):
        self.stdout.write('Reprocessing tags (lowercasing, slugifying, etc.)...')
        project_total = Project.objects.count()

        # Use an iterator so the queryset isn't stored in memory
        # This may take a long time but should be memory efficient
        for i, project in enumerate(Project.objects.iterator()):
            old_tags_objs = list(project.tags.all())

            if old_tags_objs:
                old_tags = sorted([t.name for t in old_tags_objs])
                old_tag_string = edit_string_for_tags(old_tags_objs)
                new_tags = parse_tags(old_tag_string)

                # Update the tags on the project if they are different
                # Note: "parse_tags" handles sorting
                if new_tags != old_tags:
                    if not self.dry_run:
                        self.stdout.write(
                            '[{}/{}] Setting tags on "{}"'.format(
                                i + 1,
                                project_total,
                                project.slug,
                            )
                        )
                        project.tags.set(*new_tags)
                    else:
                        self.stdout.write(
                            '[{}/{}] Not setting tags on "{}" (dry run)'.format(
                                i + 1,
                                project_total,
                                project.slug,
                            )
                        )

    def remove_tags_with_no_projects(self):
        self.stdout.write('Removing tags with no projects...')
        for tag in Tag.objects.all().annotate(num=Count('taggit_taggeditem_items')).filter(num=0):
            if not self.dry_run:
                self.stdout.write('Removing tag {}'.format(tag.name))
                tag.delete()
            else:
                self.stdout.write('Not removing tag "{}" (dry run)'.format(tag.name))

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Don't actually perform the actions, just print output",
        )

    def handle(self, *args, **options):
        self.dry_run = options["dry_run"]

        self.reprocess_tags()
        self.remove_tags_with_no_projects()
