Automation rules
================

Automation rules allow project maintainers to automate actions on new branches, tags,
and pull requests in Git repositories.
If you are familiar with :term:`GitOps`,
this might seem familiar.
The goal of automation rules is to be able to control versioning and builds through your Git repository
and avoid duplicating these efforts on Read the Docs.

.. seealso::

   :doc:`/guides/automation-rules`
     A practical guide to managing automated versioning of your documentation.

   :doc:`/versions`
     General explanation of how versioning works on Read the Docs

How automation rules work
-------------------------

When a new tag or branch is pushed to your repository,
or a pull request is opened or updated,
Read the Docs receives a webhook from your Git provider.
Read the Docs then creates (or updates) a *version* that matches your Git *tag, branch, or pull request*.

All enabled automation rules are evaluated for that version,
in the order they are listed.
A rule has three groups of conditions, which are checked in order:

1. The version **type** must be one of the version types selected in the rule (tag, branch, or pull request).
2. The version **name** must match the version pattern in the rule.
3. If any **webhook filter** is configured, the data from the webhook event
   (changed files, commit message, or pull request labels) must also match.

If all the configured conditions match, the rule's **action** is performed on the version.

.. note::

   Versions can match multiple automation rules,
   and all matching version actions will be performed on the version.
   For build actions, only the first matching rule per version triggers a build,
   to avoid triggering multiple builds for the same change.

Matching the version type
-------------------------

Each rule applies to one or more version types:

- **Tag** — Git tags pushed to the repository.
- **Branch** — Git branches pushed to the repository.
- **Pull request** — pull/merge requests opened against the repository.

You can select any combination of types in a single rule.

Matching the version name
-------------------------

We have a couple predefined ways to match against the name of versions that are created,
and you can also define your own.

Predefined matches
~~~~~~~~~~~~~~~~~~

Automation rules support two predefined version name matches:

- **Any version**: All new versions will match the rule.
- **SemVer versions**: All new versions that follow `semantic versioning <https://semver.org/>`__
  (with or without a ``v`` prefix) will match the rule.

Custom matches
~~~~~~~~~~~~~~

If none of the above predefined matches meet your use case,
you can use a **Custom match**.

The custom match should be a valid `Python regular expression <https://docs.python.org/3/library/re.html>`__.
Each new version's name will be tested against this regular expression.

Webhook filters
---------------

In addition to matching the version, a rule can filter on the contents of the
webhook event that triggered it.
Webhook filters are useful to **avoid running an action when nothing relevant has changed**,
for example to skip builds when only non-documentation files were modified,
or when the commit message indicates the change should be ignored.

The following filters are available:

Changed files
  Match against the list of files modified, added, or deleted in the push or pull request.
  Patterns use `fnmatch <https://docs.python.org/3/library/fnmatch.html>`__ syntax,
  one pattern per line. The filter matches if **any** of the changed files matches **any** pattern.

Commit message
  Match against the commit message of the push event,
  or the head commit of the pull request,
  using a `Python regular expression <https://docs.python.org/3/library/re.html>`__.

Pull request labels
  Match against the labels of the pull request,
  using a `Python regular expression <https://docs.python.org/3/library/re.html>`__.
  This filter is only relevant for pull request events.

When more than one filter is configured, **all** of them must match for the rule to fire.

.. note::

   Webhook filters are only available for projects connected through the
   :doc:`GitHub App integration </reference/git-integration>`.
   Rules that don't use webhook filters keep working with every Git provider.

Actions
-------

When an automation rule matches,
the specified action is performed on the version.
Actions are split into two groups: actions that operate on the version itself,
and actions that trigger a build.

Version actions
~~~~~~~~~~~~~~~

Activate version
  Activates and builds the version.

Hide version
  Hides the version. If the version is not active, activates it and builds the version.
  See :ref:`versions:Version states`.

Make version public
  Sets the version's privacy level to public.
  See :ref:`versions:Version states`.

Make version private
  Sets the version's privacy level to private.
  See :ref:`versions:Version states`.

Set version as default
  Sets the version as the :term:`default version`.
  It also activates and builds the version.
  See :ref:`root_url_redirect`.

Delete version
  When a branch or tag is deleted from your repository,
  Read the Docs will delete it *only if isn't active*.
  This action allows you to delete *active* versions when a branch or tag is deleted from your repository.

There are a couple caveats to these actions that are useful:

*   The :term:`default version` isn't deleted even if it matches a rule.
    You can use the ``Set version as default`` action to change the default version
    before deleting the current one.
*   If your versions follow :pep:`440`,
    Read the Docs activates and builds the version if it's greater than the current stable version.
    The stable version is also automatically updated at the same time.
    See more in :doc:`versions`.

Build actions
~~~~~~~~~~~~~

Trigger build for version
  Trigger a build for the version when the rule matches.

Build actions are designed to be used together with :ref:`webhook filters <automation-rules:Webhook filters>`,
so that builds are only triggered when something relevant has changed.

.. important::

   When a project has at least one enabled rule with the **Trigger build for version** action,
   builds are **gated** by those rules:
   if no build rule matches the incoming webhook event, no build is triggered.
   If you don't have any build rule configured, builds keep being triggered for every push and pull request as usual.

Enabling and disabling rules
----------------------------

Each rule has an **Enabled** toggle.
Disabling a rule keeps its configuration around but stops it from being evaluated,
which is useful when you want to temporarily turn off an automation without losing its configuration.

Order
-----

When a new Read the Docs version is created,
all rules with a successful match will have their action triggered,
in the order they appear on the :guilabel:`Automation Rules` page.

Examples
--------

Activate all new tags
~~~~~~~~~~~~~~~~~~~~~

- Match: ``Any version``
- Version type: ``Tag``
- Action: ``Activate version``

Activate only new branches that belong to the ``1.x`` release
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Custom match: ``^1\.\d+$``
- Version type: ``Branch``
- Action: ``Activate version``

Delete an active version when a branch is deleted
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Match: ``Any version``
- Version type: ``Branch``
- Action: ``Delete version``

Set as default new tags that have the ``-stable`` or ``-release`` suffix
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Custom match: ``-(stable|release)$``
- Version type: ``Tag``
- Action: ``Set version as default``

.. note::

   You can also create two rules:
   one to match ``-stable`` and other to match ``-release``.

Activate all new tags and branches that start with ``v`` or ``V``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Custom match: ``^[vV]``
- Version types: ``Tag``, ``Branch``
- Action: ``Activate version``

Activate all new tags that don't contain the ``-nightly`` suffix
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. TODO: update example if https://github.com/readthedocs/readthedocs.org/issues/6354 is approved.

- Custom match: ``.*(?<!-nightly)$``
- Version type: ``Tag``
- Action: ``Activate version``

Only build when documentation files change
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Match: ``Any version``
- Version types: ``Tag``, ``Branch``, ``Pull request``
- Changed files:

  .. code-block:: text

     docs/*
     .readthedocs.yaml
     requirements/docs.txt

- Action: ``Trigger build for version``

Skip builds for commits with ``[skip ci]`` in the message
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configure a single rule that triggers a build only when the commit message
does *not* contain ``[skip ci]``:

- Match: ``Any version``
- Version types: ``Tag``, ``Branch``, ``Pull request``
- Commit message: ``^(?!.*\[skip ci\]).*``
- Action: ``Trigger build for version``

Only build pull requests labeled with ``documentation``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Match: ``Any version``
- Version type: ``Pull request``
- Pull request labels: ``^documentation$``
- Action: ``Trigger build for version``
