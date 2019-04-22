import time

from client import api
from utils import p


# Get specific project by slug
p(api.projects('test-builds').get())
input('Press Enter to continue...')

# Get specific project by slug full expanded
# (all active versions with each last build object and its configuration)
p(api.projects('test-builds').get(
    expand='active_versions,active_versions.last_build,active_versions.last_build.config',
))
input('Press Enter to continue...')


# Get all active and built versions for a project selecting only needed fields:
# slug, urls, downloads
# (useful to create the versions menu on a theme)
p(api.projects('test-builds').versions.get(
    expand='last_build',
    fields='slug,urls,downloads',
    active=True,
    built=True,  # filtering by built we avoid ending up with 404 links
))
input('Press Enter to continue...')

# Get all running builds for a project
# (useful for a status page of the project)
p(api.projects('test-builds').builds.get(
    running=True,
))
input('Press Enter to continue...')

# Get all running builds for specific version of a project
p(api.projects('test-builds').versions('latest').builds.get(
    running=True,
))
input('Press Enter to continue...')


# trigger a build of default version and poll the status
# (useful on the release process to check that docs build before publishing)
# response = api.projects('test-builds').builds().post()

# Trigger a build for a specific version
response = api.projects('test-builds').versions('use-py2').builds().post()
p(response)
if response['triggered']:
    finished = response['build']['finished']
    build_id = response['build']['id']
    project_slug = response['project']['slug']
    build_url = response['build']['links']['_self']

    while not finished:
        time.sleep(5)
        # NOTE: I already have the url for this on ``build_url`` but as I'm
        # using slumber which already have the Authorization header, I don't
        # know how to hit it directly and I need to rebuilt it here (this is a
        # limitation of the client, not of API design)
        response = api.projects(project_slug).builds(build_id).get()
        state = response['state']['code']
        finished = response['finished']
        print(f'Current state: {state}')
    print('Finished')

input('Press Enter to continue...')


# Activate and make private a specific version of a project
# NOTE: slumber can't be used here since ``.patch`` send the data in the URL
api._store['session'].patch(
    api.projects('test-builds').versions('submodule-https-scheme').url(),
    data=dict(
        active=True,
        privacy_level='private',
    ),
)
input('Press Enter to continue...')
