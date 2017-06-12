"""Support functions for donations."""

from __future__ import absolute_import
import pytz
import datetime

from django.core.cache import cache

from readthedocs.donate.constants import OFFERS, CLICKS, VIEWS


def get_ad_day():
    date = pytz.utc.localize(datetime.datetime.utcnow())
    day = datetime.datetime(
        year=date.year,
        month=date.month,
        day=date.day,
        tzinfo=pytz.utc,
    )
    return day


def offer_promo(promo_obj, project=None):
    """
    Do the book keeping required to track promo offers.

    This generated a hash as part of the return dict,
    so that must be used throughout the processing pipeline in order to dedupe clicks.
    """
    promo_dict = promo_obj.as_dict()
    promo_obj.incr(OFFERS)
    # Set validation cache
    for promo_type in [VIEWS, CLICKS]:
        cache.set(
            promo_obj.cache_key(type=promo_type, hash=promo_dict['hash']),
            0,  # Number of times used. Make this an int so we can detect multiple uses
            60 * 60  # hour
        )

    if project:
        # Set project for hash key, so we can count it later.
        promo_obj.incr(OFFERS, project=project)
        cache.set(
            promo_obj.cache_key(type='project', hash=promo_dict['hash']),
            project.slug,
            60 * 60  # hour
        )
    return promo_dict
