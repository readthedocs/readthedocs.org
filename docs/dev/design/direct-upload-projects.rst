Direct upload projects
======================

This document proposes how a project declares whether Read the Docs builds its documentation
or whether the documentation is only uploaded through the :doc:`upload API <direct-artifacts-upload>`,
and what changes in the platform depending on that choice.

This document is based on the discussion call we had on 2026-09-23 and the onboarding proof of concept
that came out of it.

Goals
-----

- Let a new project start using direct upload from the "Add project" wizard,
  without Read the Docs creating versions, attaching webhooks or triggering builds that are guaranteed to fail.
- Make it obvious, in code and in the dashboard, whether a project is built by Read the Docs or by the user.
- Hide the parts of the dashboard that only make sense when Read the Docs builds the documentation.
- Keep supporting projects that build on Read the Docs and upload some versions.
- Give users a way to revert a version back to Read the Docs builds when they uploaded it by mistake.

Non-goals
---------

- A migration path from direct upload back to Read the Docs builders.
  Projects can go from Read the Docs builders to direct upload, not the other way around, for now.
- Redesigning the "Add project" wizard to stop creating ``latest`` and ``stable`` for every project.
  We agreed this is the right long term direction, but it is a separate project.
- Exposing the new field in the public API so new projects can be created as direct upload from the start.
  This will be proposed separately once this design is accepted.

Motivation
----------

The upload API was designed as a per-version feature:
a version becomes ``is_uploaded`` on its first successful upload and Read the Docs stops building it.
That works for a project that already builds on Read the Docs and uploads a version now and then.

It does not work for a project that never wants Read the Docs to build anything.
Creating such a project today triggers a build of ``latest`` that fails for lack of a configuration file,
the version sync creates and builds ``stable`` with the same result,
every push through the webhook produces another failing build,
and pull request builds are enabled by default.
The proof of concept worked around this by marking ``latest`` and ``stable`` as uploaded at import time,
which is fragile and still leaves the dashboard full of build settings that do nothing.

We also found ourselves unable to answer a simple question from the code or the dashboard:
is this project fully direct upload, or a mix?
Every feature that assumes a build exists needs that answer,
and deriving it from the versions is neither cheap nor reliable.

Project types
-------------

We distinguish two types of projects.

Built on Read the Docs
   The project works as it always has.
   Read the Docs syncs versions from the repository, builds them, and runs pull request builds.
   Any version can still be uploaded through the upload API,
   and that version becomes ``is_uploaded`` and stops being built by Read the Docs.
   This is the type for existing projects, and for new projects that pick "Build on Read the Docs" in the wizard.

Direct upload
   Read the Docs never builds, never syncs versions, and never attaches a webhook.
   All versions are created by the upload API.
   This is the type for new projects that pick "Build externally and upload" in the wizard,
   and for existing projects that switch once they finished migrating their pipeline.

.. list-table::
   :header-rows: 1

   * -
     - Built on Read the Docs
     - Direct upload
   * - Who builds
     - Read the Docs, plus uploads for any version
     - Only the user's pipeline
   * - Webhook and SSH key
     - Attached at import
     - Not attached
   * - Version sync
     - On webhooks and builds
     - Never
   * - Builds triggered by Read the Docs
     - Yes, except on versions with ``is_uploaded``
     - Never
   * - Uploads
     - Accepted, the version becomes ``is_uploaded``
     - Accepted

The build method setting
------------------------

The project type is stored on the project itself as a "build method" with two values,
"Build on Read the Docs" and "Build externally and upload".
The default is "Build on Read the Docs", so existing projects keep working unchanged.

It is a project setting, not something derived from the versions,
so that every feature can answer "does Read the Docs build this project?" with one lookup,
and so the dashboard can show the right thing before the project has any version.
It describes what the project does rather than what it disables,
which avoids confusion with the existing ways builds can be turned off for spam or repeated failures,
and leaves room for more values later if we need them.

The setting is stored:

- from the "Add project" wizard, based on the tab chosen on the configuration step;
- from the project settings, where a project built on Read the Docs can switch to direct upload.

The setting is not exposed in the API for now.
During the beta, the existing direct upload feature flag remains the gate,
and the wizard enables it on new direct upload projects.
The flag goes away when direct upload is available to everyone.

What direct upload turns off
----------------------------

Every way a build or a version sync can start already goes through a single place for each,
so the project type is checked there once, instead of at every trigger.
Any new trigger added in the future is covered automatically.

Builds
   Read the Docs never starts a build on a direct upload project.
   This covers pushes and pull requests arriving through webhooks and the GitHub App,
   builds requested through the API,
   the automatic build of ``stable`` when a new tag is promoted,
   automation rule actions,
   activating a version,
   changing the default branch,
   the first build after import,
   and the admin actions.
   Builds created by an upload are the only ones accepted.

Version sync
   Read the Docs never syncs versions from the repository on a direct upload project.
   This covers the sync on webhooks, the "Resync versions" button,
   and branch created or deleted events from the GitHub App.

Project import
   No webhook is attached and, on the commercial site, no SSH key is generated.
   The repository connection is kept, because commit statuses on uploaded pull request previews need it.
   No build is triggered and no version is created:
   ``latest`` is not created for direct upload projects,
   and ``stable`` only ever comes from the version sync, which does not run.
   Every version comes from an upload.
   The first branch or tag uploaded becomes the default version, so the root of the documentation works right away.
   Pull request previews never become the default.
   A dismissable notification on the project page tells the user which version became the default
   and links to the settings to change it.

Pull request builds
   The "Build pull requests for this project" setting becomes irrelevant, since webhooks no longer start builds.
   The setting is hidden and its value left alone, instead of being changed at import.

Automation rules
   Not run on direct upload projects for now, and the "Automation rules" page is hidden in their settings.
   Versions are managed from the user's pipeline, and anything a rule would do can be done through the API.
   On projects built by Read the Docs, an upload that creates a version runs the rules,
   the same way the repository sync does when it creates one.
   The action that triggers a build is skipped like any other build on an uploaded version.
   We plan to extend automation rules support for direct upload projects in the future,
   allowing users to define rules that react to uploads similarly to how they currently react to repository syncs.

Uploads
   On direct upload projects the uploaded name is the version, so a push to ``main`` publishes ``/en/main/``.
   There are no ``latest`` and ``stable`` aliases and no default branch concept:
   a user who wants them uploads versions with those names from the pipeline,
   for example an extra upload step named ``stable`` that only runs on tags.
   The user documentation shows how.
   On projects built by Read the Docs, an upload named after the default branch lands on ``latest``,
   the same way a push to that branch does.

Dashboard changes
-----------------

On a direct upload project the following is hidden or replaced.

- Settings menu, "Building" group: Integrations, Pull request builds and Environment variables are removed.
  Build notifications stay, because an upload can fail validation.
- Project settings form: "Default branch", "Path for .readthedocs.yaml", "Custom git clone command",
  "Disable builds after consecutive failures", "Build pull requests for this project"
  and "Privacy level of pull request previews" are removed.
  Everything else is hosting configuration and stays.
- Versions page: the "Activate a new version" form and the "Resync versions" button are removed,
  replaced by a note explaining that versions are created by uploading.
  Deactivating an uploaded version deletes it from the database, together with its files and search index.
  There is no inactive uploaded version: an upload creates the version active,
  and to serve it again after deactivating it, the user uploads it again.
  The action keeps its "Deactivate" name in the dashboard, and the confirmation explains that the version
  and its documentation are removed and that a new upload recreates it.
  This applies to uploaded versions on both project types.
- "Rebuild version" is removed everywhere it appears: builds list, versions list and build detail page.
  On projects built on Read the Docs, the control stays and is disabled with a tooltip on uploaded versions.
- The builds list keeps listing uploaded builds and their logs.
- Until a direct upload project has a built version,
  the versions list placeholder explains that the first version appears after the first upload
  and links to the user documentation.
  The "I need help" modal on the configuration step of the wizard shows the upload steps
  with the project slug filled in.

Migrating a project to direct upload
------------------------------------

The migration path from Read the Docs builders to direct upload is version by version,
and it already works today.
A project built on Read the Docs uploads one version, then another, and each uploaded version
stops being built by Read the Docs while the rest keeps working as before.
Nothing has to be decided up front, and the project can stay in that mixed state as long as it wants.

Once every version the project cares about is uploaded, the project switches to direct upload from its settings.
The settings page warns that Read the Docs will stop building and syncing versions, and that some settings will disappear.

On switching:

- The build method becomes "Build externally and upload".
- The webhook is removed from the repository.
- Inactive versions that were never uploaded are deleted.
  They only exist because of the version sync and would otherwise go stale.
- Active versions keep serving whatever they have, built or uploaded.
  Active versions built by Read the Docs are not deleted, but they will never be rebuilt;
  uploading them replaces their content.

Switching back to Read the Docs builders is not offered.
A resync would recreate the deleted versions, so a way back is possible later if real usage asks for it.

Reverting a version to Read the Docs builds
-------------------------------------------

On projects built on Read the Docs,
the version detail page shows an "Uploaded" checkbox,
only for versions that were uploaded.
Unchecking it and saving removes the uploaded files and triggers a build,
so the version is unavailable until that build succeeds and a failed build never leaves uploaded files being served.
The help text says so.

This is the way back for a user who uploaded a version manually and wants Read the Docs to build it again.
It does not prevent a later upload from marking the version as uploaded again.

Onboarding
----------

The "Add project" wizard keeps one repository selection flow under "Configure automatically".
The configuration step offers two tabs:

Build on Read the Docs
   The current page with the ``.readthedocs.yaml`` samples and the "This file exists" button.
   The tab carries a "Recommended" label, so the Read the Docs builders stay the default path.

Build externally and upload
   A short explanation that Read the Docs will not build the project,
   an "I need help" button opening a modal with the upload steps and snippets for GitHub Actions and the command line,
   and an "I will upload my documentation" button.

During the beta the second tab is shown to anyone opening the wizard with ``?direct_upload=1``.
The beta email, the documentation and a blog post carry that link.
The "Configure manually" flow does not offer direct upload for now.
