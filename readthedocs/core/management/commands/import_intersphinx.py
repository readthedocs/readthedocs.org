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
            try:
                inv = fetch_inventory(app, app.srcdir, 'objects.inv')
            except TypeError:
                print "Failed to fetch inventory for %s" % version
                continue
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
                        url = "http://%s.readthedocs.org/en/latest/%s" % (version.project.slug, url)
                        self.save_term(version, term, url, title)
                        if '.' in term:
                            self.save_term(version, term.split('.')[-1], url, title)
                    except: #Yes, I'm an evil person.
                        print "*** Failed updating %s" % term


    def save_term(self, version, term, url, title):
        print "Inserting %s: %s" % (term, url)
        lang = "en"
        project_slug = version.project.slug
        version_slug = version.slug
        r.sadd('redirects:v3:%s:%s:%s:%s' % (lang, project_slug,
                                             version_slug, term), url)
        r.setnx('redirects:v3:%s:%s:%s:%s:%s' % (lang, project_slug,
                                                 version_slug, term, url), 1)
