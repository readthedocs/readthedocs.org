"""Customizations to Django Taggit."""
from allauth.socialaccount.models import SocialApp
from django.db.models import Count
from django.utils.text import slugify
import requests
from taggit.models import Tag
from taggit.utils import _parse_tags

from .constants import GITHUB_REGEXS


def rtd_parse_tags(tag_string):
    """
    Parses a string into its tags.

    - Lowercases all tags
    - Converts underscores to hyphens
    - Slugifies tags
    - Removes empty tags

    :see: https://django-taggit.readthedocs.io/page/custom_tagging.html
    :param tag_string: a delimited string of tags
    :return: a sorted list of tag strings
    """
    if tag_string:
        tag_string = tag_string.lower().replace('_', '-')

    tags = [slugify(tag) for tag in _parse_tags(tag_string)]
    return sorted([tag for tag in tags if tag])


def remove_unused_tags():
    """Removes all tags that have no corresponding items (projects)."""
    return Tag.objects.all().annotate(
        num=Count('taggit_taggeditem_items')
    ).filter(num=0).delete()


def import_tags(project):
    """
    Import tags using the version control API.

    Currently, this is only implemented for github.
    Uses the client ID and client secret for github otherwise the rate limit is 60/hr.
    https://developer.github.com/v3/#rate-limiting

    :returns: A list of the tags set or ``None`` on an error
    """
    user = repo = ''
    for regex in GITHUB_REGEXS:
        match = regex.search(project.repo)
        if match:
            user, repo = match.groups()
            break

    if not user:
        return None

    provider = SocialApp.objects.filter(provider='github').first()
    if not provider:
        return None

    # https://developer.github.com/v3/repos/#list-all-topics-for-a-repository
    url = 'https://api.github.com/repos/{user}/{repo}/topics'.format(
        user=user,
        repo=repo,
    )
    headers = {
        # Getting topics is a preview API and may change
        # It requires this custom Accept header
        'Accept': 'application/vnd.github.mercy-preview+json',
    }
    params = {
        'client_id': provider.client_id,
        'client_secret': provider.secret,
    }

    resp = requests.get(url, headers=headers, params=params)
    if resp.ok:
        tags = resp.json()['names']
        if tags:
            project.tags.set(*tags)
            return tags
        return []

    return None
