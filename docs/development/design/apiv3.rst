=======================
 APIv3 Design Document
=======================

This document describes the design,
some decisions already made and built (current Version 1 of APIv3)
and an implementation plan for next Versions of APIv3.

APIv3 will be designed to be easy to use and useful to perform read and write operations as the main two goals.

It will be based on Resources as APIv2 but considering the ``Project`` resource as the main one,
from where most of the endpoint will be based on it.

.. contents::
   :local:
   :backlinks: none
   :depth: 1


Goals
-----

* Easy to use for our users (access most of resources by ``slug``)
* Useful to perform read and write operations
* Authentication/Authorization

  * Authentication based on scoped-tokens
  * Handle Authorization nicely using an abstraction layer

* Cover most useful cases:

  * Integration on CI (check build status, trigger new build, etc)
  * Usage from public Sphinx/MkDocs extensions
  * Allow creation of flyout menu client-side
  * Simplify migration from other services (import projects, create multiple redirects, etc)


Non-Goals
---------

* Filter by arbitrary and non-useful fields

  * "Builds with ``exit_code=1``"
  * "Builds containing ``ERROR`` on their output"
  * "Projects created after X datetime"
  * "Versions with tag ``python``"

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

These are some features that we may want to build at some point.
Although, they are currently out of our near roadmap because they don't affect too many users,
or are for internal usage only.

* CRUD for Domain
* Add User as maintainer
* Give access to a documentation page (``objects.inv``, ``/design/core.html``)
* Internal Build process


Nice to have
------------

* ``Request-ID`` header
* `JSON minified by default`_ (maybe with ``?pretty=true``)
* `JSON schema and validation`_ with docs_


.. _JSON minified by default: https://geemus.gitbooks.io/http-api-design/content/en/responses/keep-json-minified-in-all-responses.html
.. _JSON schema and validation: https://geemus.gitbooks.io/http-api-design/content/en/responses/keep-json-minified-in-all-responses.html
.. _docs: https://geemus.gitbooks.io/http-api-design/content/en/artifacts/provide-human-readable-docs.html
