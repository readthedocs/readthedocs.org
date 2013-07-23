from django.contrib import admin
from .models import SphinxComment, SphinxNode


admin.site.register(SphinxNode)
admin.site.register(SphinxComment)
