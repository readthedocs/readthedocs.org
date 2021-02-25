import json

from django.core.management.base import BaseCommand

from readthedocs.projects.models import Project


class Command(BaseCommand):
    help = "Dump Project and RemoteRepository Relationship in JSON format"

    def handle(self, *args, **options):
        data = []

        queryset = Project.objects.filter(
            remote_repository__isnull=False,
        ).values_list('id', 'remote_repository__json').distinct()

        for project_id, remote_repository__json in queryset:
            try:
                json_data = json.loads(remote_repository__json)
                # GitHub and GitLab uses `id` and Bitbucket uses `uuid`
                # for the repository id
                remote_id = json_data.get('id') or json_data.get('uuid')

                if remote_id:
                    data.append({
                        'remote_id': remote_id,
                        'project_id': project_id
                    })
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Project {project_id} does not have a remote_repository remote_id'
                        )
                    )
            except json.decoder.JSONDecodeError:
                self.stdout.write(
                    self.style.ERROR(
                        f'Project {project_id} does not have a valid remote_repository__json'
                    )
                )

        # Dump the data to a json file
        with open('project-remote-repo-dump.json', 'w') as f:
            f.write(json.dumps(data))
