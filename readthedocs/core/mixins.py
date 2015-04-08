'''
Common mixin classes for views
'''

from django.conf import settings


class StripeMixin(object):
    '''Adds Stripe publishable key to the context data'''

    def get_context_data(self, **kwargs):
        context = super(StripeMixin, self).get_context_data(**kwargs)
        context.update({
            'publishable': settings.STRIPE_PUBLISHABLE,
        })
        return context
