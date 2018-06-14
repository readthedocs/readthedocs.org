from django.db import models


class HTMLFileManager(models.Manager):

    def get_queryset(self):
        return super(HTMLFileManager, self).get_queryset().filter(name__endswith='.html')


class ImportedFileManager(models.Manager):

    def get_queryset(self):
        # Exclude the html file as its handled by HTMLFile
        return super(ImportedFileManager, self).get_queryset().exclude(name__endswith='.html')
