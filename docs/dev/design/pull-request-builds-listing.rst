Pull request builds listing page
================================

This document describes a new :guilabel:`Pull requests` tab in the project dashboard
that lists open pull requests and the status of their latest build.

.. contents:: Contents
   :local:
   :backlinks: none
   :depth: 1

Problem
-------

Pull request builds are invisible in the dashboard until you land on a single build page.
The project overview only lists branches and tags,
the project list on the user dashboard only shows the last branch build,
and the build list hides pull request builds behind a dropdown filter.

The result is that a maintainer who wants to know
"which of my open pull requests have a docs preview, and did it build?"
has no page to go to.
They find out from the commit status on GitHub or GitLab, or not at all.

Two issues describe the same gap from the build page side:
clicking a pull request from a build leads to an empty list
(`ext-theme #505 <https://github.com/readthedocs/ext-theme/issues/505>`_,
`readthedocs.org #13065 <https://github.com/readthedocs/readthedocs.org/issues/13065>`_).
The original :doc:`pull request builder design <pr-builder>` also listed
a "PR builds" tab in the project dashboard as part of its scope,
but that part was never built.

Goals
-----

Give every project a page that answers one question:
what is the state of my open pull requests' docs previews?

* Show open pull requests and the status of their latest build in one list, without any filtering.
* Make it one click from a pull request to its preview and to its build history.
* Make in-progress builds obvious, so people can tell "building" from "broken".
* Reuse the look and feel of the existing versions and builds lists, so the page needs no explanation.

Not in scope for the first version:

* Live updating without a page reload.
* Cross-project views on the user dashboard.
* Changes to how pull requests are opened, closed, or cleaned up in the backend.

Proposed UX
-----------

A new :guilabel:`Pull requests` tab in the project header,
next to :guilabel:`Versions` and :guilabel:`Builds`,
with a count of open pull requests in its label.
The page lives at ``/projects/<slug>/pull-requests/``
and uses the same list layout as the versions page,
so nothing about it needs to be learned.

.. figure:: /_static/images/design-docs/pull-request-builds/list.png
   :target: /_static/images/design-docs/pull-request-builds/list.png

   Mockup of the :guilabel:`Pull requests` tab with four open pull requests:
   one building, two built, one failed.
   Rendered with the dashboard's own styles.

Each row is one open pull request, newest activity first:

.. list-table::
   :header-rows: 1
   :widths: 20 45 35

   * - Element
     - What it shows
     - Where it goes
   * - Status icon
     - Latest build result: success, failure, cancelled, or a spinner while building.
     - Build detail page.
   * - Title
     - "Pull request #123" (or "Merge request #123" on GitLab).
     - The pull request on GitHub or GitLab.
   * - Subtitle
     - "Built 5 minutes ago", "Building", or "Build failed 2 hours ago".
     - Build detail page.
   * - Pull request title
     - The title from GitHub or GitLab, saved when the webhook arrives.
     - The pull request on GitHub or GitLab.
   * - View docs
     - Opens the preview, shown only when the latest build succeeded.
     - The preview site.
   * - Builds
     - All builds for this pull request.
     - Build list, filtered to this pull request.
   * - Rebuild
     - Starts a new build of the latest commit, project admins only.
     - Stays on the page, the row shows the new build.

Builds that are still running sort to the top,
so an active list reads as "what is happening now" before "what already finished".

Empty states:

* Pull request builds are enabled but nothing is open:
  "No open pull requests. Previews appear here when a pull request is opened."
* Pull request builds are disabled:
  a short note with a link to the :guilabel:`Pull request builds` settings page.
  Only project admins see the link.
* The project is not connected to GitHub or GitLab:
  the tab is hidden, since pull request builds cannot exist.

.. figure:: /_static/images/design-docs/pull-request-builds/empty.png
   :target: /_static/images/design-docs/pull-request-builds/empty.png

   Empty state when no pull requests are open.

.. figure:: /_static/images/design-docs/pull-request-builds/disabled.png
   :target: /_static/images/design-docs/pull-request-builds/disabled.png

   Empty state when pull request builds are turned off,
   with a button to the settings page.

Behavior
--------

**What counts as active.**
A pull request is listed while its version is in the ``open`` state.
Closing or merging the pull request removes it from the list immediately,
even though the version and its builds stay around for 90 days before cleanup.
The list is about open pull requests, not about the whole 90-day history.

**Who can see it.**
Anyone who can see the project sees the tab.
The rows follow the project's pull request privacy level:
if previews are private, only project members see them,
exactly as the build list behaves today.

**Ordering.**
Rows sort by the latest build's start time, newest first.
Running builds always sort above finished ones.

**Links into the build list.**
The :guilabel:`Builds` action on a row opens the existing build list filtered to that pull request.
This same link is used from the build detail page,
which fixes the empty list bug in ext-theme #505.

**Counts.**
The tab label counts open pull requests, not builds.
A pull request with five builds counts once.

Implementation sketch
---------------------

The page is mostly assembly of parts that already exist.
The build list and version list already know how to render a pull request row,
a status icon, and a build chip.

readthedocs.org
~~~~~~~~~~~~~~~

* A new project view that lists open pull request versions with their latest build,
  using the existing public-versions queryset so privacy rules apply unchanged.
* Save the pull request title on the version when the webhook creates or updates it.
  One new field and migration.
* Let the build list's version filter accept pull request versions,
  so :guilabel:`Builds` on a row and the link from the build detail page both work.
* A URL and a tab count for the project header.

ext-theme
~~~~~~~~~

* The tab in the project header and a list template built on the shared list layout,
  reusing the pull request markup from the build list and the version chip.
* The empty states described above.
* The :guilabel:`Rebuild` action, reusing the rebuild web component from the build list.
* Repoint the pull request link on the build detail page to the filtered build list.

One migration for the pull request title.
No API changes.

Decisions
---------

* The tab is always shown.
  When pull request builds are off it shows the empty state with a link to settings, rather than hiding.
* Each row has a :guilabel:`Rebuild` action for project admins.
* Store the pull request title on the version, so a row reads as more than a number.
* Closed pull requests are not shown in the first version.
* No link to a version detail page for now.
* No commit chip on the row.
  The commit is one click away on the build page and adds noise here.

Follow-ups once the page ships:

* A "Show closed" toggle for pull requests closed in the last 90 days.
* Live status updates on the list, using the same polling the build detail page already does.
* A count of open pull requests on each project row of the user dashboard, linking to this page.

Related issues
--------------

.. list-table::
   :header-rows: 1
   :widths: 45 15 40

   * - Issue
     - State
     - Relevance
   * - `ext-theme #505 <https://github.com/readthedocs/ext-theme/issues/505>`_
       Builds: filter by PR version shows empty list
     - Open
     - Fixed by the build list filter change in this design.
   * - `ext-theme #742 <https://github.com/readthedocs/ext-theme/issues/742>`_
       Add version detail page
     - Open
     - Possible future link target for a pull request row.
   * - `readthedocs.org #13065 <https://github.com/readthedocs/readthedocs.org/issues/13065>`_
       Builds: allow filtering by pull request ID
     - Closed as duplicate of #505
     - Same request from the build page side.
   * - `ext-theme #158 <https://github.com/readthedocs/ext-theme/issues/158>`_
       Builds: list filtering and PR builds bugs
     - Closed
     - Noted there is no entry point to pull request builds besides a build page.
   * - `ext-theme #40 <https://github.com/readthedocs/ext-theme/issues/40>`_
       Add pull request build filter to version list and build list
     - Closed
     - Added the current build list filter.
