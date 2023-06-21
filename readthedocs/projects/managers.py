from django.db import models


class HTMLFileManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().html_files()
