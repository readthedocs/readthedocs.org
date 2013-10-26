import re


REGEX1 = re.compile('github.com/(.+)/(.+)(?:\.git){1}')
REGEX2 = re.compile('github.com/(.+)/(.+)')
REGEX3 = re.compile('github.com:(.+)/(.+).git')


def get_github_username_repo(version):
    repo_url = version.project.repo
    if 'github' in repo_url:
        match = REGEX1.search(repo_url)
        if match:
            return match.groups()
        match = REGEX2.search(repo_url)
        if match:
            return match.groups()
        match = REGEX3.search(repo_url)
        if match:
            return match.groups()
    return (None, None)


def get_github_version(version):
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
