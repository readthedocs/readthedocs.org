Read the Docs tutorial
======================

In this tutorial you will create a documentation project on Read the Docs
by importing an Sphinx project from a GitHub repository,
tailor its configuration, and explore several useful features of the platform.

The tutorial is aimed at people interested in learning
how to use Read the Docs to host their documentation projects.
You will fork a fictional software library
similar to the one developed in the :doc:`official Sphinx tutorial <sphinx:tutorial/index>`.
No prior experience with Sphinx is required,
and you can follow this tutorial without having done the Sphinx one.

The only things you will need to follow are
a web browser, an Internet connection, and a GitHub account
(you can `register for a free account <https://github.com/signup>`_ if you don't have one).
You will use Read the Docs Community, which means that the project will be public.

Getting started
---------------

Preparing your project on GitHub
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To start, `sign in to GitHub <https://github.com/login>`_
and navigate to `the tutorial GitHub template <https://github.com/readthedocs/tutorial-template/>`_,
where you will see a green :guilabel:`Use this template` button.
Click it to open a new page that will ask you for some details:

* Leave the default "Owner", or change it to something better for a tutorial project.
* Introduce an appropriate "Repository name", for example ``rtd-tutorial``.
* Make sure the project is "Public", rather than "Private".

After that, click on the green :guilabel:`Create repository from template` button,
which will generate a new repository on your personal account
(or the one of your choosing).
This is the repository you will import on Read the Docs,
and it contains the following files:

``README.rst``
  Basic description of the repository, you will leave it untouched.

``pyproject.toml``
  Python project metadata that makes it installable.
  Useful for automatic documentation generation from sources.

``lumache.py``
  Source code of the fictional Python library.

``docs/``
  Directory holding all the Sphinx documentation sources,
  including some required dependencies in ``docs/requirements.txt``,
  the Sphinx configuration ``docs/source/conf.py``,
  and the root document ``docs/source/index.rst`` written in reStructuredText.

.. figure:: /_static/images/tutorial/github-template.png
   :width: 80%
   :align: center
   :alt: GitHub template for the tutorial

   GitHub template for the tutorial

Sign up for Read the Docs
~~~~~~~~~~~~~~~~~~~~~~~~~

To sign up for a Read the Docs account,
navigate to the `Sign Up page <https://readthedocs.org/accounts/signup/>`_
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
   like installing webhooks.
   If you want to learn more,
   check out :ref:`connected-accounts:permissions for connected accounts`.

After that, you will be redirected to Read the Docs,
where you will need to confirm your e-mail and username.
Clicking the :guilabel:`Sign Up »` button will create your account
and redirect you to your :term:`dashboard`.

By now, you should have two email notifications:

* One from GitHub, telling you that "A third-party OAuth application ...
  was recently authorized to access your account". You don't need to do
  anything about it.
* Another one from Read the Docs, prompting you to "verify your email
  address". Click on the link to finalize the process.

Finally, you created your account on Read the Docs
and are ready to import your first project.

Welcome!

.. figure:: /_static/images/tutorial/rtd-empty-dashboard.png
   :width: 80%
   :align: center
   :alt: Read the Docs empty dashboard

   Read the Docs empty dashboard

.. note::

   Our commercial site offers some extra features,
   like support for private projects.
   You can learn more about :doc:`our two different sites </choosing-a-site>`.

First steps
-----------

Importing the project to Read the Docs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To import your GitHub project to Read the Docs,
first click on the :guilabel:`Import a Project` button on your dashboard
(or browse to `the import page <https://readthedocs.org/dashboard/import/>`_ directly).
You should see your GitHub account under the "Filter repositories" list on the right.
If the list of repositories is empty, click the |:arrows_counterclockwise:| button,
and after that all your repositories will appear on the center.

.. figure:: /_static/images/tutorial/rtd-import-projects.gif
   :width: 80%
   :align: center
   :alt: Import projects workflow

   Import projects workflow

Locate your ``rtd-tutorial`` project
(possibly clicking :guilabel:`next ››` at the bottom if you have several pages of projects),
and then click on the |:heavy_plus_sign:| button to the right of the name.
The next page will ask you to fill some details about your Read the Docs project:

Name
  The name of the project. It has to be unique across all the service,
  so it is better if you prepend your username,
  for example ``astrojuanlu-rtd-tutorial``.

Repository URL
  The URL that contains the sources. Leave the automatically filled value.

Repository type
  Version control system used, leave it as "Git".

Default branch
  Name of the default branch of the project, leave it as ``main``.

Edit advanced project options
  Leave it unchecked, we will make some changes later.

After hitting the :guilabel:`Next` button, you will be redirected to the :term:`project home`.
You just created your first project on Read the Docs! |:tada:|

.. figure:: /_static/images/tutorial/rtd-project-home.png
   :width: 80%
   :align: center
   :alt: Project home

   Project home

Checking the first build
~~~~~~~~~~~~~~~~~~~~~~~~

Read the Docs will try to build the documentation of your project
right after you create it.
To see the build logs,
click on the "Your documentation is building" link on the :term:`project home`,
or alternatively navigate to the "Builds" page,
then open the one on top (the most recent one).

If the build has not finished yet by the time you open it,
you will see a spinner next to a "Installing" or "Building" indicator,
meaning that it is still in progress.

.. figure:: /_static/images/tutorial/rtd-first-successful-build.png
   :width: 80%
   :align: center
   :alt: First successful documentation build

   First successful documentation build

When the build finishes, you will see a green "Build completed" indicator,
the completion date, the elapsed time,
and a link to see the corresponding documentation.
If you now click on "View docs", you will see your documentation live!

.. figure:: /_static/images/tutorial/rtd-first-light.png
   :width: 80%
   :align: center
   :alt: HTML documentation live on Read the Docs

   HTML documentation live on Read the Docs

.. note::

   Advertisement is one of our main sources of revenue.
   If you want to learn more about how do we fund our operations
   and explore options to go ad-free,
   check out our `Sustainability page <https://readthedocs.org/sustainability/>`_.

   If you don't see the ad, you might be using an ad blocker.
   Our Ethical Ads network respects your privacy, doesn't target you,
   and tries to be as unobstrusive as possible,
   so we would like to kindly ask you to :doc:`not block us </advertising/ad-blocking>` |:heart:|

Basic configuration changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can now proceed to make some basic configuration adjustments.
Navigate back to the :term:`project page`
and click on the "⚙ Admin" button, which will open the Settings page.

First of all, add the following text in the description:

    Lumache (/lu'make/) is a Python library for cooks and food lovers
    that creates recipes mixing random ingredients.

Then set the project homepage to ``https://world.openfoodfacts.org/``,
and write ``food, python`` in the list of tags.
All this information will be shown on your project home.

After that, configure your email so you get a notification if the build fails.
To do so, click on the "Notifications" link on the left,
type the email where you would like to get the notification,
and click the "Add" button.
After that, your email will be shown under "Existing Notifications".

Trigger a build from a pull request
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Read the Docs allows you to :doc:`trigger builds from GitHub pull requests </pull-requests>`
and gives you a preview of how the documentation would look like with those changes.

To enable that functionality, first click on the "Advanced Settings" link on the left
under the "⚙ Admin" menu, check the "Build pull requests for this project" checkbox,
and click the :guilabel:`Save` button at the bottom of the page.

Next, navigate to your GitHub repository, locate the file ``docs/source/index.rst``,
and click on the |:pencil2:| icon on the top-right with the tooltip "Edit this file"
to open a web editor (more information `on their documentation`__).

__  https://docs.github.com/en/github/managing-files-in-a-repository/managing-files-on-github/editing-files-in-your-repository

.. figure:: /_static/images/tutorial/gh-edit.png
   :width: 80%
   :align: center
   :alt: File view on GitHub before launching the editor

   File view on GitHub before launching the editor

In the editor, add the following sentence to the file:

.. code-block:: rst
   :caption: docs/source/index.rst

   Lumache has its documentation hosted on Read the Docs.

Write an appropriate commit message,
and choose the "Create a **new branch** for this commit and start a pull request" option,
typing a name for the new branch.
When you are done, click the green :guilabel:`Propose changes` button,
which will take you to the new pull request page,
and there click the :guilabel:`Create pull request` button below the description.

.. figure:: /_static/images/tutorial/gh-pr-build.png
   :width: 80%
   :align: center
   :alt: Read the Docs building the pull request from GitHub

   Read the Docs building the pull request from GitHub

After opening the pull request, a Read the Docs check will appear
indicating that it is building the documentation for that pull request.
If you click on the "Details" link while it is building,
you will access the build logs,
otherwise it will take you directly to the documentation.
When you are satisfied, you can merge the pull request!

Customizing the build process
-----------------------------

The Settings page of the :term:`project home` allows you
to change some *global* configuration values of your project.
In addition, you can further customize the building process
using the ``.readthedocs.yaml`` :doc:`configuration file </config-file/v2>`.
This has several advantages:

- The configuration lives next to your code and documentation, tracked by version control.
- It can be different for every version (more on versioning in the next section).
- Some configurations are only available using the config file.

Read the Docs works without this configuration
by :ref:`making some decisions on your behalf <default-versions>`.
For example, what Python version to use, how to install the requirements, and others.

.. tip::

   Settings that apply to the entire project are controlled in the web dashboard,
   while settings that are version or build specific are better in the YAML file.

Upgrading the Python version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For example, to explicitly use Python 3.8 to build your project,
navigate to your GitHub repository, click on the :guilabel:`Add file` button,
and add a ``.readthedocs.yaml`` file with these contents to the root of your project:

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2

   python:
     version: "3.8"

The purpose of each key is:

``version``
  Mandatory, specifies :doc:`version 2 of the configuration file </config-file/v2>`.

``python.version``
  Declares the Python version to be used.

After you commit these changes, go back to your project home,
navigate to the "Builds" page, and open the new build that just started.
You will notice that one of the lines contains ``python3.8``:
if you click on it, you will see the full output of the corresponding command,
stating that it used Python 3.8.6 to create the virtual environment.

.. figure:: /_static/images/tutorial/build-python3.8.png
   :width: 80%
   :align: center
   :alt: Read the Docs build using Python 3.8

   Read the Docs build using Python 3.8

Making warnings more visible
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you navigate to your HTML documentation,
you will notice that the index page looks correct,
but actually the API section is empty.
This is a very common issue with Sphinx,
and the reason is stated in the build logs.
On the build page you opened before,
click on the "View raw" text on the top right,
which opens the build logs in plain text,
and you will see several warnings:

.. code-block:: text

   WARNING: [autosummary] failed to import 'lumache': no module named lumache
   ...
   WARNING: autodoc: failed to import function 'get_random_ingredients' from module 'lumache'; the following exception was raised:
   No module named 'lumache'
   WARNING: autodoc: failed to import exception 'InvalidKindError' from module 'lumache'; the following exception was raised:
   No module named 'lumache'

To spot these warnings more easily and allow you to address them,
you can add the ``sphinx.fail_on_warning`` option to your Read the Docs configuration file.
For that, navigate to GitHub, locate the ``.readthedocs.yaml`` file you created earlier,
click on the |:pencil2:| icon, and add these contents:

.. code-block:: yaml
   :caption: .readthedocs.yaml
   :emphasize-lines: 4-5

   python:
     version: "3.8"

   sphinx:
     fail_on_warning: true

At this point, if you navigate back to your "Builds" page,
you will see a ``Failed`` build, which is exactly the intended result:
the Sphinx project is not properly configured yet,
and instead of rendering an empty API page, now the build fails.

The reason :py:mod:`sphinx:sphinx.ext.autosummary` and :py:mod:`sphinx:sphinx.ext.autodoc`
fail to import the code is because it is not installed.
Luckily, the ``.readthedocs.yaml`` also allows you to specify
which requirements to install.

To install the library code of your project,
go back to editing ``.readthedocs.yaml`` on GitHub and modify it as follows:

.. code-block:: yaml
   :caption: .readthedocs.yaml
   :emphasize-lines: 3-5

   python:
     version: "3.9"
     # Install our python package before building the docs
     install:
       - method: pip
         path: .

With this change, Read the Docs will install the Python code
before starting the Sphinx build, which will finish seamlessly.
If you go now to the API page of your HTML documentation,
you will see the ``lumache`` summary!

Enabling PDF and EPUB builds
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sphinx can build several other formats in addition to HTML, such as PDF and EPUB.
You might want to enable these formats for your project
so your users can read the documentation offline.

To do so, add this extra content to your ``.readthedocs.yaml``:

.. code-block:: yaml
   :caption: .readthedocs.yaml
   :emphasize-lines: 4-6

   sphinx:
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

Read the Docs allows you to have :doc:`several versions of your documentation </versions>`,
in the same way that you have several versions of your code.
By default, it creates a ``latest`` version
that points to the default branch of your version control system
(``main`` in the case of this tutorial),
and that's why the URLs of your HTML documentation contain the string ``/latest/``.

Creating a new version
~~~~~~~~~~~~~~~~~~~~~~

Let's say you want to create a ``1.0`` version of your code,
with a corresponding ``1.0`` version of the documentation.
For that, first navigate to your GitHub repository, click on the branch selector,
type ``1.0.x``, and click on "Create branch: 1.0.x from 'main'"
(more information `on their documentation`__).

__  https://docs.github.com/en/github/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-and-deleting-branches-within-your-repository

Next, go to your :term:`project home`, click on the "Versions" button,
and under "Active Versions" you will see two entries:

- The ``latest`` version, pointing to the ``main`` branch.
- A new ``stable`` version, pointing to the ``origin/1.0.x`` branch.

.. figure:: /_static/images/tutorial/active-versions.png
   :width: 80%
   :align: center
   :alt: List of active versions of the project

   List of active versions of the project

Right after you created your branch,
Read the Docs created a new special version called ``stable`` pointing to it,
and started building it. When the build finishes,
the ``stable`` version will be listed in the :term:`flyout menu`
and your readers will be able to choose it.

.. note::

   Read the Docs :ref:`follows some rules <versions:how we envision versions working>`
   to decide whether to create a ``stable`` version pointing to your new branch or tag.
   To simplify, it will check if the name resembles a version number
   like ``1.0``, ``2.0.3`` or ``4.x``.

Now you might want to set ``stable`` as the *default version*,
rather than ``latest``,
so that users see the ``stable`` documentation
when they visit the :term:`root URL` of your documentation
(while still being able to change the version in the flyout menu).

For that, go to the "Advanced Settings" link under the "⚙ Admin" menu of your project home,
choose ``stable`` in the "Default version*" dropdown,
and hit :guilabel:`Save` at the bottom.
Done!

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

Let's activate the ``1.0.x`` version.
For that, go to the "Versions" on your :term:`project home`,
locate ``1.0.x`` under "Activate a version",
and click on the :guilabel:`Activate` button.
This will take you to a new page with two checkboxes,
"Active" and "Hidden". Check only "Active",
and click :guilabel:`Save`.

After you do this, ``1.0.x`` will appear on the "Active Versions" section,
and a new build will be triggered for it.

.. note::

   You can read more about :ref:`hidden versions <versions:hidden>`
   in our documentation.

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
To display a warning to your readers, go to the "⚙ Admin" menu of your project home,
click on the "Advanced Settings" link on the left,
enable the "Show version warning" checkbox, and click the :guilabel:`Save` button.

If you now browse the ``1.0.x`` documentation, you will see a warning on top
encouraging you to browse the latest version instead. Neat!

.. figure:: /_static/images/tutorial/old-version-warning.png
   :width: 80%
   :align: center
   :alt: Warning for old versions

   Warning for old versions

----

That's the end of the tutorial,
but you can learn more about the platform starting with our :doc:`/features` page.
