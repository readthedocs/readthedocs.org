=======================
 APIv3 Design Document
=======================

This document describes the design,
some decisions already made and an implementation plan for APIv3 in stages.

APIv3 will be designed to be easy to use and useful to perform read and write operations as the main two goals.

It will be based on Resources as APIv2 but considering the ``Project`` resource as the main one,
from where most of the endpoint will be based on it.

.. contents::
   :local:
   :backlinks: none
   :depth: 1


Goals
-----

* Easy to use for our users
* Useful to perform read and write operations
* Cover most useful cases


Non-Goals
---------

* Filter by arbitrary and non-useful fields
* Cover *all the actions* available from the WebUI


Problems with APIv2
-------------------

There are several problem with our current APIv2 that we can list:

* No authentication
* It's read-only
* Not designed for slugs
* Useful APIs not exposed (only for internal usage currently)
* Error reporting is a mess
* Relationships between API resources is not obvious
* Footer API endpoint returns HTML


Implementation stages
---------------------

Version 1
+++++++++

The first implementation of APIv3 will cover the following aspects:

.. note::

   This is currently implemented and live. Although, it's only for internal testing.

* Authentication

  * all endpoints require authentication via ``Authorization:`` request header
  * detail endpoints are available for all authenticated users
  * only Project's maintainers can access listing endpoints
  * personalized listing

* Read and Write

  * edit attributes from Version (only ``active`` and ``privacy_level``)
  * trigger Build for a specific Version

* Accessible by slug

  * Projects are accessed by ``slug``
  * Versions are accessed by ``slug``
  * ``/projects/`` endpoint is the main one and all of the other are nested under it
  * Builds are accessed by  ``id``, as exception to this rule
  * access all (active/non-active) Versions of a Project by ``slug``
  * get latest Build for a Project (and Version) by ``slug``
  * filter by relevant fields

* Proper status codes to report errors

* Browse-able endpoints

  * browse is allowed hitting ``/api/v3/projects/`` as starting point
  * ability to navigate clicking on other resources under ``_links`` attribute

* Rate limited


Version 2
+++++++++

Second iteration will polish issues found from the first step,
and add new endpoints to allow *import a project and configure it*
without the needed of using the WebUI as a main goal.

After Version 2 is deployed,
we will invite users that reach us as beta testers to receive more feedback
and continue improving it by supporting more use cases.

This iteration will include:

* Minor changes to fields returned in the objects
* Import Project endpoint
* Edit Project attributes ("Settings" and "Advanced settings-Global settings" in the WebUI)
* Trigger Build for default version
* Allow CRUD for Redirect, Environment Variables and Notifications (``WebHook`` and ``EmailHook``)
* Documentation


Version 3
+++++++++

Third iteration will implement granular permissions.
Keeping in mind how Sphinx extension will use it:

* ``sphinx-version-warning`` needs to get *all active Versions of a Project*
* An extension that creates a landing page, will need *all the subprojects of a Project*

To fulfill these requirements, this iteration will include:

* Scope-based authorization token


Version 4
+++++++++

* Specific endpoint for our flyout menu (returning JSON instead of HTML)


Out of roadmap
--------------

These are some features that we may want to build but they are not in the roadmap at this moment:

* CRUD for Domain
* Add User as maintainer
* Give access to a documentation page (``objects.inv``, ``/design/core.html``)
* Internal Build process


Open questions
--------------

There are some questions that we still have.
These will need more discussion before making a decision on where,
when and how to implement them.

* Do we want to add ``/api/v2/sustainability/`` to APIv3?
  Should be part of the new "Ad Server" that we are building?
* Should we make our search endpoint at ``/api/v2/search`` publicly on APIv3?


Nice to have
------------

* ``Request-ID`` header
* `JSON minified by default`_ (maybe with ``?pretty=true``)
* `JSON schema and validation`_ with docs_


.. _JSON minified by default: https://geemus.gitbooks.io/http-api-design/content/en/responses/keep-json-minified-in-all-responses.html
.. _JSON schema and validation: https://geemus.gitbooks.io/http-api-design/content/en/responses/keep-json-minified-in-all-responses.html
.. _docs: https://geemus.gitbooks.io/http-api-design/content/en/artifacts/provide-human-readable-docs.html
