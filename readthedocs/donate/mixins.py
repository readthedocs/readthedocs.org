'''
Mixin classes for donation views
'''

from django.db.models import Avg, Sum

from .models import Supporter


class DonateProgressMixin(object):
    '''Add donation progress to context data'''

    def get_context_data(self):
        context = super(DonateProgressMixin, self).get_context_data()
        sums = (Supporter.objects
                .aggregate(dollars=Sum('dollars')))
        avgs = (Supporter.objects
                .aggregate(dollars=Avg('dollars')))
        dollars = sums.get('dollars', None) or 0
        avg = int(avgs.get('dollars', None) or 0)
        count = Supporter.objects.count()
        percent = int((float(dollars) / 24000.0) * 100.0)
        context.update({
            'donate_amount': dollars,
            'donate_avg': avg,
            'donate_percent': percent,
            'donate_count': count,
        })
        return context
