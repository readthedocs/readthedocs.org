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

The only things you will need to follow the are
a web browser, an Internet connection, and a GitHub account
(you can `register for a free account <https://github.com/signup>`_ if you don't have one).
You will use Read the Docs Community, which means that the project will be public.

Getting started
---------------

Preparing your project on GitHub
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To start, `sign in to GitHub <https://github.com/login>`_
and navigate to `the tutorial GitHub template <https://github.com/astrojuanlu/tutorial-template/>`_,
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

.. figure:: /_static/images/tutorial/rtd-import-projects.png
   :width: 80%
   :align: center
   :alt: Import projects view

   Import projects view

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
click on the "Your documentation is building" link on the dashboard,
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

   If you don't see the ad, you might be using an ad blocker.
   Our Ethical Ads network respects your privacy, doesn't target you,
   and tries to be as unobstrusive as possible,
   so we would like to kindly ask you to :doc:`not block us </advertising/ad-blocking>` |:heart:|

   Advertisement is one of our main sources of revenue.
   If you want to learn more about how do we fund our operations
   and explore options to go ad-free,
   check out our `Sustainability page <https://readthedocs.org/sustainability/>`_.

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

That's the end of the tutorial for now,
but you can learn more about the platform starting with our :doc:`/features` page.
