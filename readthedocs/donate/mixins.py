"""Mixin classes for donation views"""

from __future__ import absolute_import
from __future__ import division
from builtins import object
from past.utils import old_div
from django.db.models import Avg, Sum

from .models import Supporter


class DonateProgressMixin(object):

    """Add donation progress to context data"""

    def get_context_data(self, **kwargs):
        context = super(DonateProgressMixin, self).get_context_data(**kwargs)
        sums = (Supporter.objects
                .aggregate(dollars=Sum('dollars')))
        avgs = (Supporter.objects
                .aggregate(dollars=Avg('dollars')))
        dollars = sums.get('dollars', None) or 0
        avg = int(avgs.get('dollars', None) or 0)
        count = Supporter.objects.count()
        percent = int((old_div(float(dollars), 24000.0)) * 100.0)
        context.update({
            'donate_amount': dollars,
            'donate_avg': avg,
            'donate_percent': percent,
            'donate_count': count,
        })
        return context
