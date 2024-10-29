Automation rules
================

Automation rules allow project maintainers to automate actions on new branches and tags in Git repositories.
If you are familiar with :term:`GitOps`,
this might seem familiar.
The goal of automation rules is to be able to control versioning through your Git repository
and avoid duplicating these efforts on Read the Docs.

.. seealso::

   :doc:`/guides/automation-rules`
     A practical guide to managing automated versioning of your documentation.

   :doc:`/versions`
     General explanation of how versioning works on Read the Docs

How automation rules work
-------------------------

When a new tag or branch is pushed to your repository,
Read the Docs receives a webhook.
We then create a new Read the Docs *version* that matches your new Git *tag or branch*.

All automation rules are evaluated for this version,
in the order they are listed.
If the version **matches** the version type and the pattern in the rule,
the specified **action** is performed on that version.

.. _TODO: A diagram would be great here in the future, but probably too much for this refactor.

.. note::

   Versions can match multiple automation rules,
   and all matching actions will be performed on the version.

Matching a version in Git
-------------------------

We have a couple predefined ways to match against versions that are created,
and you can also define your own.

Predefined matches
~~~~~~~~~~~~~~~~~~

Automation rules support two predefined version matches:

- **Any version**: All new versions will match the rule.
- **SemVer versions**: All new versions that follow `semantic versioning <https://semver.org/>`__
  (with or without a `v` prefix) will match the rule.

Custom matches
~~~~~~~~~~~~~~

If none of the above predefined matches meet your use case,
you can use a **Custom match**.

The custom match should be a valid `Python regular expression <https://docs.python.org/3/library/re.html>`__.
Each new version will be tested against this regular expression.

Actions for versions
--------------------

When an automation rule matches a new version,
the specified action is performed on that version.
Currently, the following actions are available:

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

There are a couple caveats to these rules that are useful:

*   The :term:`default version` isn't deleted even if it matches a rule.
    You can use the ``Set version as default`` action to change the default version
    before deleting the current one.
*   If your versions follow :pep:`440`,
    Read the Docs activates and builds the version if it's greater than the current stable version.
    The stable version is also automatically updated at the same time.
    See more in :doc:`versions`.

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
- Version type: ``Tag``
- Action: ``Activate version``

.. Force new line

- Custom match: ``^[vV]``
- Version type: ``Branch``
- Action: ``Activate version``

Activate all new tags that don't contain the ``-nightly`` suffix
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. TODO: update example if https://github.com/readthedocs/readthedocs.org/issues/6354 is approved.


- Custom match: ``.*(?<!-nightly)$``
- Version type: ``Tag``
- Action: ``Activate version``
