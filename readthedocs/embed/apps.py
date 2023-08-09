"""Embed app config."""

from django.apps import AppConfig


class EmbedConfig(AppConfig):
    name = "readthedocs.embed"
    verbose_name = "Embedded API"
