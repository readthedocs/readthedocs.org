"""List the webhook deliveries GitHub sent to our GitHub App for a project."""

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from readthedocs.oauth.clients import get_gh_app_client
from readthedocs.projects.models import Project


class Command(BaseCommand):
    help = (
        "List the webhook deliveries GitHub sent to our GitHub App for a project. "
        "GitHub only keeps deliveries for a few days."
    )

    def add_arguments(self, parser):
        parser.add_argument("project_slug", type=str)
        parser.add_argument(
            "--max-pages",
            type=int,
            default=20,
            help="Pages of 100 deliveries to search, newest first. Deliveries are for all projects.",
        )
        parser.add_argument(
            "--redeliver",
            type=int,
            metavar="DELIVERY_ID",
            help="Ask GitHub to send this delivery again, instead of listing deliveries.",
        )

    def handle(self, *args, **options):
        requester = get_gh_app_client().requester

        if options["redeliver"]:
            requester.requestJsonAndCheck(
                "POST", f"/app/hook/deliveries/{options['redeliver']}/attempts"
            )
            self.stdout.write(f"Redelivery requested for {options['redeliver']}.")
            return

        project = Project.objects.filter(slug=options["project_slug"]).first()
        if not project or not project.is_github_app_project:
            raise CommandError("Project not found, or it isn't connected to our GitHub App.")
        repository_id = int(project.remote_repository.remote_id)

        url = "/app/hook/deliveries"
        parameters = {"per_page": 100}
        oldest = None
        for _ in range(options["max_pages"]):
            headers, deliveries = requester.requestJsonAndCheck("GET", url, parameters=parameters)
            for delivery in deliveries:
                oldest = delivery["delivered_at"]
                if delivery["repository_id"] == repository_id:
                    self.stdout.write(
                        "{delivered_at}  {id}  {status_code}  {event} {action}  {guid}".format(
                            **delivery
                        )
                    )
            # The next URL already includes the query parameters.
            url, parameters = _get_next_url(headers), None
            if not url:
                break
        self.stdout.write(f"Searched deliveries back to {oldest}.")


def _get_next_url(headers):
    for link in headers.get("link", "").split(","):
        if 'rel="next"' in link:
            return link.split(";")[0].strip(" <>")
    return None
