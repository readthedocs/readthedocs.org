import json

from django.core.management.base import BaseCommand

from readthedocs.oauth.models import RemoteRepository


class Command(BaseCommand):
    help = "Load Project and RemoteRepository Relationship from JSON file"

    def add_arguments(self, parser):
        # File path of the json file containing relationship data
        parser.add_argument(
            '--file',
            required=True,
            nargs=1,
            type=str,
            help='File path of the json file containing relationship data.',
        )

    def handle(self, *args, **options):
        file = options.get('file')[0]

        try:
            # Load data from the json file
            with open(file, 'r') as f:
                data = json.load(f)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Exception occurred while trying to load the file "{file}". '
                    f'Exception: {e}.'
                )
            )
            return

        for item in data:
            try:
                update_count = RemoteRepository.objects.filter(
                    remote_id=item['remote_id']
                ).update(project_id=item['project_id'])

                if update_count < 1:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Could not update {item['slug']}'s "
                            f"relationship with {item['html_url']}, "
                            f"remote_id {item['remote_id']}, "
                            f"username: {item['username']}."
                        )
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Exception occurred while trying to update {item['slug']}'s "
                        f"relationship with {item['html_url']}, "
                        f"username: {item['username']}, Exception: {e}."
                    )
                )
