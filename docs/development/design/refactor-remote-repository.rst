======================================
 Refactor ``RemoteRepository`` object
======================================


This document describes the current usage of ``RemoteRepository`` objects and proposes a new normalized modeling.


Goals
=====

* De-duplicate data stored in our database.
* Save only one ``RemoteRepository`` per GitHub repository.
* Use an intermediate table between ``RemoteRepository`` and ``User`` to store associated remote data for the specific user.
* Make this model usable from our SSO implementation (adding ``remote_id`` field in ``Remote`` objects).
* Use Post ``JSONField`` to store associated ``json`` remote data.
* Make ``Project`` connect directly to ``RemoteRepository`` without being linked to a specific ``User``.
* Do not disconnect ``Project`` and ``RemoteRepository`` when a user delete/disconnects their account.


Non-Goals
=========

* Keep ``RemoteRepository`` in sync with GitHub repositories.
* Delete ``RemoteRepository`` objects deleted from GitHub.
* Listen to GitHub events to detect ``full_name`` changes and update our objects.

.. note::

   We may need/want some of these non-goals in the future.
   They are just outside the scope of this document.


Current Implementation
======================

When a user connect their account to a social account, we create a

* ``allauth.socialaccount.models.SocialAccount``
  * basic information (provider, last login, etc)
  * provider's specific data saved in a JSON under ``extra_data``
* ``allauthsocialaccount.models.SocialToken``
  * token to hit the API on behalf the user


We *don't create* any ``RemoteRepository`` at this point.
They are created when the user jumps into "Import Project" page and hit the circled arrows.
It triggers ``sync_remote_repostories`` task in background that updates or creates ``RemoteRepositories``,
but **it does not delete** them (after `#7183`_ and `#7310`_ got merged, they will be deleted).
One ``RemoteRepository`` is created per repository the ``User`` has access to.

.. note::

   In corporate, we are automatically syncing ``RemoteRepository`` and ``RemoteOganization``
   at signup (foreground) and login (background) via a signal. We should eventually move these to community.


.. _sync_remote_repositoies: https://github.com/readthedocs/readthedocs.org/blob/56253cb786945c9fe53a034a4433f10672ae8a4f/readthedocs/oauth/tasks.py#L25-L43
.. _#7183: https://github.com/readthedocs/readthedocs.org/pull/7183
.. _#7310: https://github.com/readthedocs/readthedocs.org/pull/7310


Where ``RemoteRepository`` is used?
===================================

* List of available repositories to import under "Import Project"
* Show a "+", "External Arrow" or a "Lock" sign next to the element in the list
  * +: it's available to be imported
  * External Arrow: the repository is already imported (see `RemoteRepository.matches`_ method)
  * Lock: user doesn't have (admin) permissions to import this repository (uses ``RemoteRepository.private`` and ``RemoteRepository.admin``)
* Avatar URL in the list of project available to import
* `Update webhook`_ when user clicks "Resync webhook" from the :guilabel:`Admin` > :guilabel:`Integrations` tab
* `Send build status`_ when building Pull Requests


.. _RemoteRepository.matches: https://github.com/readthedocs/readthedocs.org/blob/56253cb786945c9fe53a034a4433f10672ae8a4f/readthedocs/oauth/models.py#L182-L204
.. _Update webhook: https://github.com/readthedocs/readthedocs.org/blob/56253cb786945c9fe53a034a4433f10672ae8a4f/readthedocs/oauth/utils.py#L26-L62
.. _Send build status: https://github.com/readthedocs/readthedocs.org/blob/56253cb786945c9fe53a034a4433f10672ae8a4f/readthedocs/projects/tasks.py#L1852-L1956


New Normalized Implementation
=============================

The ``ManyToMany`` relation ``RemoteRepository.users`` will be changed to be ``ManyToMany(through='RemoteRelation')``
`to add extra fields in the relation`_ that are specific only for the User.
Allows us to have *only one* ``RemoteRepository`` per GitHub repository with multiple relationships to ``User``.

.. _to add extra fields in the relation: https://docs.djangoproject.com/en/2.2/topics/db/models/#extra-fields-on-many-to-many-relationships

With this modeling, we can avoid the disconnection ``Project`` and ``RemoteRepository`` only by removing the ``RemoteRelation``.

.. note::

   All the points mentioned in the previous section may need to be adapted to use the new normalized modeling.
   However, it may be only field renaming or small query changes over new fields.


Use this modeling for SSO
-------------------------

We can get the list of ``Project`` where a user as access:

.. code-block:: python

   admin_remote_repositories = RemoteRepository.objects.filter(
       users__contains=request.user,
       users__remoterelation__admin=True,  # False for read-only access
   )
   Project.objects.filter(remote_repository__in=admin_remote_repositories)


Rollout Plan
============

Due the constraints we have in the ``RemoteRepository`` table and its size,
we can't just do the data migration at the same time of the deploy.
Because of this we need to be more creative here and find a way to re-sync the data from VCS providers,
while the site continue working.

To achieve this, we thought on following this steps:

1. modify all the Python code to use the new modeling in .org and .com (will help us to find out bugs locally in an easier way)
1. QA this locally with test data
1. enable Django signal to re-sync RemoteRepository on login async (we already have this in .com). New active users will have updated data immediately
1. spin up a new instance with the new refactored code
1. run migrations to create a new table for `RemoteRepository`
1. re-sync everything from VCS providers into the new table for 1-week or so
1. dump-n-load `Project - RemoteRepository` relations
1. create a migration to use the new table with synced data
1. deploy new code once the sync is finished

See these issues for more context:
* https://github.com/readthedocs/readthedocs.org/pull/7536#issuecomment-724102640
* https://github.com/readthedocs/readthedocs.org/pull/7675#issuecomment-732756118
