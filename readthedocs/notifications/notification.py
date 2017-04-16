from django.conf import settings
from django.template import Template, Context
from django.template.loader import render_to_string
from django.db import models

from .backends import send_notification
from .constants import INFO, HTML, TEXT


class Notification(object):

    name = None
    context_object_name = 'object'
    level = INFO
    subject = None
    user = None

    def __init__(self, object, request, user=None):
        self.object = object
        self.request = request
        self.user = user
        if self.user is None:
            self.user = request.user

    def get_subject(self):
        template = Template(self.subject)
        return template.render(context=Context(self.get_context_data()))

    def get_context_data(self):
        return {
            self.context_object_name: self.object,
            'request': self.request,
            'production_uri': '{scheme}://{host}'.format(
                scheme='https', host=settings.PRODUCTION_DOMAIN
            )
        }

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
            context=Context(self.get_context_data()),
        )

    def send(self):
        """Trigger notification send through all notification backends

        In order to limit which backends a notification will send out from,
        override this method and duplicate the logic from
        :py:func:`send_notification`, taking care to limit which backends are
        avoided.
        """
        send_notification(self.request, self)
