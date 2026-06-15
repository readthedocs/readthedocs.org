"""Dataclasses used by the API v2 utils."""

from dataclasses import dataclass


@dataclass
class VersionData:
    """Represents version data from a repository (tag or branch).

    :param verbose_name: Human-readable name of the version (e.g. "v1.0.0").
    :param identifier: Git commit identifier (e.g. SHA hash) for the version.
    """

    verbose_name: str
    identifier: str
