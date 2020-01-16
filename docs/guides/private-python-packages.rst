Using Private Python Packages with Read the Docs for Business
=============================================================

Read the Docs uses :doc:`PIP <pip:index>` to install your Python packages,
see :doc:`/guides/specifying-dependencies`.

Installing packages from a Git repository
-----------------------------------------

PIP supports installing packages from a :ref:`Git repository <pip:vcs support>` using the form:

.. code::
   
   git+https://gitprovider.com/user/project.git@{version}#egg={package-name}

Where ``version`` can be a tag, a branch, or a commit.

If your repository is private you need to use the form:

.. code::
   
   git+https://{token}@gitprovider.com/user/project.git@{version}#egg={package-name}

Where ``token`` is a personal access token with read only permissions from your provider.
Below you can find the steps to get a personal token from our supported providers.

.. We should add the git+ssh form when we support running the ssh-agent in the build step.

.. note::
   
   The URI should be in your :ref:`requirements file <config-file/v2:Requirements file>`.

GitHub
~~~~~~

If you are using GitHub,
you need to create a personal access token with the ``repo`` scope.
Check the `GitHub documentation <https://help.github.com/en/github/authenticating-to-github/creating-a-personal-access-token-for-the-command-line#creating-a-token>`__
on how to create a personal token.

URI example:

.. code::
   
   git+https://{token}@github.com/user/project.git@{version}#egg={package-name}

.. warning::

   GitHub doesn't support tokens per repository.
   A personal token will grant read and write access to all repositories the user has access to.
   You can create a `machine user <https://developer.github.com/v3/guides/managing-deploy-keys/#machine-users>`__
   to give read access only to the repositories you need.

GitLab
~~~~~~

If you are using GitLab,
you need to create a deploy token with the ``read_repository`` scope for the repository you want to install the package from.
Check the `GitLab documentation <https://docs.gitlab.com/ee/user/project/deploy_tokens/#creating-a-deploy-token>`__
on how to create a deploy token.

URI example:

.. code::
   
   git+https://{user}:{token}@gitlab.com/user/project.git@{version}#egg={package-name}

Here ``user`` is the user from the deploy token you created, not  your GitLab user.

Bitbucket
~~~~~~~~~

Create an app password with ``Read repositories`` permissions.
Check the `Bitbucket documentation <https://confluence.atlassian.com/bitbucket/app-passwords-828781300.html>`__
on how to create an app password.

URI example:

.. code::
   
   git+https://{user}:{app-password}@bitbucket.org/user/project.git@{version}#egg={package-name}'

Here ``user`` is your Bitbucket user.

.. warning::

   Bitbucket doesn't support app passwords per repository.
   An app password will grant read access to all repositories the user has access to.

Installing packages from a repository manager other than PyPI
-------------------------------------------------------------

Environment variables
~~~~~~~~~~~~~~~~~~~~~

Using a ``pip.conf`` file
~~~~~~~~~~~~~~~~~~~~~~~~~

Using a requirements file
~~~~~~~~~~~~~~~~~~~~~~~~~
