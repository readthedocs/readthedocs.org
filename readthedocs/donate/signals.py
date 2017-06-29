"""Django signal plumbing for the donate app."""

from __future__ import absolute_import
import random
import logging

from django.dispatch import receiver
from django.conf import settings
from django.core.cache import cache

import redis

from readthedocs.restapi.signals import footer_response
from readthedocs.donate.models import SupporterPromo
from readthedocs.donate.constants import INCLUDE, EXCLUDE
from readthedocs.donate.utils import offer_promo


log = logging.getLogger(__name__)

PROMO_GEO_PATH = getattr(settings, 'PROMO_GEO_PATH', None)

if PROMO_GEO_PATH:
    import geoip2.database  # noqa
    from geoip2.errors import AddressNotFoundError  # noqa
    geo_reader = geoip2.database.Reader(PROMO_GEO_PATH)


def show_to_geo(promo, country_code):
    # Remove promo's that exclude this country.
    for geo_filter in promo.geo_filters.all():
        if geo_filter.filter_type == INCLUDE:
            if country_code in geo_filter.codes:
                continue
            else:
                return False
        if geo_filter.filter_type == EXCLUDE:
            if country_code in geo_filter.codes:
                return False

    return True


def show_to_programming_language(promo, programming_language):
    """
    Filter a promo by a specific programming language

    Return True if we haven't set a specific language,
    which means show to all languages.
    """
    if promo.programming_language:
        return programming_language == promo.programming_language
    return True


def choose_promo(promo_list):
    """
    This is the algorithm to pick which promo to show.

    This takes into account how many remaining days this
    promo has to be shown.

    The algorithm is currently as such:

    * Take the remaining number of views each promo has today
    * Add them together, with each promo "assigned" to a range
    * Pick a random number between 1 and that total
    * Choose the ad whose range is in the chosen random number

    In the future,
    we should take into account the expected views for today
    (The number of views from this day last week)
    Then we can scale the "total ads sold" against that "expected views",
    and that will give us more spread throughout the day.

    """
    promo_range = []
    total_views_needed = 0
    for promo in promo_list:
        promo_range.append([
            total_views_needed,
            total_views_needed + promo.views_needed_today(),
            promo
        ])
        total_views_needed += promo.views_needed_today()
    choice = random.randint(0, total_views_needed)
    for range_list in promo_range:
        if range_list[0] <= choice <= range_list[1]:
            return range_list[2]
    return None


def get_promo(country_code, programming_language, theme,
              gold_project=False, gold_user=False, community_only=False):
    """
    Get a proper promo.

    Takes into account:

    * Gold User status
    * Gold Project status
    * Geo
    * Programming Language

    """
    promo_queryset = SupporterPromo.objects.filter(live=True, display_type='doc')

    if community_only:
        promo_queryset = promo_queryset.filter(community=True)

    filtered_promos = []
    for promo in promo_queryset:
        # Break out if we aren't meant to show to this language
        if promo.programming_language and not show_to_programming_language(promo, programming_language):  # noqa
            continue
        # Break out if we aren't meant to show to this country
        if country_code and not show_to_geo(promo, country_code):
            continue
        # Don't show if the theme doesn't match
        if promo.theme not in ['any', theme]:
            continue
        # If we haven't bailed because of language or country, possibly show the promo
        filtered_promos.append(promo)

    promo_obj = choose_promo(filtered_promos)

    # Show a random house ad if we don't have anything else
    if not promo_obj:
        house_promo = SupporterPromo.objects.filter(live=True,
                                                    name='house').order_by('?')
        if house_promo.exists():
            promo_obj = house_promo.first()

    # Support showing a "Thank you" message for gold folks
    if gold_user:
        gold_promo = SupporterPromo.objects.filter(live=True,
                                                   name='gold-user')
        if gold_promo.exists():
            promo_obj = gold_promo.first()

    # Default to showing project-level thanks if it exists
    if gold_project:
        gold_promo = SupporterPromo.objects.filter(live=True,
                                                   name='gold-project')
        if gold_promo.exists():
            promo_obj = gold_promo.first()

    return promo_obj


def is_gold_user(user):
    """Return True if the user is a Gold supporter."""
    return user.is_authenticated() and (
        user.gold.count() or
        user.goldonce.count()
    )


def is_gold_project(project):
    """Return True if the project has been mapped by a Gold supporter."""
    return project.gold_owners.count()


def is_community_only(user, project):
    """Return True is this project or user should only be shown community ads"""
    if user.is_authenticated() and not user.profile.allow_ads:
        return True
    if not project.allow_promos:
        return True
    return False


def get_user_country(request):
    """Return the ISO country code from geo-IP data, or None if not found."""
    if not PROMO_GEO_PATH:
        return None
    ip = request.META.get('REMOTE_ADDR')
    if not ip:
        return None
    try:
        geo_response = geo_reader.city(ip)
        return geo_response.country.iso_code
    except (AddressNotFoundError, ValueError):  # Invalid IP
        return None


@receiver(footer_response)
def attach_promo_data(sender, request, context, resp_data, **__):
    """Insert promotion data keys into the footer API response."""
    del sender  # unused

    project = context['project']
    theme = context['theme']

    if getattr(settings, 'USE_PROMOS', True):
        promo = lookup_promo(request, project, theme)
    else:
        promo = None

    if promo:
        resp_data.update({
            'promo': True,
            'promo_data': promo,
        })
    else:
        resp_data['promo'] = False


def lookup_promo(request, project, theme):
    """Look up a promo to show for the given project.

    Return a dict of promo_data for inclusion in the footer response, or None
    if no promo should be shown.

    """
    gold_user = is_gold_user(request.user)
    gold_project = is_gold_project(project)
    community_only = is_community_only(request.user, project)

    # Don't show promos to gold users or on gold projects for now
    # (Some day we may show them something customised for them)
    if gold_user or gold_project:
        return None

    promo_obj = get_promo(
        country_code=get_user_country(request),
        programming_language=project.programming_language,
        theme=theme,
        gold_project=gold_project,
        gold_user=gold_user,
        community_only=community_only,
    )

    # If we don't have anything to show, don't show it.
    if not promo_obj:
        return None

    return offer_promo(
        promo_obj=promo_obj,
        project=project
    )


@receiver(footer_response)
def index_theme_data(sender, **kwargs):
    """
    Keep track of which projects are using which theme.

    This is primarily used so we can send email to folks using alabaster,
    and other themes we might want to display ads on.
    This will allow us to give people fair warning before we put ads on their docs.

    """
    del sender  # unused
    context = kwargs['context']

    project = context['project']
    theme = context['theme']

    try:
        redis_client = cache.get_client(None)
        redis_client.sadd("readthedocs:v1:index:themes:%s" % theme, project.slug)
    except (AttributeError, redis.exceptions.ConnectionError):
        log.warning('Redis theme indexing error: %s', exc_info=True)
