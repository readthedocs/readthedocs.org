from django.db import connection
from django.db.models import Count

from rest_framework import decorators, permissions
from rest_framework.renderers import JSONPRenderer, JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response

from builds.models import Build


VALID_INTERVALS = (
    'minute',
    'second',
    'hour',
    'day',
    'week',
    'month',
    'quarter',
    'year'
)


@decorators.api_view(['GET'])
@decorators.permission_classes((permissions.AllowAny,))
@decorators.renderer_classes((JSONRenderer, JSONPRenderer, BrowsableAPIRenderer))
def build_stats(request):
    """Returns the number of builds per the given interval."""
    interval = request.GET.get('interval', 'hour')
    if connection.vendor != 'postgresql':
        return Response({
            'error': 'This query relies on postgres date_trunc, postgres is the only support DB for this endpoint.'
        })
    if interval not in VALID_INTERVALS:
        return Response({
            'error': 'interval not valid. Valid choices are ' + ', '.join(VALID_INTERVALS)
        })
    results = (Build.objects.filter(state='finished')
                            .extra(select={'when': 'extract(epoch from date_trunc(%s, date))'},
                                   select_params=(interval,))
                            .values('when')
                            .annotate(count=Count('id'))
                            .order_by('when'))

    return Response({'results': list(results)})
