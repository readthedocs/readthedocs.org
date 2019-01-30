from django.db import models


class HTMLFileManager(models.Manager):

    def get_queryset(self):
        return super(HTMLFileManager, self).get_queryset().filter(name__endswith='.html')
