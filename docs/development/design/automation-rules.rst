Automation Rules
================

Automation rules allow users to apply some actions over new or deleted versions.
See :doc:`/automation-rules` for more details of the current features.

This document explore some ideas to expand automation rules to automate more tasks.

Current state and limitations
-----------------------------

- Matches are done using regular expressions.
  But the models were designed so other type of matches can be implemented
  (like comparing the version with the highest semver version).
- Automation rules are meant to automate existing actions,
  so an action shouldn't be able to be triggered only inside an automation rule.
  This is so users aren't blocked if a rule didn't match a version,
  or if they need to execute the action over existing versions.
- Automation rules are currently matched against new versions,
  but they can also be executed over deleted versions (https://github.com/readthedocs/readthedocs.org/pull/7644).

Improvements
------------

Keep track of the ``n`` latest matches
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We do this with webhook exchanges (keeping the latest 10)
https://github.com/readthedocs/readthedocs.org/blob/f5b76e87a3b970d42228f5972ae9a50364c3c76c/readthedocs/integrations/models.py#L99-L111.
See https://github.com/readthedocs/readthedocs.org/issues/6393.

Live feedback of versions that match a rule
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When creating/editing a rule, it would be useful to know what versions are going to match.
We could list the current versions that match and/or allow the user to enter a custom input.
A new enpoint in api v2/v3 should be added.

Easy way to invert a match
~~~~~~~~~~~~~~~~~~~~~~~~~~

Currently, users need to write a negative look ahead,
which isn't really user-friendly or easy to remember/write.
Having an explicit option to invert a match would be more useful,
see https://github.com/readthedocs/readthedocs.org/issues/6354.

New features
------------

Change the privacy level of external versions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In Read the Docs for business all versions are private by default.
Some users may want to change the privacy level of external versions.
See https://github.com/readthedocs/readthedocs-corporate/issues/1063.

If automation rules are going to be used, users will need to be able to edit those versions.
This means having a place to list all external versions and allow to edit some properties,
privacy level is the only option that makes sense maybe also allow to de-activate it so docs aren't accessible.

Decide what PRs should be built
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use automation rules to decide which pull requests should be built,
this is for example only built branches that are going to be merged against an specific branch.
Or branch names that match a pattern, like (``^docs/.*``).

.. note::

   Here we don't need a separate UI element yet,
   as users can still trigger a new build by pushing to that branch if they got the pattern wrong.

Change the slug a version served from
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Currently, we create the version slug from the version name, and this can't be changed.
Some users may end up with a slug they didn't intend,
Or there are users that want their slug to be different from the name of the branch/tag,
such as https://github.com/readthedocs/readthedocs.org/issues/7078.

The models from automation rules already support passing enxtra arguments to be used by an action.
Before implementing this rule, we need to allow adding an alias for versions manually,
this would be by creating an alias (should the version be served from two slugs?)
or by allowing to change the slug of the version (less code to change).
See https://github.com/readthedocs/readthedocs.org/issues/5318,
and https://github.com/readthedocs/readthedocs.org/pull/6273.

Set a version as stable
~~~~~~~~~~~~~~~~~~~~~~~

Internally we create a version named ``stable`` pointing to the commit of the latest semver tag or branch,
see https://github.com/readthedocs/readthedocs.org/blob/f5b76e87a3b970d42228f5972ae9a50364c3c76c/readthedocs/api/v2/views/model_views.py#L246-L246
Currently, users can create a version named stable to override this version.

If we implement this rule,
we need to implement a way to set a version as stable,
maybe similar to the option ``default version`` (if empty we select stable based on latest semver version).
This can also be done in a more general way using aliases,
but we'll need to change the logic when syncing versions to not lose the slug (see above section).

See https://github.com/readthedocs/readthedocs.org/issues/5319.
