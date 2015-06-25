import re
import logging
from shutil import rmtree


log = logging.getLogger(__name__)


GH_REGEXS = [
    re.compile('github.com/(.+)/(.+)(?:\.git){1}'),
    re.compile('github.com/(.+)/(.+)'),
    re.compile('github.com:(.+)/(.+).git'),
]

BB_REGEXS = [
    re.compile('bitbucket.org/(.+)/(.+)/'),
    re.compile('bitbucket.org/(.+)/(.+)'),
    re.compile('bitbucket.org:(.+)/(.+)\.git'),
]


def get_github_username_repo(url):
    if 'github' in url:
        for regex in GH_REGEXS:
            match = regex.search(url)
            if match:
                return match.groups()
    return (None, None)


def get_bitbucket_username_repo(url=None):
    if 'bitbucket' in url:
        for regex in BB_REGEXS:
            match = regex.search(url)
            if match:
                return match.groups()
    return (None, None)


def clean_build_path(version):
    '''Clean build path for project version

    Ensure build path is clean for project version. Used to ensure stale build
    checkouts for each project version are removed.

    version
        Instance of :py:class:`readthedocs.builds.models.Version` to perform
        build path cleanup on
    '''
    try:
        path = version.get_build_path()
        if path is not None:
            log.debug('Removing build path {0} for {1}'.format(
                path, version))
            rmtree(path)
    except OSError:
        log.error('Build path cleanup failed', exc_info=True)
