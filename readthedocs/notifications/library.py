from django.conf import settings
from django.template import Template, Context
from django.template.loader import render_to_string
from django.db import models


TEXT = 'txt'
HTML = 'html'


class NotificationSource(object):

    name = None
    context_object_name = 'object'

    def __init__(self, object):
        self.object = object

    def get_subject(self):
        template = Template(self.subject)
        return template.render(context=Context({
            self.context_object_name: self.object
        }))

    def get_template_names(self, backend_name, source_format=HTML):
        names = []
        if self.object and isinstance(self.object, models.Model):
            names.append(
                '{app}/notifications/{name}_{backend}.{source_format}'
                .format(
                    app=self.object._meta.app_label,
                    name=self.name or self.object._meta.model_name,
                    backend=backend_name,
                    source_format=source_format,
                ))
            return names
        else:
            raise AttributeError()

    def render(self, backend_name, source_format=HTML):
        return render_to_string(
            template_name=self.get_template_names(
                backend_name=backend_name,
                source_format=source_format,
            ),
            context=Context({
                self.context_object_name: self.object
            })
        )
