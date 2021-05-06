Explicit Builders
=================

.. contents::
   :local:
   :depth: 2

Background
----------

In the past we have installed some dependencies on each build,
and tried to guess some options for users in order to make it *easy* for them to start using Read the Docs.
This has bring some unexpected problems and confusion to users, like:

- The Sphinx version (or from any other tool) isn't the one they expect.
- Unexpected dependencies are installed.
- The wrong docs directory is used.
- Their configuration file is changed on build time overriding the defaults or adding new things.
- Some files are auto-generated (like ``index.{rst,md}``).

Currently we are aiming to remove this *magic* behaviour from our build process,
and educating users to be more explicit about their dependencies and options
in order to make their builds reproducible.

We are using several feature flags to stop doing this for new projects,
but with so many flags to check our code starts to be hard to follow.
Instead we would manage a single feature flag and several classes of builds and environments.

Python Environments
-------------------

Currently we have two Python environments: Virtualenv and Conda,
they are in charge of installing requirements into an isolated environment.
We would need to refactor those classes into two types: the new build, and the old build.

The new Python environments would install only the latest versions of the following dependencies:

Virtualenv
   - Sphinx or MkDocs
   - readthedocs-sphinx-ext

Conda
   - readthedocs-sphinx-ext

Note that for Conda we won't install Sphinx or MkDocs,
this is to avoid problems like `#3829`_ and `#8096`_.

.. _#3829: https://github.com/readthedocs/readthedocs.org/issues/3829
.. _#8096: https://github.com/readthedocs/readthedocs.org/issues/8096

Doc builders
------------

Currently we have two types of doc builders: Sphinx and MkDocs.
They are in charge of generating the HTML files (or PDF/EPUB) from the source files.
We would need to refactor those classes into two types: the new build, and the old build.

Both builders create an ``index.{rst,md}`` file with some suggestions if one doesn't exist,
this is to avoid surprises to users, but sometimes this is done on purpose.
We could change our default 404 page to include some of these suggestions instead,
or fail the build if there isn't an ``index.html`` file created (do users want to do this on purpose?).
Related to `#1800`_.

.. _#1800: https://github.com/readthedocs/readthedocs.org/issues/1800

The new builders would do the minimal (or none) changes to the user's configuration in order to build their docs.

Sphinx
~~~~~~

conf.py
'''''''

We should read the configuration file from the user or default to *one* path,
and error if it doesn't exist.
We shouldn't change or override the values from the user's configuration (``conf.py``),
some are:

- ``_static`` is added to ``html_static_path`` (probably an old setting)
- ``html_theme`` (we are only setting this if certain condition is met)
- ``websupport2_*`` (probably old settings)
- ``html_context`` (more information below)
- Latex settings
  (they are used to improve the output for Chinese and Japanese languages, we should write a guide instead)

Sphinx's ``html_context``
'''''''''''''''''''''''''

We should pass the minimal needed information into the context.
This is related to :doc:`/development/design/theme-context`.

With :doc:`/api/v3` and environment variables (to store the secret token)
should be possible to query several things from the project without having to pass them at build time into the context.
Most the of basic information can be obtained from our environment variables (``READTHEDOCS_*``).

Some values from the context are used in our Sphinx extension,
we should define them as configuration options instead.
Others are used in our theme, should we stop setting them?

Extension
'''''''''

There are some things our extension does that are already supported by Sphinx or themes
(analytics, canonical URL, etc), we should write a guide instead of applying our magic.
Alternative, we can make this options, analytics is already an option.

The extension also injects some custom js and css files.
We could try another more general approach and inject these on each HTML file after the build is complete.

The extension injects the warning banner if you are reading the docs from a pull request.
We could implement this like the version warning banner instead, so it works for MkDocs too.
(this is injected with the version selector).

MkDocs
~~~~~~

We should read the configuration file from the user or default to *one* path,
and error if it doesn't exist.

We shouldn't change the values from the user's configuration (``mkdocs.yml``),
currently we change:

- ``docs_dir``
- ``extra_javascript``
- ``extra_css``
- ``google_analytics`` (we change this to ``None`` and use our own method)
- ``theme`` (we set it to our theme for old projects)

Only the additional js/css files should be added.
Additionally, we could try another more general approach and inject these after the build is complete.

Related to `#7844`_, `#4924`_, `#4827`_, `#4820`_

.. _#7844: https://github.com/readthedocs/readthedocs.org/issues/7844
.. _#4924: https://github.com/readthedocs/readthedocs.org/issues/4924
.. _#4827: https://github.com/readthedocs/readthedocs.org/issues/4827
.. _#4820: https://github.com/readthedocs/readthedocs.org/issues/4820

Web settings
------------

Simple defaults, without fallbacks.

Currently if some of our settings aren't set or are incorrect
we try to guess some values for the user.
We should have some sane defaults and error otherwise.
Some are:

- Requirements file (we shouldn't install any if isn't set)
- Sphinx/MkDocs configuration file (we could default to ``docs/conf.py`` and ``mkdocs.yml``)

.. note::

   When using the v2 of the config file we remove all this magic.

Other settings are used for things that can be done from the user side:

- Analytics code (exposed as an option)
- Canonical domain (Sphinx only, and isn't exposed as an option)

Adoption
--------

If we remove some magical behaviour that was doing things for the user,
we should document how to do them using Sphinx/MkDocs.

These new builders/environments would be under a feature flag.
We can keep the implementation incrementally by start using a feature flag on some of our projects first,
after we everything is implemented we can move the flag to be active for projects created after ``x`` date,
and past projects would use the old ones.

Deprecation
-----------

Using a feature flag can bring some confusion to users that have a project created before the given date,
and other after that date. We can opt-in users into the new builders by adding them into the feature flag.

In order to simplify our code and have all projects using the same options and dependencies
we want to fully migrate all projects to use the new builders.
We could put a date to do this, and contact all users of old projects about this change
Some things to do would be:

- Write several guides on how to do things explicitly
- Write several guides on how users can implement the magic things we were doing
  (canonical domain, analytics, custom theme, dependencies, PDF improvements for Japanese and Chinese languages, etc)
- An entry in our blog
- Email all users that have old projects
- Give users some time to migrate (six months, one year?)
- Migrate all projects to the new builders
  (allow users to opt-in into the old builders with a feature flag for a short time in case they didn't get to migrate? Could be useful for commercial)
- Remove old code

The future
----------

We may also take this as an opportunity to get ready to support more tools,
this is by depending less on overrides and extensions, and work over the generated HTML.

For Sphinx, it could be useful to implement our new context :doc:`/development/design/theme-context`,
but do we really need to inject that context anymore? We have API v3 now.

As proposed, we can make this changes incrementally and test in our own projects before
making the final decisions.
