import re

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

def get_github_username_repo(version):
    repo_url = version.project.repo
    if 'github' in repo_url:
        for regex in GH_REGEXS:
            match = regex.search(repo_url)
            if match:
                return match.groups()
    return (None, None)

def get_bitbucket_username_repo(version):
    repo_url = version.project.repo
    if 'bitbucket' in repo_url:
        for regex in BB_REGEXS:
            match = regex.search(repo_url)
            if match:
                return match.groups()
    return (None, None)

def get_vcs_version(version):
    if version.slug == 'latest':
        if version.project.default_branch:
            return version.project.default_branch
        else:
            return version.project.vcs_repo().fallback_branch
    else:
        return version.slug

def get_conf_py_path(version):
    conf_py_path = version.project.conf_file(version.slug)
    conf_py_path = conf_py_path.replace(
        version.project.checkout_path(version.slug), '')
    return conf_py_path.replace('conf.py', '')
