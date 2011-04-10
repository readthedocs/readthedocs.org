class DictObj(object):
    def __getattr__(self, attr):
        return self.__dict__.get(attr)

from sphinx.ext.intersphinx import fetch_inventory
from django.core.management.base import BaseCommand
from django.conf import settings
from optparse import make_option
import redis

from projects.models import Project
from builds.models import Version
from projects.tasks import update_docs

r = redis.Redis(**settings.REDIS)

class Command(BaseCommand):
    def handle(self, *args, **options):
        for version in Version.objects.filter(slug="latest"):
            path = version.project.rtd_build_path(version.slug)
            if not path:
                print "ERR: %s has no path" % version
                continue
            app = DictObj()
            app.srcdir = path
            inv = fetch_inventory(app, app.srcdir, 'objects.inv')
            # I'm entirelty not sure this is even close to correct.
            # There's a lot of info I'm throwing away here; revisit later?
            for keytype in inv:
                for term in inv[keytype]:
                    try:
                        _, _, url, title = inv[keytype][term]
                        if not title or title == '-':
                            if '#' in url:
                                title = url.rsplit('#')[-1]
                            else:
                                title = url
                        find_str = "rtd-builds/latest"
                        latest = url.find(find_str)
                        url = url[latest + len(find_str) + 1:]
                        self.save_term(version, term, url, title)
                        if '.' in term:
                            self.save_term(version, term.split('.')[-1], url, title)
                    except: #Yes, I'm an evil person.
                        print "*** Failed updating %s" % term


    def save_term(self, version, term, url, title):
        print "Inserting %s: %s" % (term, url)
        r.sadd('redirects:v2:%s:%s' % (version, term), url)
        r.setnx('redirects:v2:%s:%s:%s' % (version, term, url), 1)
        r.set('redirects:v2:titles:%s' % (url,), title)
