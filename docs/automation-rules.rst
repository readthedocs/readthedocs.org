Automation Rules
================

By default when new versions are created,
they are not activated.
So, when a new tag or branch is pushed to your repository,
you need to log in your Read the Docs account to activate it or
do other type of actions over that version.

To help to automate this tasks you can create an automation rule.

#. Go to your project :guilabel:`Admin` > :guilabel:`Automation Rules`
#. Click on "Add Rule" button
#. Fill in the fields

   - Description: A description of what the rule does
   - Match: What versions the rule should be applied to
   - Version type: What type of versions the rule should be applied to
   - Action: What action should be applied to matching rules

#. Click "Save"

Match
-----

New versions are matched against the type of match you chose:

- **All versions**: All new versions.
- **SemVer versions**: All new versions that follow `semantic versioning <https://semver.org/>`__.
- **Custom match**: If none of the above rules match your use case,
  you can write a regular expression.

Custom match
~~~~~~~~~~~~

The custom match should be a valid `Python regular expression <https://docs.python.org/3/library/re.html>`__.
Each new version is going to be tested against this regular expression,
if it matches the corresponding action is executed against that version.

Actions
-------

Currently we only support the following actions:

- **Activate version on match**: It activates and builds the version.
- **Set as default version on match**: It activates and builds the version too.
  Additionally, it sets the version as default,
  i.e. the version of your project that `/` redirects to.
  See more in :ref:`automatic-redirects:Root URL`.

.. note::
   
   If your versions follow :pep:`440`,
   Read the Docs activates and builds the version if it's greater than the current stable version.
   See more in :doc:`versions`.

Order
-----

The order your rules are listed in  :guilabel:`Admin` > :guilabel:`Automation Rules` matters.
Each action will be executed in that order,
so first rules have a higher priority.

You can change the order using the up and down arrow buttons.

.. note::
   
   All actions of the rules that the version matches will be executed over that version.

Examples
--------

Activate all new tags
~~~~~~~~~~~~~~~~~~~~~

- Match: ``All versions``
- Version type: ``Tag``
- Action: ``Activate version on match``

Activate only new branches that belong to the ``1.x`` release
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Custom match: ``^1\.\d+$``
- Version type: ``Branch``
- Action: ``Activate version on match``

Set as default new tags that have the ``-stable`` or ``-release`` suffix
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Custom match: ``-(stable)|(release)$``
- Version type: ``Branch``
- Action: ``Set as default version on match``

.. note::
   
   You can also create two rules, one to match ``-stable`` and
   other to match ``-release``.

Activate all new tags and branches that start with ``v`` or ``V``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Custom match: ``^[vV]``
- Version type: ``Tag``
- Action: ``Activate version on match``


- Custom match: ``^[vV]``
- Version type: ``Branch``
- Action: ``Activate version on match``

Activate all new tags that don't contain the ``-nightly`` suffix
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Custom match: ``.*(?<!-nightly)$``
- Version type: ``Tag``
- Action: ``Activate version on match``
