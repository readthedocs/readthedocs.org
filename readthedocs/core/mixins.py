'''
Common mixin classes for views
'''

from django.conf import settings

from vanilla import ListView


class StripeMixin(object):

    '''Adds Stripe publishable key to the context data'''

    def get_context_data(self, **kwargs):
        context = super(StripeMixin, self).get_context_data(**kwargs)
        context.update({
            'publishable': settings.STRIPE_PUBLISHABLE,
        })
        return context


class ListViewWithForm(ListView):

    '''List view that also exposes a create form'''

    def get_context_data(self, **kwargs):
        context = super(ListViewWithForm, self).get_context_data(**kwargs)
        context['form'] = self.get_form(data=None, files=None)
        return context
