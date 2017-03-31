import random

from django.dispatch import receiver
from django.conf import settings

from readthedocs.restapi.signals import footer_response
from readthedocs.donate.models import SupporterPromo
from readthedocs.donate.constants import INCLUDE, EXCLUDE
from readthedocs.donate.utils import offer_promo


PROMO_GEO_PATH = getattr(settings, 'PROMO_GEO_PATH', None)

if PROMO_GEO_PATH:
    import geoip2.database  # noqa
    from geoip2.errors import AddressNotFoundError  # noqa
    geo_reader = geoip2.database.Reader(PROMO_GEO_PATH)


def show_to_geo(promo, country_code):
    # Remove promo's that exclude this country.
    for filter in promo.geo_filters.all():
        if filter.filter_type == INCLUDE:
            if country_code in filter.codes:
                continue
            else:
                return False
        if filter.filter_type == EXCLUDE:
            if country_code in filter.codes:
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


def get_promo(country_code, programming_language, gold_project=False, gold_user=False):
    """
    Get a proper promo.

    Takes into account:

    * Gold User status
    * Gold Project status
    * Geo
    * Programming Language
    """

    promo_queryset = SupporterPromo.objects.filter(live=True, display_type='doc')

    filtered_promos = []
    for obj in promo_queryset:
        # Break out if we aren't meant to show to this language
        if obj.programming_language and not show_to_programming_language(obj, programming_language):
            continue
        # Break out if we aren't meant to show to this country
        if country_code and not show_to_geo(obj, country_code):
            continue
        # If we haven't bailed because of language or country, possibly show the promo
        filtered_promos.append(obj)

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


@receiver(footer_response)
def attach_promo_data(sender, **kwargs):
    request = kwargs['request']
    context = kwargs['context']
    resp_data = kwargs['resp_data']

    project = context['project']

    # Bail out early if promo's are disabled.
    use_promo = getattr(settings, 'USE_PROMOS', True)
    if not use_promo:
        resp_data['promo'] = False
        return

    gold_user = gold_project = False
    promo_obj = country_code = None

    show_promo = project.allow_promos

    # The request is by a GoldUser
    if request.user.is_authenticated():
        if request.user.gold.count() or request.user.goldonce.count():
            gold_user = True

    # A GoldUser has mapped this project
    if project.gold_owners.count():
        gold_project = True

    # Don't show gold users promos.
    # This will get overridden if we have specific promos for them below.
    if gold_user or gold_project:
        show_promo = False

    if PROMO_GEO_PATH:
        # Get geo information from the IP, but don't record it anywhere
        ip = request.META.get('REMOTE_ADDR')
        if ip:
            try:
                geo_response = geo_reader.city(ip)
                country_code = geo_response.country.iso_code
            except (AddressNotFoundError, ValueError):  # Invalid IP
                country_code = None

    # Try to get a promo if we should be using one.
    if show_promo:
        promo_obj = get_promo(
            country_code=country_code,
            programming_language=project.programming_language,
            gold_project=gold_project,
            gold_user=gold_user,
        )

    # If we don't have anything to show, don't show it.
    if not promo_obj:
        show_promo = False

    if show_promo:
        promo_dict = offer_promo(promo_obj=promo_obj, project=project)
        resp_data['promo_data'] = promo_dict

    # Set promo object on return JSON
    resp_data['promo'] = show_promo
