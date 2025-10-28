Read the Docs tutorial
======================

In this tutorial you will learn how to host a public documentation project on Read the Docs Community.

.. note::

   Find out the `differences between Read the Docs Community and Read the Docs for Business <https://about.readthedocs.com/pricing/#/community>`_.

In the tutorial we will:

1. Import a Sphinx project from a GitHub repository (no prior experience with Sphinx is required).
2. Tailor the project's configuration.
3. Explore other useful Read the Docs features.

If you don't have a GitHub account, you'll need to `register for a free account <https://github.com/signup>`_ before you start.

Preparing your repository on GitHub
-----------------------------------

#. `Sign in to GitHub <https://github.com/login>`_ and navigate to the `tutorial GitHub template <https://github.com/readthedocs/tutorial-template/>`_.

#. Click the green :guilabel:`Use this template` button, then click :guilabel:`Create a new Repository`. On the new page:

   Owner
      Leave the default, or change it to something suitable for a tutorial project.
   Repository name
      Something memorable and appropriate, for example ``rtd-tutorial``.
   Visibility
      Make sure the project is "Public", rather than "Private".

#. Click the green :guilabel:`Create repository` button to create a public repository that you will use in this Read the Docs tutorial, containing  following files:

   ``.readthedocs.yaml``
      Read the Docs configuration file. Required.

   ``README.rst``
      Description of the repository.

   ``pyproject.toml``
      Python project metadata that makes it installable.
      Useful for automatic documentation generation from sources.

   ``lumache.py``
      Source code of the fictional Python library.

   ``docs/``
      Directory holding all the fictional Python library documentation in reStructuredText, the Sphinx configuration ``docs/source/conf.py``
      and the root document ``docs/source/index.rst``.

.. figure:: /_static/images/tutorial/github-template.png
   :width: 80%
   :align: center
   :alt: GitHub template for the tutorial

   GitHub template for the tutorial

Creating a Read the Docs account
--------------------------------

To create a Read the Docs account:
navigate to the `Sign Up page <https://app.readthedocs.org/accounts/signup/>`_
and choose the option :guilabel:`Sign up with GitHub`.
On the authorization page, click the green :guilabel:`Authorize readthedocs` button.

.. figure:: /_static/images/tutorial/github-authorization.png
   :width: 60%
   :align: center
   :alt: GitHub authorization page

   GitHub authorization page

.. note::

   Read the Docs needs elevated permissions to perform certain operations
   that ensure that the workflow is as smooth as possible,
   like installing :term:`webhooks <webhook>`.
   If you want to learn more,
   check out :ref:`reference/git-integration:permissions for connected accounts`.

After that, you will be redirected to Read the Docs to confirm your e-mail and username. Click the :guilabel:`Sign Up »` button to create your account and
open your :term:`dashboard`.

When you have clicked the link in your email from Read the Docs to "verify your email address" and finalize the process, your Read the Docs account will be ready to create your first project.

.. figure:: /_static/images/tutorial/rtd-empty-dashboard.png
   :width: 80%
   :align: center
   :alt: Read the Docs empty dashboard

   Welcome to your Read the Docs dashboard!

Importing the project to Read the Docs
--------------------------------------

To import your GitHub project to Read the Docs:

#. Click the :guilabel:`Import a Project` button on your `dashboard <https://app.readthedocs.org/dashboard/>`_.

#. Click the |:heavy_plus_sign:| button to the right of your ``rtd-tutorial`` project. If the list of repositories is empty, click the |:arrows_counterclockwise:| button.

   .. figure:: /_static/images/tutorial/rtd-import-projects.gif
      :width: 80%
      :align: center
      :alt: Import projects workflow

      Import projects workflow

#. Enter some details about your Read the Docs project:

   Name
      The name of the project, used to create a unique subdomain for each project.
      so it is better if you prepend your username,
      for example ``{username}-rtd-tutorial``.

   Repository URL
      The URL that contains the documentation source. Leave the automatically filled value.

   Default branch
      Name of the default branch of the project, leave it as ``main``.

   Then click the :guilabel:`Next` button to create the project and open the :term:`project home`.

You just created your first project on Read the Docs! |:tada:|

.. figure:: /_static/images/tutorial/rtd-project-home.png
   :width: 80%
   :align: center
   :alt: Project home

   Project home

Checking the first build
------------------------

Read the Docs will build your project documentation right after you create it.

To see the build logs:

#. Click the :guilabel:`Your documentation is building` link on the :term:`project home`.

   - If the build has not finished by the time you open it, you will see a spinner next to a "Installing" or "Building" indicator, meaning that it is still in progress.
   - If the build has finished, you'll see a green "Build completed" indicator, the completion date, the elapsed time, and a link to the generated documentation.

   .. figure:: /_static/images/tutorial/rtd-first-successful-build.png
      :width: 80%
      :align: center
      :alt: First successful documentation build

      First successful documentation build

#. Click on :guilabel:`View docs` to see your documentation live!

.. figure:: /_static/images/tutorial/rtd-first-light.png
   :width: 80%
   :align: center
   :alt: HTML documentation live on Read the Docs

   HTML documentation live on Read the Docs

.. note::

   Advertisement is one of our main sources of revenue.
   If you want to learn more about how do we fund our operations
   and explore options to go ad-free,
   check out our `Sustainability page <https://app.readthedocs.org/sustainability/>`_.

   If you don't see the ad, you might be using an ad blocker.
   Our EthicalAds network respects your privacy, doesn't target you,
   and tries to be as unobtrusive as possible,
   so we would like to kindly ask you to :doc:`not block us </advertising/ad-blocking>` |:heart:|

Configuring the project
-----------------------

To update the project description and configure the notification settings:

#. Navigate back to the :term:`project page` and click the :guilabel:`⚙ Admin` button,to open the Settings page.

#. Update the project description by adding the following text:

    Lumache (/lu'make/) is a Python library for cooks and food lovers
    that creates recipes mixing random ingredients.

#. Set the project homepage to ``https://world.openfoodfacts.org/``, and add ``food, python`` to the list of public project tags.

#. To get a notification if the build fails, click the :guilabel:`Email Notifications` link on the left, add your email address, and click the :guilabel:`Add` button.

Triggering builds from pull requests
------------------------------------

Read the Docs can :doc:`trigger builds from GitHub pull requests </pull-requests>`
and show you a preview of the documentation with those changes.

To trigger builds from pull requests:

#. Click the :guilabel:`Settings` link on the left under the :guilabel:`⚙ Admin` menu, check the "Build pull requests for this project" checkbox, and click the :guilabel:`Save` button at the bottom of the page.

#. Make some changes to your documentation:

   #. Navigate to your GitHub repository, locating the file ``docs/source/index.rst``, and clicking on the |:pencil2:| icon on the top-right with the tooltip "Edit this file" to open a web editor (more information `on their documentation`__).

      __  https://docs.github.com/en/github/managing-files-in-a-repository/managing-files-on-github/editing-files-in-your-repository

      .. figure:: /_static/images/tutorial/gh-edit.png
         :width: 80%
         :align: center
         :alt: File view on GitHub before launching the editor

         File view on GitHub before launching the editor

   #. In the editor, add the following sentence to the file:

      .. code-block:: rst
         :caption: docs/source/index.rst

         Lumache hosts its documentation on Read the Docs.

   #. Write an appropriate commit message, choose the "Create a **new branch** for this commit and start a pull request" option.

   #. Click the green :guilabel:`Propose changes` button to open the new pull request page, then click the :guilabel:`Create pull request` button below the description.

   .. figure:: /_static/images/tutorial/gh-pr-build.png
      :width: 80%
      :align: center
      :alt: Read the Docs building the pull request from GitHub

      Read the Docs building the pull request from GitHub

After opening the pull request, a Read the Docs check will appear
indicating that it is building the documentation for that pull request.
If you click the :guilabel:`Details` link while your project is building
the build log will be opened. After building this link opens the documentation directly.

Adding a configuration file
---------------------------

The Admin tab of the :term:`project home` has some *global* configuration settings for your project.

Build process configuration settings are in ``.readthedocs.yaml`` :doc:`configuration file </config-file/v2>`, in your Git repository, which means it can be different for every version or branch of your project (more on `versioning <#versioning-documentation>`_).

.. TODO: We are adding a how-to that we need to include in this tutorial.
.. Maybe by reference or maybe as full-featured content.

.. TODO there is a bit of handwaving about whether you're committing and merging branches here, we might need to be a bit more explicit. Or at least add a mention at this level that wherever we talk about editing, we mean on main and pushing to GH.

Using different Python versions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To build your project with Python 3.8 instead of the latest Python version, edit the ``.readthedocs.yaml`` file and change the Python version to 3.8 like this:

.. code-block:: yaml
   :caption: .readthedocs.yaml
   :emphasize-lines: 6

   version: 2

   build:
     os: "ubuntu-22.04"
     tools:
       python: "3.8"

   python:
     install:
       - requirements: docs/requirements.txt

   sphinx:
     configuration: docs/source/conf.py

The :doc:`purpose of each key </config-file/v2>` in the ``.readthedocs.yaml`` configuration file is:

``version``
  Required, specifies :doc:`version 2 of the configuration file </config-file/v2>`.

``build.os``
  Required, specifies the Docker image used to build the documentation.
  :ref:`states the name of the base image <config-file/v2:build.os>`.

``build.tools.python``
  Specifies the :ref:`Python version <config-file/v2:build.tools.python>`.

``python.install.requirements``
  Specifies what :ref:`Python dependencies <config-file/v2:python.install>` to install.

After you commit these changes, go back to your project home,
navigate to the "Builds" page, and open the new build that just started.
You will notice that one of the lines contains ``python -mvirtualenv``:
if you click on it, you will see the full output of the corresponding command,
stating that it used Python 3.8.6, the latest version of Python 3.8, to create the virtual environment.

.. figure:: /_static/images/tutorial/build-python3.8.png
   :width: 80%
   :align: center
   :alt: Read the Docs build using Python 3.8

   Read the Docs build using Python 3.8

Making build warnings more visible
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you navigate to your HTML documentation,
you will notice that the index page looks correct
but the API section is empty.
This is a common issue with Sphinx,
and the reason is stated in the build logs.
On the build page you opened before,
click on the :guilabel:`View raw` link on the top right,
which opens the build logs in plain text,
and you will see several warnings:

.. code-block:: text

   WARNING: [autosummary] failed to import 'lumache': no module named lumache
   ...
   WARNING: autodoc: failed to import function 'get_random_ingredients' from module 'lumache'; the following exception was raised:
   No module named 'lumache'
   WARNING: autodoc: failed to import exception 'InvalidKindError' from module 'lumache'; the following exception was raised:
   No module named 'lumache'

To spot these warnings more easily and help you to address them,
add the ``sphinx.fail_on_warning`` option to your Read the Docs configuration file.

To fail on warnings to your Read the Docs project, edit the ``.readthedocs.yaml`` file in your project, add the three lines of ``sphinx`` configuration below, and commit the file:

.. code-block:: yaml
   :caption: .readthedocs.yaml
   :emphasize-lines: 14

   version: 2

   build:
     os: "ubuntu-22.04"
     tools:
       python: "3.8"

   python:
     install:
       - requirements: docs/requirements.txt

   sphinx:
     configuration: docs/source/conf.py
     fail_on_warning: true

If you navigate to your "Builds" page, you will see a ``Failed`` build, which is expected because we've configured Sphinx to fail on warnings and several warnings were encountered during the build.

To learn how to fix these warnings, see the next section.

Installing Python dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The reason :py:mod:`sphinx:sphinx.ext.autosummary` and :py:mod:`sphinx:sphinx.ext.autodoc` fail to import the :ref:`tutorial/index:making build warnings more visible`, is because the ``lumache`` module is not installed.

You will need to specify those installation requirements in ``.readthedocs.yaml``.

To install your project dependencies and make your code available to Sphinx,
edit ``.readthedocs.yaml``, add the ``python.install``  section and commit it:

.. code-block:: yaml
   :caption: .readthedocs.yaml
   :emphasize-lines: 4-6

   python:
     install:
       - requirements: docs/requirements.txt
       # Install our python package before building the docs
       - method: pip
         path: .

Now, Read the Docs installs the Python code
before starting the Sphinx build, which will finish seamlessly.
If you go now to the API page of your HTML documentation,
you will see the ``lumache`` summary! :tada:

Enabling PDF and EPUB builds
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sphinx can build several other formats in addition to HTML, such as PDF and EPUB.
You might want to enable these formats for your project
so your users can read the documentation offline.

To do so, add the following ``formats`` to your ``.readthedocs.yaml``:

.. code-block:: yaml
   :caption: .readthedocs.yaml
   :emphasize-lines: 5-7

   sphinx:
     configuration: docs/source/conf.py
     fail_on_warning: true

   formats:
     - pdf
     - epub

After this change, PDF and EPUB downloads will be available
both from the "Downloads" section of the :term:`project home`,
as well as the :term:`flyout menu`.

.. figure:: /_static/images/tutorial/flyout-downloads.png
   :align: center
   :alt: Downloads available from the flyout menu

   Downloads available from the flyout menu

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

Read the Docs automatically creates documentation versions from GitHub branches and tags that :ref:`follows some rules <versions:Versioning workflows>` about looking like version numbers, such as ``1.0``, ``2.0.3`` or ``4.x``.

To create version ``1.0`` of your code, and consequently of your documentation:

#. Navigate to your GitHub repository, click the branch selector, type ``1.0.x``, and click "Create branch: 1.0.x from 'main'" (more information `in the GitHub documentation`__).

#. Check that you now have version ``1.0.x`` in your :term:`project home`, click on the :guilabel:`Versions` button, and under "Active Versions" you will see two entries:

  - The ``latest`` version, pointing to the ``main`` branch.
  - A new ``stable`` version, pointing to the ``origin/1.0.x`` branch.

__ https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-and-deleting-branches-within-your-repository


.. figure:: /_static/images/tutorial/active-versions.png
   :width: 80%
   :align: center
   :alt: List of active versions of the project

   List of active versions of the project

When you created your branch,
Read the Docs created a new special version called ``stable`` pointing to it. When it's built it will be listed in the :term:`flyout menu`.

Setting stable as the default
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To set ``stable`` as the *default version*,
rather than ``latest``,
so that users see the ``stable`` documentation
when they visit the :term:`root URL` of your documentation:

#. In the :guilabel:`⚙ Admin` menu of your project home, go to the :guilabel:`Settings` link, choose ``stable`` in the "Default version*" dropdown, and hit :guilabel:`Save` at the bottom.

Modifying versions
~~~~~~~~~~~~~~~~~~

Both ``latest`` and ``stable`` are now *active*, which means that
they are visible for users, and new builds can be triggered for them.
In addition to these, Read the Docs also created an *inactive* ``1.0.x``
version, which will always point to the ``1.0.x`` branch of your repository.

.. figure:: /_static/images/tutorial/inactive-versions.png
   :width: 80%
   :align: center
   :alt: List of inactive versions of the project

   List of inactive versions of the project

To activate the ``1.0.x`` version:

#. On your :term:`project home`, go to the "Versions", locate ``1.0.x`` under "Activate a version", and click the :guilabel:`Activate` button.

#. On the "Activate" page with "Active" and "Hidden" checkboxes, check only "Active" and click :guilabel:`Save`.

.. note::

   Read more about :ref:`hidden versions <versions:Version states>`
   in our documentation.

.. "Show a warning for old versions" feature is not available anymore.
   We should re-write this section once we have the notification addons rolled out.


   Show a warning for old versions
   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

   When your project matures, the number of versions might increase.
   Sometimes you will want to warn your readers
   when they are browsing an old or outdated version of your documentation.

   To showcase how to do that, let's create a ``2.0`` version of the code:
   navigate to your GitHub repository, click on the branch selector,
   type ``2.0.x``, and click on "Create branch: 2.0.x from 'main'".
   This will trigger two things:

   - Since ``2.0.x`` is your newest branch, ``stable`` will switch to tracking it.
   - A new ``2.0.x`` version will be created on your Read the Docs project.
   - Since you already have an active ``stable`` version, ``2.0.x`` will be activated.

   From this point, ``1.0.x`` version is no longer the most up to date one.
   To display a warning to your readers, go to the :guilabel:`⚙ Admin` menu of your project home,
   click on the :guilabel:`Settings` link on the left,
   enable the "Show version warning" checkbox, and click the :guilabel:`Save` button.

   If you now browse the ``1.0.x`` documentation, you will see a warning on top
   encouraging you to browse the latest version instead. Neat!

   .. figure:: /_static/images/tutorial/old-version-warning.png
      :width: 80%
      :align: center
      :alt: Warning for old versions

      Warning for old versions

Getting project insights
------------------------

Once your project is up and running, you will probably want to understand
how readers are using your documentation, addressing some common questions like:

- what are the most visited pages?
- what are the most frequently used search terms?
- are readers finding what they are looking for?

Read the Docs has traffic and search analytics tools to help you find answers to these questions.

Understanding traffic analytics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Traffic Analytics view gives you a simple overview of how your readers browse your documentation. It respects visitor privacy by not storing identifying information about your them.

This page shows the most viewed documentation pages of the past 30 days,
plus a visualization of the daily views during that period.

To see the Traffic Analytics view, go back the :term:`project page` again,
click the :guilabel:`⚙ Admin` button,
and then click the :guilabel:`Traffic Analytics` section.
You will see the list of pages in descending order of visits,
and a similar visualization to this one:

.. figure:: /_static/images/tutorial/traffic-analytics-plot.png
   :width: 80%
   :align: center
   :alt: Traffic Analytics plot

   Traffic Analytics plot

You can also download this data in :abbr:`CSV (Comma-Separated Values)`  format for closer inspection.
To do that, scroll to the bottom of the page
and click the :guilabel:`Download all data` button.

Understanding search analytics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As well as traffic analytics, Read the Docs shows :doc:`what terms your readers are searching for </search-analytics>`.
This can inform decisions on what areas to focus on,
or what parts of your project are less understood or more difficult to find.

To generate some artificial search statistics on the project,
go to the HTML documentation, locate the Sphinx search box on the left,
type ``ingredients``, and press the :kbd:`Enter` key.
You will be redirected to the search results page, which will show two entries.

Next, go back to the :guilabel:`⚙ Admin` section of your project page,
and then click the :guilabel:`Search Analytics` section.
You will see a table with the most searched queries
(including the ``ingredients`` one you just typed),
how many results did each query return, and how many times it was searched.
Below the queries table, you will also see a visualization
of the daily number of search queries during the past 30 days.

.. figure:: /_static/images/tutorial/search-analytics-terms.png
   :width: 80%
   :align: center
   :alt: Most searched terms

   Most searched terms

Like the Traffic Analytics, you can also download the whole dataset in CSV format
by clicking on the :guilabel:`Download all data` button.

Where to go from here
---------------------

This is the end of the tutorial. You have accomplished a lot:

#. Forked a GitHub repository.
#. Connected it to Read the Docs.
#. Built its HTML documentation.
#. Customized the build process.
#. Added new documentation versions.
#. Browsed the project analytics.

Nice work!

Here are some resources to help you continue learning about documentation
and Read the Docs:

- Learn more about the platform :doc:`features </reference/features>`.
- Learn about other supported documentation generators in the :doc:`Sphinx tutorial <sphinx:tutorial/index>` or the `MkDocs User Guide <https://www.mkdocs.org/user-guide/>`_.
- See a list of Read the Docs :doc:`/examples`.
- Learn how to do specific tasks in the :doc:`/guides/index`.
- Learn about private project support and other enterprise features
  in :doc:`our commercial service guide </commercial/index>`.
- Join a global community of fellow `documentarians <writethedocs:documentarians>` in `Write the Docs <https://www.writethedocs.org/>`_ and
  :doc:`its Slack workspace <writethedocs:slack>`.
- Contribute to Read the Docs in :doc:`rtd-dev:contribute`, we appreciate it!

Happy documenting!
