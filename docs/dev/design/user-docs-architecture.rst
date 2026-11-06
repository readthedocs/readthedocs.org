User docs: one page per feature, sidebar by lifecycle
=====================================================

.. note::

   Proposal, October 2026. First steps are open as
   `PR 13461 <https://github.com/readthedocs/readthedocs.org/pull/13461>`_
   (custom domains merge) and
   `PR 13460 <https://github.com/readthedocs/readthedocs.org/pull/13460>`_
   (AI section).
   `PR 13451 <https://github.com/readthedocs/readthedocs.org/pull/13451>`_
   does the same thing for the integration docs.

The problem
-----------

Most features are documented twice: an overview page at the top level and a
how-to guide under ``guides/``. The two link to each other, and the reader
has to guess which one has the steps. Custom domains, subprojects, redirects,
pull requests, automation rules and environment variables all work this way.

The sidebar makes it worse. "How-to guides" is a second tree that repeats the
feature sections (``reproducible-builds`` is listed three times). The
sections themselves follow the codebase rather than the reader: Addons is
under "Project setup" while its parts are under "Reading" and "Maintaining",
and the AI pages are split across two sections. Underneath all of that are
orphaned ``tutorials/`` and ``explanation/`` index pages from an earlier
reorganization, hidden from the sidebar but still built.

The change
----------

Two things, in this order.

**1. One page per feature.** Merge each how-to guide into its feature page.
The merged page reads top to bottom: what the feature does, how to turn it
on, what the settings mean. It keeps the feature page's URL.

The pairs, feature page first:

- ``custom-domains`` and ``guides/custom-domains``
- ``subprojects`` and ``guides/subprojects``
- ``user-defined-redirects`` and ``guides/redirects``
- ``environment-variables`` and ``guides/environment-variables``
- ``offline-formats`` and ``guides/enable-offline-formats``
- ``build-notifications`` and ``guides/build/email-notifications``
- ``versions`` and ``guides/hiding-a-version``
- ``automation-rules`` and ``guides/automation-rules``
- ``pull-requests`` and ``guides/pull-requests``
- ``commercial/single-sign-on`` and the three SSO guides, as a tab per provider
- ``commercial/organizations`` and ``guides/manage-read-the-docs-teams``
- ``builds`` and ``continuous-deployment``
- ``config-file/index`` and ``explanation/configuration-file``
- ``guides/build-troubleshooting`` and ``guides/build-using-too-many-resources``

A feature with real variants, such as integration types, can grow sub-pages
under its feature page, as PR 13451 does. The feature page stays the entry
point: same URL, same place in the sidebar, sub-pages reached from it.

Delete the leftover index pages: ``tutorials/index`` and
``explanation/{index,advanced,methodology}``, which nothing links to, and
the eight ``guides/*/index`` sub-indexes and ``guides/index``, whose job the
sidebar does. Together with the merges, this takes 154 ``.rst`` files to
about 125 without moving any.

**2. Group the sidebar by what the reader is doing.** Eight sections, in
the order a project owner meets them, each one level deep:

- *Get started*: what Read the Docs is, add your project, choose your tool,
  tutorial, examples, moving from another platform (new; the website's
  comparison pages say why, these say how).
- *Documentation tools*: one page per tool. Sphinx's page lists the
  Sphinx-only guides (Intersphinx, Jupyter, custom CSS, and so on).
- *Build*: config file, build process, customization, pull request builds,
  environment variables, notifications, integrations, direct upload,
  troubleshooting.
- *Host*: versions and automation rules, custom domains, subprojects,
  translations, redirects, URLs, CDN.
- *Reader experience*: Addons, flyout, search, link previews, visual diff,
  offline formats, analytics.
- *AI and agents*: llms.txt, Markdown for agents, agent skills, main
  content detection.
- *Teams and organizations*: organizations, teams, single sign-on, sharing,
  subscriptions, accounts, security log.
- *Reference and help*: config file schema, environment variable reference,
  API, FAQ, support, changelog.

No "How-to guides" section. A how-to lives inside its feature.

What follows
------------

Once the sidebar is right, the front page stops being a hand-written copy of
it. It becomes one sentence, three ways in (add your project, choose your
tool, follow the tutorial), a card per section built from the same toctrees,
and a help strip. The company copy moves to About.

The dashboard already links each settings page to its docs, and today those
links show the problem: Domains links to both the custom domains guide and
the overview, Redirects to both of its pages, Environment variables to all
three. After the merges each pair collapses to one link. The links point at
the guide URLs, so every merged guide needs its redirect in place before the
docs PR merges, and ext-theme then updates the link to the feature page. The
settings menu has the same four groups as today's docs and can re-sort with
them into Setup, Build, Host and Readers, with feature page titles taking
the dashboard's labels ("Pull request builds", "Domains").

Not changing
------------

- Files and URLs. Pages stay where they are; only merged guides go away, each
  with a redirect.
- Content types as navigation. Tutorial, how-to, reference and explanation
  live inside a feature page, not beside it in the sidebar.
- Marketing copy. Pricing, Community vs Business and comparisons stay on
  about.readthedocs.com; the docs link to them.

Prior art
---------

- `Diátaxis <https://diataxis.fr/how-to-use-diataxis/#don-t-worry-about-structure>`_
  itself says not to split docs into four top-level sections ("Don't do
  that. It's horrible."). Our orphaned ``tutorials/`` and ``explanation/``
  indexes are that split, half done.
- `GitHub Actions <https://docs.github.com/en/actions>`_ did the split and has
  a 150-item index that only works because of a curated block of nine links.
- `Render <https://render.com/docs>`_ and `Netlify <https://docs.netlify.com/>`_
  group by what the reader is doing (Create, Configure, Operate; Start,
  Build, Deploy, Manage) with the settings pages inside one of those groups.
- `Plausible <https://plausible.io/docs>`_'s docs sidebar is its settings
  menu. It is small enough to get away with that; we aren't.
- `GitLab's contextual help pattern <https://design.gitlab.com/patterns/contextual-help/>`_
  sets the rules for the dashboard help links: link only when the help won't
  fit in the UI, phrase it as a question, open in a new tab.

Rollout
-------

Merge first, under today's sidebar. Change the sidebar once each feature has
one page.

1. Merge the pairs PR 13451 doesn't touch, one per PR: custom domains
   (PR 13461), subprojects, redirects, offline formats, build notifications,
   organizations, config file, build troubleshooting.
2. After PR 13451 merges, the rest: pull requests, automation rules,
   environment variables, hiding a version, builds, SSO.
3. Delete the orphans and the ``guides/*/index`` sub-indexes.
4. Rewrite ``index.rst`` into the eight sections and rebuild the front page
   from it. PR 13460 is an early piece of this step.
5. ext-theme: point each settings page's help links at the merged feature
   page (one link where there were two) and re-sort the settings menu.
6. Write "moving from" guides for the platforms the website compares
   against, and link them from the comparison pages.

Every merged guide gets an exact redirect in the docs project.
``sphinx-build -W`` catches broken references.

Open questions
--------------

- "Reader experience" or "Addons" as the section name.
- Integrations under Setup (PR 13451) or Build (dashboard today). One answer
  for both.
- Front-page cards generated from the toctrees, or written once by hand.
