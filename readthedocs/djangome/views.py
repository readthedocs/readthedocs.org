import redis
import itertools
import operator
import urlparse

from django import forms
from django import http
from django.conf import settings
from django.shortcuts import render
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_view_exempt

r = redis.Redis(**settings.REDIS)

class RedirectForm(forms.Form):
    _domain = 'readthedocs.org'

    url = forms.URLField(label='URL')
    title = forms.CharField(label='Title', required=False)

    def clean_url(self):
        url = urlparse.urlparse(self.cleaned_data['url'])
        if self._domain not in url.netloc:
            raise forms.ValidationError('Please enter a valid URL on %s' % self._domain)
        return self.cleaned_data['url']

def redirect_home(request, version):
    return http.HttpResponseRedirect('http://%s.readthedocs.org' % request.slug)

def redirect_to_term(request, version, term):
    # Check for an admin oneoff first.
    oneoff_redirect = find_oneoff_redirect(version, term)
    if oneoff_redirect:
        return oneoff_redirect

    form = RedirectForm(request.GET or None)

    # If we're explicitly choosing a new URL for this term, just go ahead and
    # do that. This could also insert new URLs, so do a brief sanity check to
    # make sure this service can't be used for spam.
    if 'url' in request.GET:
        if form.is_valid():
            # Make sure the new URL is in the set of URLs and increment its score.
            url = form.cleaned_data['url']
            r.sadd('redirects:v2:%s:%s' % (version, term), url)
            r.incr('redirects:v2:%s:%s:%s' % (version, term, url))
            return redirect(request.GET.get('return_to', url))

    urls = get_urls(version, term)
    if urls:
        scoregroups = group_urls(urls)

        # The first group is the URLs with the highest score.
        score, winners = scoregroups.next()

        # If there's only a single winning URL, we're done. Count the redirect and
        # then issue it.
        if len(winners) == 1:
            url = winners[0]
            r.incr('redirects:v2:%s:%s:%s' % (version, term, url))
            return redirect(url)

        # Otherwise we need to display a list of all choices. We'll present this into
        # two buckets: the tied URLs with the high score (which is the list of winners
        # we've already gotten) and the tied URLs with a lower score. This second
        # bucket might be empty.
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

@csrf_view_exempt
def manage_oneoffs(request):
    """
    Manage the hard-coded one-offs. Admins only.
    """
    if request.COOKIES.get('sekrit') != settings.SECRET_KEY:
        return http.HttpResponseNotAllowed()

    if request.method == 'POST':
        if 'action' in request.POST:
            try:
                action, version, term, target = (request.POST['action'],
                                                 request.POST['version'],
                                                 request.POST['term'],
                                                 request.POST['target'])
            except KeyError:
                return redirect(manage_oneoffs)
            if action == 'add':
                add_oneoff(version, term, target)
            elif action == 'kill':
                kill_oneoff(version, term)
        return redirect(manage_oneoffs)

    keys = r.keys('redirects:v2:oneoffs:*')
    targets = r.mget(keys) if keys else []

    oneoffs = []
    for (k, target) in zip(keys, targets):
        k = k.replace('redirects:v2:oneoffs:', '')
        if ':' in k:
            version, term = k.split(':')
        else:
            version, term = None, k
        oneoffs.append((version, term, target))

    return render(request, 'djangome/oneoffs.html', {
        'oneoffs': oneoffs,
    })

def find_oneoff_redirect(version, term):
    """
    Find a one-off redirect for the given version/term.

    Returns an HttpResponseRedirect if the redirect was found, None otherwise.

    Increments a count of the found term if successful.
    """
    oneoff_keys = ['redirects:v2:oneoffs:%s' % term,
                   'redirects:v2:oneoffs:%s:%s' % (version, term)]
    oneoff_redirects = r.mget(oneoff_keys)
    for k, target in zip(oneoff_keys, oneoff_redirects):
        if target:
            r.incr('redirects:v2:%s:%s:%s' % (version, term, target))
            return redirect(target)
    return None

def add_oneoff(version, term, target):
    if version:
        k = 'redirects:v2:oneoffs:%s:%s' % (version, term)
    else:
        k = 'redirects:v2:oneoffs:%s' % term
    r.set(k, target)

def kill_oneoff(version, term):
    if version:
        k = 'redirects:v2:oneoffs:%s:%s' % (version, term)
    else:
        k = 'redirects:v2:oneoffs:%s' % term
    print "kill", k
    r.delete(k)

def get_urls(version, term):
    """
    Gets the set of URLs for <term> in <version>.

    Returns a list of (score, url) tuples, sorted by score descending.
    """
    # Sort the set of URLs in redirects:v1:term by the scores (clicks) in
    # redirects:v1:term:url, then get each score along with each URL.
    # This returns a list [score, url, score, url, ...]
    urls = r.sort('redirects:v2:%s:%s' % (version, term),
                  by   = 'redirects:v2:%s:%s:*' % (version, term),
                  get  = ('redirects:v2:%s:%s:*' % (version, term), '#'),
                  desc = True)

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
