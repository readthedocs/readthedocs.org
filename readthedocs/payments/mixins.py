"""Payment view mixin classes"""

from __future__ import absolute_import
from builtins import object
from django.conf import settings


class StripeMixin(object):

    """Adds Stripe publishable key to the context data"""

    def get_context_data(self, **kwargs):
        context = super(StripeMixin, self).get_context_data(**kwargs)
        context['stripe_publishable'] = settings.STRIPE_PUBLISHABLE
        return context

    def get_form(self, data=None, files=None, **kwargs):
        """Pass in copy of POST data to avoid read only QueryDicts on form

        This is used to be able to reset some important credit card fields if
        card validation fails. In this case, the Stripe token was valid, but the
        card was rejected during the charge or subscription instantiation.
        """
        if self.request.method == 'POST':
            data = self.request.POST.copy()
        cls = self.get_form_class()
        return cls(data=data, files=files, **kwargs)
