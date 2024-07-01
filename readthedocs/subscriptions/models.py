from djstripe.models import Subscription
from simple_history import register

from readthedocs.core.history import ExtraHistoricalRecords

register(Subscription, records_class=ExtraHistoricalRecords, app=__package__)
