import shutil
import os

from readthedocs.projects.models import Project

slugs = [p.slug for p in Project.objects.all()]
build_projects = os.listdir('/home/docs/checkouts/readthedocs.org/user_builds/')

final = []
for slug in build_projects:
    if slug not in slugs and slug.replace('_', '-') not in slugs:
        final.append(slug)

print "To delete: %s" % len(final)

for to_del in final:
    root = '/home/docs/checkouts/readthedocs.org'
    print "Deleting " + to_del
    shutil.rmtree('{root}/user_builds/{slug}'.format(root=root, slug=to_del), ignore_errors=True)
    shutil.rmtree('{root}/media/pdf/{slug}'.format(root=root, slug=to_del), ignore_errors=True)
    shutil.rmtree('{root}/media/epub/{slug}'.format(root=root, slug=to_del), ignore_errors=True)
    shutil.rmtree('{root}/media/json/{slug}'.format(root=root, slug=to_del), ignore_errors=True)
    shutil.rmtree('{root}/media/man/{slug}'.format(root=root, slug=to_del), ignore_errors=True)
    shutil.rmtree('{root}/media/htmlzip/{slug}'.format(root=root, slug=to_del), ignore_errors=True)
