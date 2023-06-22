from django.db import models

from .querysets import ImportedFileQuerySet


class HTMLFileManager(models.Manager):

    def get_queryset(self):
        return ImportedFileQuerySet(self.model, using=self._db).html_files()
