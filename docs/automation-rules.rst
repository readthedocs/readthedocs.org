Automation Rules
================

Automation rules allow you to execute some actions over new versions.

By default when new versions are created,
they are not activated.
If you want to activate it and do other type of actions,
you need to log in your Read the Docs account first.

Creating an automation rule
---------------------------

#. Go to your project :guilabel:`Admin` > :guilabel:`Automation Rules`
#. Click on "Add Rule" button
#. Fill in the fields

   - Description: A description of what the rule does
   - Match: What versions the rule should be applied to
   - Version type: What type of versions the rule should be applied to
   - Action: What action should be applied to matching versions

#. Click "Save"

How do they work?
-----------------

When a new tag or branch is pushed to your repository,
Read the Docs creates a new version.

All rules are run over this version in the order they are listed,
if the version matches the version type and the pattern in the rule,
an action is executed over that version.

.. note::
   
   All actions of the rules that the version matches will be executed over that version.

Predefined matches
------------------

There are some predefined matches:

- **Any version**: All new versions will match.
- **SemVer versions**: All new versions that follow `semantic versioning <https://semver.org/>`__ will match.

User defined matches
--------------------

If none of the above predefined matches meet your use case,
choose **Custom match**.

The custom match should be a valid `Python regular expression <https://docs.python.org/3/library/re.html>`__.
Each new version will be tested against this regular expression.

Actions
-------

Actions are the task to be executed over the matching version.
Currently, this actions are available:

- **Activate version**: Activates and builds the version.
- **Set version as default**: Sets the version as default,
  i.e. the version of your project that `/` redirects to.
  See more in :ref:`automatic-redirects:Root URL`.
  It also activates and builds the version.

.. note::
   
   If your versions follow :pep:`440`,
   Read the Docs activates and builds the version if it's greater than the current stable version,
   and updates the stable version.
   See more in :doc:`versions`.

Order
-----

The order your rules are listed in  :guilabel:`Admin` > :guilabel:`Automation Rules` matters.
Each action will be executed in that order,
so first rules have a higher priority.

You can change the order using the up and down arrow buttons.

.. note::

   New rules are added at the end (lower priority).

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

Set as default new tags that have the ``-stable`` or ``-release`` suffix
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Custom match: ``-(stable)|(release)$``
- Version type: ``Tag``
- Action: ``Set version as default``

.. note::
   
   You can also create two rules, one to match ``-stable`` and
   other to match ``-release``.

Activate all new tags and branches that start with ``v`` or ``V``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Custom match: ``^[vV]``
- Version type: ``Tag``
- Action: ``Activate version``


- Custom match: ``^[vV]``
- Version type: ``Branch``
- Action: ``Activate version``

Activate all new tags that don't contain the ``-nightly`` suffix
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. TODO: update example if https://github.com/readthedocs/readthedocs.org/issues/6354 is approved.


- Custom match: ``.*(?<!-nightly)$``
- Version type: ``Tag``
- Action: ``Activate version``
