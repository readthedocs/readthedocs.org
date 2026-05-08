Read the Docs tutorial for Docusaurus
=====================================

In this tutorial you will learn how to host a public `Docusaurus`_ documentation project on Read the Docs Community.
No prior experience with Docusaurus is required.

.. _Docusaurus: https://docusaurus.io/

.. note::

   Find out the `differences between Read the Docs Community and Read the Docs for Business <https://about.readthedocs.com/pricing/#/community>`_.

In the tutorial we will:

1. Import a Docusaurus project from a GitHub repository.
2. Tailor the project's configuration.
3. Explore pull request previews, the build summary comment, visual diff, and link previews.

If you don't have a GitHub account, you'll need to `register for a free account <https://github.com/signup>`_ before you start.

Preparing your repository on GitHub
-----------------------------------

#. `Sign in to GitHub <https://github.com/login>`_ and navigate to the `Docusaurus tutorial GitHub template <https://github.com/readthedocs/tutorial-docusaurus-template/>`_.

#. Click the green :guilabel:`Use this template` button, then click :guilabel:`Create a new Repository`. On the new page:

   Owner
      Leave the default, or change it to something suitable for a tutorial project.
   Repository name
      Something memorable and appropriate, for example ``docusaurus-tutorial``.
   Visibility
      Make sure the project is "Public", rather than "Private".

#. Click the green :guilabel:`Create repository` button to create a public repository that you will use in this Read the Docs tutorial, containing the following files:

   ``.readthedocs.yaml``
      Read the Docs configuration file. Required.

   ``README.md``
      Description of the repository.

   ``docs/``
      Directory holding the Docusaurus project, including
      ``package.json``, ``docusaurus.config.js``, ``sidebars.js``,
      and the Markdown source files under ``docs/pages/``.

Creating a Read the Docs account
--------------------------------

To create a Read the Docs account,
navigate to the `Sign Up page <https://app.readthedocs.org/accounts/signup/>`_
and choose the option :guilabel:`Sign up with GitHub` and then :guilabel:`Sign up using GitHub App`.

.. TODO: we need a way to install the GitHub App upfront before adding a project

Installing the Read the Docs GitHub App
---------------------------------------

For Read the Docs to access your ``docusaurus-tutorial`` repository,
install the `Read the Docs Community GitHub App <https://github.com/apps/read-the-docs-community>`_:

#. Open the GitHub App page and click :guilabel:`Install`.
#. Choose the GitHub account or organization that owns your ``docusaurus-tutorial`` repository.
#. Select :guilabel:`Only select repositories` and pick ``docusaurus-tutorial``. You can grant access to additional repositories at any time from your GitHub settings.
#. Click :guilabel:`Install` to complete the setup.

.. seealso::

   :ref:`reference/git-integration:GitHub App`
     Details on what the GitHub App can do and the permissions it requests.

Adding the project to Read the Docs
-----------------------------------

To add your GitHub project to Read the Docs:

#. Click the :guilabel:`Add project` button on your `dashboard <https://app.readthedocs.org/dashboard/>`_.

#. Search for your ``docusaurus-tutorial`` repository, select it, and click :guilabel:`Continue`.

#. Enter some details about your Read the Docs project:

   Name
      The name of the project, used to create a unique subdomain for each project.
      so it is better if you prepend your username,
      for example ``{username}-docusaurus-tutorial``.

   Repository URL
      The URL that contains the documentation source. Leave the automatically filled value.

   Default branch
      Name of the default branch of the project, leave it as ``main``.

   Then click the :guilabel:`Next` button to create the project and open the :term:`project home`.

 #. Click :guilabel:`This file exists` to trigger the first build of your documentation.

You just created your first Docusaurus project on Read the Docs! |:tada:|

Checking the first build
------------------------

Read the Docs will build your project documentation right after you create it.

.. TODO: update this since the UI has changed
.. 1. click on the version
.. 2. click on the build that just started

To see the build logs:

#. Click the :guilabel:`Your documentation is building` link on the :term:`project home`.

   - If the build has not finished by the time you open it, you will see a spinner next to a "Installing" or "Building" indicator, meaning that it is still in progress.
   - If the build has finished, you'll see a green "Build completed" indicator, the completion date, the elapsed time, and a link to the generated documentation.

#. Click on :guilabel:`View docs` to see your documentation live!

Configuring the project
-----------------------

To update the project description and configure the notification settings:

#. Navigate back to the :term:`project page` and click the :guilabel:`⚙ Admin` button, to open the Settings page.

#. Update the project description with a short summary of what the documentation is about.

#. Set a project homepage and add a couple of public project tags such as ``docusaurus, documentation``.

#. To get a notification if the build fails, click the :guilabel:`Email Notifications` link on the left, add your email address, and click the :guilabel:`Add` button.

Triggering builds from pull requests
------------------------------------

Read the Docs can :doc:`trigger builds from GitHub pull requests </pull-requests>`
and show you a preview of the documentation with those changes.

To trigger builds from pull requests:

#. Click the :guilabel:`Settings` link on the left under the :guilabel:`⚙ Admin` menu, check the "Build pull requests for this project" checkbox, and click the :guilabel:`Save` button at the bottom of the page.

#. Make some changes to your documentation:

   #. Navigate to your GitHub repository, locating the file ``docs/pages/intro.mdx``, and clicking on the |:pencil2:| icon on the top-right with the tooltip "Edit this file" to open a web editor.

   #. In the editor, add the following sentence to the file:

      .. code-block:: markdown
         :caption: docs/pages/intro.mdx

         This documentation is hosted on Read the Docs.

   #. Write an appropriate commit message, choose the "Create a **new branch** for this commit and start a pull request" option.

   #. Click the green :guilabel:`Propose changes` button to open the new pull request page, then click the :guilabel:`Create pull request` button below the description.

After opening the pull request, a Read the Docs check will appear
indicating that it is building the documentation for that pull request.
If you click the :guilabel:`Details` link while your project is building
the build log will be opened. After building, this link opens the documentation directly.

Reviewing the pull request preview
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once the pull request build finishes, Read the Docs adds a comment to the pull request with a build overview that includes:

- A link to the documentation preview.
- The list of files that changed between the pull request and the latest version of the documentation.

This summary saves you from clicking through the build log to find the preview, and helps you confirm at a glance that the changes you expected are the ones being deployed.

.. note::

   The build overview comment is only available for projects connected to a :ref:`reference/git-integration:GitHub App`.
   See :doc:`/pull-requests` for details on each of the pull request features.

Comparing changes with visual diff
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Reading a Markdown diff is fine for prose,
but it doesn't always tell you what the page will *look* like once rendered.
:doc:`Visual diff </visual-diff>` highlights the changes directly on the rendered documentation pages,
so you can review pull requests the same way readers will see them.

To enable visual diff:

#. Go to the :guilabel:`Settings` tab of your project.
#. Click :guilabel:`Addons`, then :guilabel:`Visual diff`.
#. Check :guilabel:`Enable visual diff` and click :guilabel:`Save`.

Open the pull request preview again. A new dropdown appears at the top right of the page listing every file that changed in the pull request. Pick a file to jump to it, then click :guilabel:`Show diff` (or press the ``d`` hotkey) to highlight the additions and deletions inline. Use the up/down arrows to step through each chunk.

Adding a configuration file
---------------------------

The Admin tab of the :term:`project home` has some *global* configuration settings for your project.

Build process configuration settings live in the ``.readthedocs.yaml`` :doc:`configuration file </config-file/v2>`, in your Git repository, which means it can be different for every version or branch of your project.

Docusaurus is a Node.js application, so Read the Docs builds it by running a sequence of commands defined under :ref:`build.jobs <config-file/v2:build.jobs>`. The template repository ships with this file:

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2

   build:
     os: "ubuntu-22.04"
     tools:
       nodejs: "20"
     jobs:
       install:
         - cd docs/ && npm install
       build:
         html:
           - cd docs/ && npm run build
           - mkdir --parents $READTHEDOCS_OUTPUT/html/
           - cp --recursive docs/build/* $READTHEDOCS_OUTPUT/html/

The :doc:`purpose of each key </config-file/v2>` is:

``version``
  Required, specifies :doc:`version 2 of the configuration file </config-file/v2>`.

``build.os``
  Required, specifies the Docker image used to build the documentation.

``build.tools.nodejs``
  Specifies the :ref:`Node.js version <config-file/v2:build.tools.nodejs>` used during the build.

``build.jobs.install``
  Commands run during the install step. The Docusaurus project lives under ``docs/``,
  so we ``cd`` into it and run ``npm install`` to install Docusaurus and its dependencies.

``build.jobs.build.html``
  Commands run to produce the HTML output. We ``cd docs/`` and run ``npm run build``
  to invoke Docusaurus, then copy the generated ``docs/build/`` directory into
  ``$READTHEDOCS_OUTPUT/html/``, where Read the Docs picks it up.

.. tip::

   ``build.jobs`` is the recommended way to override the build process for tools that do not have first-class Read the Docs support.
   Each step (``install``, ``build.html``, ``post_build``, etc.) can be overridden independently,
   which keeps the rest of Read the Docs' build pipeline intact.

Using a different Node.js version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To build your project with Node.js 22 instead of 20, edit the ``.readthedocs.yaml`` file and change the Node.js version like this:

.. code-block:: yaml
   :caption: .readthedocs.yaml
   :emphasize-lines: 6

   version: 2

   build:
     os: "ubuntu-22.04"
     tools:
       nodejs: "22"
     jobs:
       install:
         - cd docs/ && npm install
       build:
         html:
           - cd docs/ && npm run build
           - mkdir --parents $READTHEDOCS_OUTPUT/html/
           - cp --recursive docs/build/* $READTHEDOCS_OUTPUT/html/

After you commit these changes, go back to your project home, navigate to the "Builds" page, and open the new build that just started. You will see in the build logs that the new toolchain version was used to install the dependencies and build the site.

Versioning documentation
------------------------

Read the Docs supports having :doc:`several versions of your documentation </versions>`,
in the same way that you have several versions of your code.
By default, it creates a ``latest`` version
that points to the default branch of your version control system
(``main`` in the case of this tutorial),
and that's why the URLs of your HTML documentation contain the string ``/latest/``.

Creating a new version of your documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Read the Docs automatically creates documentation versions from GitHub branches and tags that :ref:`follow some rules <versions:Versioning workflows>` about looking like version numbers, such as ``1.0``, ``2.0.3`` or ``4.x``.

To create version ``1.0`` of your code, and consequently of your documentation:

#. Navigate to your GitHub repository, click the branch selector, type ``1.0.x``, and click "Create branch: 1.0.x from 'main'".

#. Check that you now have version ``1.0.x`` in your :term:`project home`, click on the :guilabel:`Versions` button, and under "Active Versions" you will see two entries:

  - The ``latest`` version, pointing to the ``main`` branch.
  - A new ``stable`` version, pointing to the ``origin/1.0.x`` branch.

When you created your branch, Read the Docs created a new special version called ``stable`` pointing to it. Once it builds, it appears in the :term:`flyout menu`.

Setting stable as the default
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To set ``stable`` as the *default version*, rather than ``latest``, so that users see the ``stable`` documentation when they visit the :term:`root URL` of your documentation:

#. In the :guilabel:`⚙ Admin` menu of your project home, go to the :guilabel:`Settings` link, choose ``stable`` in the "Default version" dropdown, and hit :guilabel:`Save` at the bottom.

Modifying versions
~~~~~~~~~~~~~~~~~~

Both ``latest`` and ``stable`` are now *active*, which means that they are visible to readers and new builds can be triggered for them.
In addition to these, Read the Docs also created an *inactive* ``1.0.x`` version, which always points to the ``1.0.x`` branch of your repository.

To activate the ``1.0.x`` version:

#. On your :term:`project home`, go to "Versions", locate ``1.0.x`` under "Activate a version", and click the :guilabel:`Activate` button.

#. On the "Activate" page with "Active" and "Hidden" checkboxes, check only "Active" and click :guilabel:`Save`.

.. note::

   Read more about :ref:`hidden versions <versions:Version states>`
   in our documentation.

Enabling link previews for your readers
---------------------------------------

:doc:`Link previews </link-previews>` show readers the content of an internal link when they hover over it,
so they can decide whether to follow the link without losing their place.

To enable link previews:

#. Go to your project's :term:`dashboard` and click the project name.
#. Go to :guilabel:`Settings`, then in the left bar, go to :guilabel:`Addons`.
#. Open :guilabel:`Link previews` and check :guilabel:`Enabled`.
#. Save your settings -- a rebuild of your project isn't required.

Open your published documentation and hover over any internal link. A small popup appears with the target page's content. Link previews only render for internal links inside the main documentation content, so navigation bars and external links are unaffected.

Building only when documentation changes
----------------------------------------

If your repository hosts both your application code and its documentation,
Read the Docs rebuilds your docs on every push by default — even when the
change doesn't touch any documentation files.
:doc:`Automation rules </automation-rules>` can gate builds on the contents
of the webhook event from GitHub, so you only spend build time on commits and
pull requests that actually affect the documentation.

To create a rule that builds your project only when documentation files change:

#. From the :term:`project home`, open the :guilabel:`⚙ Admin` menu and select
   :guilabel:`Automation Rules`, then click :guilabel:`Add Rule`.

#. Configure the rule:

   Description
      Something memorable, for example ``Build only on documentation changes``.

   Match
      ``Any version``.

   Version types
      Check :guilabel:`Tag`, :guilabel:`Branch`, and :guilabel:`Pull request`
      so the rule applies to every kind of build.

   Changed files
      One pattern per line:

      .. code-block:: text

         docs/*
         .readthedocs.yaml

   Action
      ``Trigger build for version``.

#. Click :guilabel:`Save` to create the rule.

From now on, Read the Docs only triggers a build when the push or pull request
modifies a file under ``docs/`` or the ``.readthedocs.yaml`` configuration.
Pushes that only touch application code, tests, or unrelated files no longer
trigger a documentation build.

.. important::

   Once a rule with the :guilabel:`Trigger build for version` action exists,
   builds are **gated** by automation rules: if no rule matches the incoming
   webhook event, no build runs. Make sure your patterns cover every path
   that should rebuild the docs before relying on this in production.

.. note::

   Webhook-filter automation rules are only available for projects connected
   through the :ref:`reference/git-integration:GitHub App`.

.. seealso::

   :doc:`/automation-rules`
     Full reference for automation rules, including filters by commit message
     and pull request label.

Where to go from here
---------------------

This is the end of the tutorial. You have accomplished a lot:

#. Created a Docusaurus project from a GitHub template.
#. Connected it to Read the Docs.
#. Built its HTML documentation.
#. Customized the build process with ``build.jobs``.
#. Reviewed pull requests with the build summary comment and visual diff.
#. Enabled link previews for your readers.
#. Added new documentation versions.
#. Configured an automation rule to build only when documentation changes.

Nice work!

Here are some resources to help you continue learning about documentation
and Read the Docs:

- Learn more about the platform :doc:`features </reference/features>`.
- Read the :doc:`Docusaurus deployment guide </intro/docusaurus>` for more advanced configuration tips.
- See a list of Read the Docs :doc:`/examples`.
- Learn how to do specific tasks in the :doc:`/guides/index`.
- Learn about private project support and other enterprise features
  in :doc:`our commercial service guide </commercial/index>`.
- Join a global community of fellow `documentarians <writethedocs:documentarians>` in `Write the Docs <https://www.writethedocs.org/>`_ and
  :doc:`its Slack workspace <writethedocs:slack>`.
- Contribute to Read the Docs in :doc:`rtd-dev:contribute`, we appreciate it!

Happy documenting!
