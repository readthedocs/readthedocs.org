Using Private Git Submodules
============================

.. warning::

   This guide is for :doc:`/commercial/index`.

Read the Docs uses SSH keys (with read only permissions) in order to clone private repositories.
A SSH key is automatically generated and added to your main repository, but not to your submodules.
In order to give Read the Docs access to clone your submodules you'll need to add the public SSH key to each repository of your submodules.

.. note::

   - You can manage which submodules Read the Docs should clone using a configuration file.
     See :ref:`config-file/v2:submodules`.

   - Make sure you are using ``SSH`` URLs for your submodules
     (``git@github.com:readthedocs/readthedocs.org.git`` for example)
     in your ``.gitmodules`` file, not ``http`` URLs.

.. contents:: Table of contents
   :local:
   :backlinks: none
   :depth: 2

GitHub
------

Since GitHub doesn't allow you to reuse a deploy key across different repositories,
you'll need to use `machine users <https://developer.github.com/v3/guides/managing-deploy-keys/#machine-users>`__
to give read access to several repositories using only one SSH key.

#. Remove the SSH deploy key that was added to the main repository on GitHub

   #. Go to your project on GitHub
   #. Click on :guilabel:`Settings`
   #. Click on :guilabel:`Deploy Keys`
   #. Delete the key added by ``Read the Docs Commercial (readthedocs.com)``

#. Create a GitHub user and give it read only permissions to all the necessary repositories.
   You can do this by adding the account as:

   - A `collaborator <https://help.github.com/en/github/setting-up-and-managing-your-github-user-account/inviting-collaborators-to-a-personal-repository>`__
   - An `outside collaborator <https://help.github.com/en/github/setting-up-and-managing-organizations-and-teams/adding-outside-collaborators-to-repositories-in-your-organization>`__
   - A `team in an organization <https://help.github.com/en/github/setting-up-and-managing-organizations-and-teams/adding-organization-members-to-a-team>`__

#. Attach the public SSH key from your project on Read the Docs to the GitHub user you just created

   #. Go to the user's settings
   #. Click on :guilabel:`SSH and GPG keys`
   #. Click on :guilabel:`New SSH key`
   #. Put a descriptive title and paste the
      :ref:`public SSH key from your Read the Docs project <guides/importing-private-repositories:copy your project's public key>`
   #. Click on :guilabel:`Add SSH key`

Azure DevOps
------------

Azure DevOps does not have per-repository SSH keys, but keys can be added to a user instead.
As long as this user has access to your main repository and all its submodules,
Read the Docs can clone all the repositories with the same key.

.. seealso::

   :ref:`Allow access to your Azure DevOps repository with an SSH key <guides/importing-private-repositories:azure devops>`.

Others
------

GitLab and Bitbucket allow you to reuse the same SSH key across different repositories.
Since Read the Docs already added the public SSH key on your main repository,
you only need to add it to each submodule repository.

.. seealso::

   :ref:`guides/importing-private-repositories:Giving access to your project with an SSH key`
