"""Telemetry models."""

from django.db import models
from django_extensions.db.models import TimeStampedModel


class BuildDataManager(models.Manager):
    """Manager for the BuildData model."""

    def collect(self, build, data):
        """
        Save the collected information from a build.

        We fill other fields from data we have access to
        before saving it, like the project, version, organization, etc.

        The final JSON structure should look like:

        .. code-block:: json

           {
               "os": "ubuntu-18.04.5"
               "python": "3.10.2",
               "organization": {
                    "id": 1,
                    "slug": "org"
               },
               "project": {
                    "id": 2,
                    "slug": "docs"
               },
               "version": {
                    "id": 1,
                    "slug": "latest"
               },
               "build": {
                    "id": 3,
                    "start": "2021-04-20-...",  # Date in isoformat
                    "length": "600",  # Build length in seconds
                    "commit": "abcd1234"
                    "success": true,
               },
               "config": {
                    "user": {},
                    "final": {}
               },
               "packages": {
                   "pip": {
                       "user": [
                            {
                                "name": "sphinx",
                                "version": "3.4.5"
                            },
                       ],
                       "all": [
                            {
                                "name": "sphinx",
                                "version": "3.4.5"
                            },
                       ],
                   },
                   "conda": {
                       "all": [
                           {
                                "name": "sphinx",
                                "channel": "conda-forge",
                                "version": "0.1"
                           },
                       ],
                   },
                   "apt": {
                       "user": [
                           {
                               "name": "python3-dev",
                               "version": "3.8.2-0ubuntu2"
                           },
                       ],
                       "all": [
                           {
                               "name": "python3-dev",
                               "version": "3.8.2-0ubuntu2"
                           },
                       ],
                   },
               },
           }
        """
        data["build"] = {
            "id": build.id,
            "start": build.date.isoformat(),
            "length": build.length,
            "commit": build.commit,
            "success": build.success,
        }
        data["project"] = {"id": build.project.id, "slug": build.project.slug}
        if build.version:
            data["version"] = {
                "id": build.version.id,
                "slug": build.version.slug,
            }
        org = build.project.organizations.first()
        if org:
            data["organization"] = {
                "id": org.id,
                "slug": org.slug,
            }
        data["config"]["final"] = build.config
        return self.create(data=data)


class BuildData(TimeStampedModel):
    class Meta:
        verbose_name_plural = "Build data"
        indexes = [
            # Speeds up `delete_old_build_data` task.
            models.Index(fields=["created"]),
        ]

    data = models.JSONField()
    objects = BuildDataManager()
