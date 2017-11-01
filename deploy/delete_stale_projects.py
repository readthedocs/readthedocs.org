import shutil
import os

from readthedocs.projects.models import Project

all_slugs = set([p.slug for p in Project.objects.all().iterator()])
json_projects = set(os.listdir('/home/docs/checkouts/readthedocs.org/media/json/'))
build_projects = set(os.listdir('/home/docs/checkouts/readthedocs.org/user_builds/'))
combined_ondisk_projects = json_projects + build_projects

final = []
for count, slug in enumerate(combined_ondisk_projects):
    if slug not in all_slugs and slug.replace('_', '-') not in all_slugs:
        final.append(slug)
    if count % 100 == 0:
        print(count)

print "To delete: %s" % len(final)

for count, to_del in enumerate(final):
    root = '/home/docs/checkouts/readthedocs.org'
    print "Deleting " + to_del
    shutil.rmtree('{root}/user_builds/{slug}'.format(root=root, slug=to_del), ignore_errors=True)
    shutil.rmtree('{root}/media/pdf/{slug}'.format(root=root, slug=to_del), ignore_errors=True)
    shutil.rmtree('{root}/media/epub/{slug}'.format(root=root, slug=to_del), ignore_errors=True)
    shutil.rmtree('{root}/media/json/{slug}'.format(root=root, slug=to_del), ignore_errors=True)
    shutil.rmtree('{root}/media/man/{slug}'.format(root=root, slug=to_del), ignore_errors=True)
    shutil.rmtree('{root}/media/htmlzip/{slug}'.format(root=root, slug=to_del), ignore_errors=True)
    if count % 100 == 0:
        print(count)
