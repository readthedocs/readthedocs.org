import json

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.models import OuterRef, Subquery
from django.utils import timezone

from readthedocs.projects.models import Project


class Command(BaseCommand):
    help = "Dump Project and RemoteRepository Relationship in JSON format"

    def handle(self, *args, **options):
        data = []

        users = User.objects.filter(
            oauth_repositories__project=OuterRef("pk")
        )

        queryset = Project.objects.filter(
            remote_repository__isnull=False,
        ).annotate(
            username=Subquery(users.values("username")[:1])
        ).values_list(
            'id',
            'slug',
            'remote_repository__json',
            'remote_repository__html_url',
            'username'
        ).distinct()

        for project_id, slug, remote_repo_json, url, username in queryset.iterator():
            try:
                json_data = json.loads(remote_repo_json)
                # GitHub and GitLab uses `id` and Bitbucket uses `uuid`
                # for the repository id
                remote_id = json_data.get('id') or json_data.get('uuid')

                if remote_id:
                    data.append({
                        'project_id': project_id,
                        'slug': slug,
                        'remote_id': remote_id,
                        'html_url': url,
                        'username': username,
                    })
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Project {slug} does not have a remote_repository remote_id'
                        )
                    )
            except json.decoder.JSONDecodeError:
                self.stdout.write(
                    self.style.ERROR(
                        f'Project {slug} does not have a valid remote_repository__json'
                    )
                )

        # Dump the data to a json file
        with open(f'project-remote-repo-dump-{timezone.now():%Y-%m-%d-%H:%M}.json', 'w') as f:
            f.write(json.dumps(data))
