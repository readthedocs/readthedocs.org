"""Utility functions for use in tests."""

import subprocess
import textwrap
from os import chdir, environ, mkdir
from os.path import abspath
from os.path import join as pjoin
from shutil import copytree
from tempfile import mkdtemp

import structlog
from django.contrib.auth.models import User
from django_dynamic_fixture import new
from djstripe.models import APIKey

from readthedocs.doc_builder.base import restoring_chdir

log = structlog.get_logger(__name__)


def get_readthedocs_app_path():
    """Return the absolute path of the ``readthedocs`` app."""

    try:
        import readthedocs

        path = readthedocs.__path__[0]
    except (IndexError, ImportError):
        raise Exception('Unable to find "readthedocs" path module')

    return path


def check_output(command, env=None):
    output = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    ).communicate()[0]
    log.info(output)
    return output


@restoring_chdir
def make_test_git():
    directory = mkdtemp()
    directory = make_git_repo(directory)
    env = environ.copy()
    env["GIT_DIR"] = pjoin(directory, ".git")
    chdir(directory)

    # Add fake repo as submodule. We need to fake this here because local path
    # URL are not allowed and using a real URL will require Internet to clone
    # the repo
    check_output(["git", "checkout", "-b", "submodule", "master"], env=env)
    add_git_submodule_without_cloning(
        directory,
        "foobar",
        "https://foobar.com/git",
    )
    check_output(["git", "add", "."], env=env)
    check_output(["git", "commit", '-m"Add submodule"'], env=env)

    # Add an invalid submodule URL in the invalidsubmodule branch
    check_output(["git", "checkout", "-b", "invalidsubmodule", "master"], env=env)
    add_git_submodule_without_cloning(
        directory,
        "invalid",
        "git@github.com:rtfd/readthedocs.org.git",
    )
    check_output(["git", "add", "."], env=env)
    check_output(["git", "commit", '-m"Add invalid submodule"'], env=env)

    # Checkout to master branch again
    check_output(["git", "checkout", "master"], env=env)

    # Add something unique to the master branch (so we can verify it's correctly checked out)
    open("only-on-default-branch", "w").write(
        "This file only exists in the default branch"
    )
    check_output(["git", "add", "only-on-default-branch"], env=env)
    check_output(
        ["git", "commit", '-m"Add something unique to master branch"'], env=env
    )

    return directory


@restoring_chdir
def add_git_submodule_without_cloning(directory, submodule, url):
    """
    Add a submodule without cloning it.

    We write directly to the git index, more details in:
    https://stackoverflow.com/a/37378302/2187091

    :param directory: The directory where the git repo is
    :type directory: str
    :param submodule: The name of the submodule to be created
    :type submodule: str
    :param url: The url where the submodule points to
    :type url: str
    """
    env = environ.copy()
    env["GIT_DIR"] = pjoin(directory, ".git")
    chdir(directory)

    mkdir(pjoin(directory, submodule))
    gitmodules_path = pjoin(directory, ".gitmodules")
    with open(gitmodules_path, "w+") as fh:
        content = textwrap.dedent(
            """
            [submodule "{submodule}"]
                path = {submodule}
                url = {url}
        """
        )
        fh.write(content.format(submodule=submodule, url=url))
    check_output(
        [
            "git",
            "update-index",
            "--add",
            "--cacheinfo",
            "160000",
            "233febf4846d7a0aeb95b6c28962e06e21d13688",
            submodule,
        ],
        env=env,
    )


@restoring_chdir
def make_git_repo(directory, name="sample_repo"):
    path = get_readthedocs_app_path()
    sample = abspath(pjoin(path, "rtd_tests/fixtures/sample_repo"))
    directory = pjoin(directory, name)
    copytree(sample, directory)
    env = environ.copy()
    env["GIT_DIR"] = pjoin(directory, ".git")
    chdir(directory)

    # Initialize and configure
    check_output(["git", "init"] + [directory], env=env)
    check_output(
        ["git", "config", "user.email", "dev@readthedocs.org"],
        env=env,
    )
    check_output(
        ["git", "config", "user.name", "Read the Docs"],
        env=env,
    )

    # Set up the actual repository
    check_output(["git", "add", "."], env=env)
    check_output(["git", "commit", '-m"init"'], env=env)
    return directory


@restoring_chdir
def create_git_tag(directory, tag, annotated=False):
    env = environ.copy()
    env["GIT_DIR"] = pjoin(directory, ".git")
    chdir(directory)

    command = ["git", "tag"]
    if annotated:
        command.extend(["-a", "-m", "Some tag"])
    command.append(tag)
    check_output(command, env=env)


@restoring_chdir
def delete_git_tag(directory, tag):
    env = environ.copy()
    env["GIT_DIR"] = pjoin(directory, ".git")
    chdir(directory)

    command = ["git", "tag", "--delete", tag]
    check_output(command, env=env)


@restoring_chdir
def create_git_branch(directory, branch):
    env = environ.copy()
    env["GIT_DIR"] = pjoin(directory, ".git")
    chdir(directory)

    command = ["git", "branch", branch]
    check_output(command, env=env)


@restoring_chdir
def get_git_latest_commit_hash(directory, branch):
    env = environ.copy()
    env["GIT_DIR"] = pjoin(directory, ".git")
    chdir(directory)

    command = ["git", "rev-parse", branch]
    return check_output(command, env=env).decode().strip()


@restoring_chdir
def delete_git_branch(directory, branch):
    env = environ.copy()
    env["GIT_DIR"] = pjoin(directory, ".git")
    chdir(directory)

    command = ["git", "branch", "-D", branch]
    check_output(command, env=env)


@restoring_chdir
def create_git_submodule(
    directory,
    submodule,
    msg="Add realative submodule",
    branch="master",
):
    env = environ.copy()
    env["GIT_DIR"] = pjoin(directory, ".git")
    chdir(directory)

    command = ["git", "branch", "-D", branch]
    check_output(command, env=env)
    command = ["git", "submodule", "add", "-b", branch, "./", submodule]
    check_output(command, env=env)
    check_output(["git", "add", "."], env=env)
    check_output(["git", "commit", "-m", '"{}"'.format(msg)], env=env)


@restoring_chdir
def get_current_commit(directory):
    env = environ.copy()
    env["GIT_DIR"] = pjoin(directory, ".git")
    chdir(directory)

    command = ["git", "rev-parse", "HEAD"]
    return check_output(command, env=env).decode().strip()


def create_user(username, password, **kwargs):
    user = new(User, username=username, **kwargs)
    user.set_password(password)
    user.save()
    return user
