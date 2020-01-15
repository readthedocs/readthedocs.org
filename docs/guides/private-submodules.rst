Using Private Git Submodules with Read the Docs for Business
============================================================

Read the Docs uses SSH keys (with read only permissions) in order to clone private repositories.
An SSH key is automatically generated and setup for your main repository, but not for your submodules.
You'll need to use that SSH key in all the repositories of your submodules.

.. note::

   You can manage which submodules Read the Docs should clone using a configuration file.
   See :ref:`config-file/v2:submodules`.

GitHub
------

For GitHub, Read the Docs uses `deploy keys with read only access <https://developer.github.com/v3/guides/managing-deploy-keys/#deploy-keys>`__.
For security reasons, GitHub doesn't allow you to reuse the same SSH key across different repositories.
But you can use `machine users <https://developer.github.com/v3/guides/managing-deploy-keys/#machine-users>`__
to give read access to several repositories using only one SSH key.

- Remove the SSH deploy key that was added to the main repository on GitHub

  - Go to the settings tab of project on GitHub
  - Click on :guilabel:`Deploy Keys`
  - Delete the key added by ``Read the Docs Commercial (readthedocs.com)``

- Create a GitHub user and give it read only permissions to all the necessary repositories.
  You can do this by adding the account
  as a `collaborator <https://help.github.com/en/github/setting-up-and-managing-your-github-user-account/inviting-collaborators-to-a-personal-repository>`__,
  as an `outside collaborator <https://help.github.com/en/github/setting-up-and-managing-organizations-and-teams/adding-outside-collaborators-to-repositories-in-your-organization>`__,
  or to a `team in an organization <https://help.github.com/en/github/setting-up-and-managing-organizations-and-teams/adding-organization-members-to-a-team>`__.
- Get the public SSH key from your Read the Docs project

  - Go to the :guilabel:`Admin` tab of your project
  - Click on ``SSH Keys``
  - Click on the fingerprint of the SSH key (it looks like ``6d:ca:6d:ca:6d:ca:6d:ca``)
  - Copy the content of the public SSH key 

- Attach the public SSH key to the GitHub user you just created

  - Go to the user's settings
  - Click :guilabel:`SSH and GPG keys`
  - Click :guilabel:`New SSH key`
  - Put a descriptive title and paste the public SSH key from the previous step
  - Click :guilabel:`Add SSH key`

Refer to the `GitHub documentation <https://developer.github.com/v3/guides/managing-deploy-keys/#machine-users>`__ for more information about machine users.

GitLab
------

Bitbucket
---------

Others
------

If you are not using any of the above integrations.
