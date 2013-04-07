import redis
import itertools
import operator
import urlparse

from django import forms
from django import http
from django.conf import settings
from django.shortcuts import render
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _

r = redis.Redis(**settings.REDIS)


class RedirectForm(forms.Form):
    _domain = 'readthedocs.org'

    url = forms.URLField(label='URL')
    title = forms.CharField(label='Title', required=False)

    def clean_url(self):
        url = urlparse.urlparse(self.cleaned_data['url'])
        if self._domain not in url.netloc:
            raise forms.ValidationError(_('Please enter a valid URL on %s') %
                                        self._domain)
        return self.cleaned_data['url']


def redirect_home(request, version):
    return http.HttpResponseRedirect('http://%s.readthedocs.org'
                                     % request.slug)


def redirect_to_term(request, version, term):
    form = RedirectForm(request.GET or None)

    project = request.slug
    lang = "en"
    # If we're explicitly choosing a new URL for this term, just go ahead and
    # do that. This could also insert new URLs, so do a brief sanity check to
    # make sure this service can't be used for spam.
    if 'url' in request.GET:
        if form.is_valid():
            # Make sure the new URL is in the set of URLs and increment its
            # score.
            url = form.cleaned_data['url']
            r.sadd('redirects:v4:%s:%s:%s:%s' % (lang, version, project, term),
                   url)
            r.incr('redirects:v4:%s:%s:%s:%s:%s' % (lang, version, project,
                                                    term, url))
            return redirect(request.GET.get('return_to', url))

    urls = get_urls(lang, project, version, term)
    if urls:
        scoregroups = group_urls(urls)

        # The first group is the URLs with the highest score.
        _, winners = scoregroups.next()

        # If there's only a single winning URL, we're done. Count the redirect
        # and then issue it.
        if len(winners) == 1:
            url = winners[0]
            r.incr('redirects:v4:%s:%s:%s:%s:%s' % (lang, version, project,
                                                    term, url))
            return redirect(url)

        # Otherwise we need to display a list of all choices. We'll present
        # this into two buckets: the tied URLs with the high score (which is
        # the list of winners we've already gotten) and the tied URLs with a
        # lower score. This second bucket might be empty.
        losers = [losing_group for score, losing_group in scoregroups]

    else:
        winners = losers = None

    return render(request, 'djangome/choices.html', {
        'djangome_term': term,
        'winners': winners,
        'losers': losers,
        'form': form,
        'version': version,
    })


def show_term(request, version, term):
    return render(request, 'djangome/show.html', {
        'djangome_term': term,
        'version': version,
        'urls': get_urls(version, term),
        'can_edit': request.COOKIES.get('sekrit') == settings.SECRET_KEY,
    })


def get_urls(lang, project, version, term):
    """
    Gets the set of URLs for <term> in <version>.

    Returns a list of (score, url) tuples, sorted by score descending.
    """
    # Sort the set of URLs in redirects:v1:term by the scores (clicks) in
    # redirects:v1:term:url, then get each score along with each URL.
    # This returns a list [score, url, score, url, ...]
    urls = r.sort('redirects:v4:%s:%s:%s:%s' % (lang, version, project, term),
                  by='redirects:v4:%s:%s:%s:%s:*' % (lang, version,
                                                     project, term),
                  get=('redirects:v4:%s:%s:%s:%s:*' % (lang, version,
                                                       project, term), '#'),
                  desc=True)

    # Convert that to a list of tuples [(score, url), (score, url), ...]
    return zip(urls[::2], urls[1::2])


def group_urls(urls):
    """
    Given a list of (score, url) tuples, group them into buckets by score.

    Returns a list of (score, list_of_urls) tuples.
    """
    for (score, group) in itertools.groupby(urls, operator.itemgetter(0)):
        yield (score, [url for score, url in group])


def firstof(list):
    for i in list:
        if i:
            return i
