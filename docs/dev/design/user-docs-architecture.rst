User docs navigation and content structure
==========================================

.. note::

   Proposal, October 2026. The first steps are open as
   `PR 13461 <https://github.com/readthedocs/readthedocs.org/pull/13461>`_
   (custom domains merge) and
   `PR 13460 <https://github.com/readthedocs/readthedocs.org/pull/13460>`_
   (AI section). The integration docs restructure in
   `PR 13451 <https://github.com/readthedocs/readthedocs.org/pull/13451>`_
   applies the same ideas to one feature.

Summary
-------

Organize the user docs around what a project owner is doing: get started,
pick a tool, build, host, improve the reading experience, serve AI agents,
run a team. Eight sidebar sections, one page per feature that holds the
concept, the setup steps and the settings together, and a front page that
is a map of those sections and nothing else. No files move; the change is
in ``index.rst`` toctrees and in merging pages that cover the same feature.

Problem
-------

Readers meet three overlapping structures at once:

- **Two pages per feature.** Custom domains, subprojects, redirects, pull
  requests, automation rules and environment variables each have an overview
  at the top level and a how-to twin under ``guides/`` (environment variables
  has three pages). The two link to each other with ``seealso`` blocks, and the
  reader guesses which one holds the steps.
- **A second navigation tree that repeats the first.** "How-to guides" has
  eight sub-indexes listing about 40 pages, most already in the feature
  sections. ``reproducible-builds`` appears three times, ``hiding-a-version``
  and the SEO guide twice. Two sub-indexes hold two pages each.
- **A third, hidden structure.** ``tutorials/index``, ``explanation/index``
  and ``explanation/*`` are ``:orphan:`` leftovers of a Diátaxis layout that
  was started and then taken out of the sidebar.
- **Sections follow the codebase, not the reader.** Addons is one page under
  "Project setup" while its parts (flyout, search, link previews, visual diff,
  analytics) sit under "Reading documentation" and "Maintaining projects".
  AI pages are split between "Hosting" and "Maintaining". "Maintaining
  projects" holds redirects, badges, security log, custom script, agent
  skills and advice on doc structure.
- **The front page repeats the sidebar by hand.** Nine hidden toctrees and
  nine handwritten lists cover the same pages, so every change is made twice.
- **Getting started leads with one tool.** The 600-line tutorial is
  Sphinx-only but is the first link; the ten-tool picker is second.

Design
------

Four rules. A page that doesn't fit them changes; the rules don't.

**1. Navigation by lifecycle.** Eight sections, in the order a project owner
meets them. The sidebar shows each section one level deep:

- *Get started*: what Read the Docs is, add your project, choose your tool,
  tutorial, examples, moving from another platform.
- *Documentation tools*: one page per tool (Sphinx, MkDocs, Docusaurus,
  Zensical, Starlight, VitePress, Antora, mdBook, MyST, Markdoc). The Sphinx
  page's own toctree lists the eight Sphinx-only guides (Intersphinx,
  cross-referencing, Jupyter, custom CSS, edit links, PDF Unicode,
  translations, rST to MyST). Tool-specific content lives nowhere else.
- *Build*: config file, build process and customization, pull request
  builds, environment variables, notifications and badges, integrations,
  direct upload, skip and cancel rules, reproducible builds, Conda,
  monorepos, private dependencies, troubleshooting.
- *Host*: versions (with automation rules and versioning schemes), custom
  domains, subprojects, translations, redirects, URL prefixes, canonical
  URLs, CDN, sitemaps, robots, 404.
- *Reader experience*: Addons as the landing: flyout, search, link previews,
  doc notifications, visual diff, offline formats, embedding, custom script,
  traffic and search analytics.
- *AI and agents*: llms.txt, Markdown for agents, agent skills, main content
  detection.
- *Teams and organizations*: organizations, teams and maintainers, single
  sign-on, sharing, privacy levels, subscriptions, accounts and 2FA,
  security log. Business-only pages are marked, not segregated.
- *Reference and help*: ``.readthedocs.yaml`` schema, environment variable
  reference, API, glossary, FAQ, support, security, policies, changelog, about.

There is no "How-to guides" section and no section per content type.

**2. One page per feature.** A feature page answers, in order: what it does,
how to turn it on, what the settings mean. The how-to twin merges into it and
the feature page keeps its URL. Reference-grade detail (the full config
schema, every environment variable, the API) stays in Reference and is
linked from the page. A feature with real variants (integration types, SSO
providers) grows sub-pages under the feature page, as PR 13451 does for
integrations. The feature page stays the one entry point: same URL, same
place in the sidebar, and the sub-pages are reached from it rather than
listed beside it. A reader or a dashboard link lands in the same place
whether the feature is one page or ten. Custom domains, redirects and
subprojects are one page each.

Merges, feature page first: ``custom-domains`` ← ``guides/custom-domains``;
``subprojects`` ← ``guides/subprojects``; ``user-defined-redirects`` ←
``guides/redirects``; ``environment-variables`` ←
``guides/environment-variables``; ``offline-formats`` ←
``guides/enable-offline-formats``; ``build-notifications`` ←
``guides/build/email-notifications``; ``versions`` ←
``guides/hiding-a-version``; ``automation-rules`` ←
``guides/automation-rules``; ``pull-requests`` ← ``guides/pull-requests``;
``commercial/single-sign-on`` ← the three SSO guides, as a tab per provider;
``commercial/organizations`` ← ``guides/manage-read-the-docs-teams``;
``builds`` ← ``continuous-deployment``; ``config-file/index`` ←
``explanation/configuration-file``; ``guides/build-troubleshooting`` ←
``guides/build-using-too-many-resources``.

Deleted, since nothing links to them: ``tutorials/index``,
``explanation/{index,advanced,methodology}``, the eight ``guides/*/index``
sub-indexes and ``guides/index``. That takes 154 pages to about 125 without
moving any.

**3. Dashboard and docs use the same words.** The project settings menu in
ext-theme has the same four groups as today's docs (Setup, Building, Hosting,
Maintaining) and should re-sort with them into *Setup, Build, Host, Readers*,
a subset of the eight sections. Automation rules moves to Host because it
manages versions; "Maintaining" goes away. Feature page titles take the
dashboard's labels ("Pull request builds", "Domains", "Integrations"), with
the marketing phrase in the first sentence rather than the title. Every
settings page's empty ``project_edit_sidebar`` block gets one link to its
feature page, phrased as a question ("How do custom domains work?"). One page
per feature is what makes that link possible.

**4. Front page is the sitemap.** ``index.rst`` becomes one sentence, three
ways in (*Add your project*, *Choose your tool*, *Follow the tutorial*),
eight section cards built from the same toctrees the sidebar uses, and a help
strip (FAQ, troubleshooting, support, latest changelog entry). The company
copy moves to About. Nothing exists only on the front page.

Non-goals
---------

- **Moving files.** Pages keep their paths and URLs. A folder convention for
  new content (PR 13451's ``projects/<name>/``) is a separate decision and
  this design works with or without it.
- **Finishing the Diátaxis split.** Content types live inside a feature page,
  not beside it in the navigation.
- **Marketing copy.** Community vs Business, pricing and "why us" stay on
  about.readthedocs.com; the docs link to them.

Prior art
---------

Read in October 2026. The pattern is common; these are the clearest cases.

- `Diátaxis: workflow <https://diataxis.fr/how-to-use-diataxis/#don-t-worry-about-structure>`_.
  Diátaxis's own guidance is not to divide the docs into four top-level
  sections ("Don't do that. It's horrible.") and to treat the four types as
  "a guide, not a plan" that changes structure "from the inside". Our
  orphaned ``tutorials/`` and ``explanation/`` indexes are the top-level
  version it warns against. Rule 2 is the inside version.
- `GitHub Actions docs <https://docs.github.com/en/actions>`_ is the
  counter-example in practice: Concepts / How-tos / Reference / Tutorials at
  the top produce a 150-item index that only works because of a curated
  "Recommended" block of nine.
- `Render <https://render.com/docs>`_: front page by verb (Create, Configure,
  Operate), three cards each holding three or four links; settings tabs
  mirrored under Configure. The closest match to rules 1 and 4.
- `Netlify <https://docs.netlify.com/>`_: sidebar by lifecycle (Start, Build,
  Deploy, Manage, Extend, Reference) with a settings-shaped *Manage* group
  (Accounts & Billing, Projects, Domains, Security & access) inside it.
- `Plausible <https://plausible.io/docs>`_: the docs sidebar *is* the app's
  settings menu (Website settings, Stats dashboard, Goals, Account, Team,
  Billing). Works because the product is small; it is rule 3 taken to its limit.
- `GitBook <https://gitbook.com/docs>`_: "How do you want to work?" (editor,
  agent, code), then Create, Collaborate, Publish, Improve. Lifecycle verbs
  rather than product areas.
- `Stripe <https://docs.stripe.com/>`_: "Start here" by use case, then browse
  by product, with product sections matching the Dashboard's sections.
- `GitLab Pajamas: contextual help <https://design.gitlab.com/patterns/contextual-help/>`_:
  rules for UI-to-docs links (link only when the help won't fit, open in a new
  tab, phrase as a question, "Learn more" sparingly). The standard for the
  ext-theme help links in rule 3.
- `Comparison pages on about.readthedocs.com <https://about.readthedocs.com/comparisons/>`_:
  seven "why" pages that end with generic setup steps. The docs own the
  "how" (moving from GitBook, GitHub Pages, Netlify, ...) and the two link to
  each other.

Rollout
-------

Merge pages first, under the sidebar as it is today; change the navigation
only once each feature has one page. Each step ships alone and leaves the
docs better than before it.

1. Merge the twins PR 13451 doesn't touch, one per PR, with a redirect for
   the old guide: custom domains
   (`PR 13461 <https://github.com/readthedocs/readthedocs.org/pull/13461>`_),
   subprojects, redirects, offline formats, build notifications,
   organizations and teams, build troubleshooting. The merged page keeps its
   place in the current sidebar; only the guide's entry disappears.
2. After PR 13451 merges, the remaining twins: pull requests, automation
   rules, environment variables, hiding a version, SSO.
3. Delete the orphans and the ``guides/*/index`` sub-indexes, which by now
   list little that isn't elsewhere; remove the duplicate entries from the
   remaining lists.
4. Rewrite ``index.rst`` into the eight sections and rebuild the front page
   from the toctrees with ``sphinx_design`` cards. Move the Sphinx-only
   guides under the Sphinx tool page and the company copy to About. The AI
   section (`PR 13460 <https://github.com/readthedocs/readthedocs.org/pull/13460>`_)
   is a small early piece of this step.
5. ext-theme: re-sort the settings menu, fill ``project_edit_sidebar`` per
   page, point the dashboard's Help topics at final ``docs.readthedocs.com``
   URLs (today they go through one or two redirects each).
6. Write the "moving from" guides and link them from the comparison pages.

Every merged guide gets an exact redirect in the docs project.
``sphinx-build -W`` catches broken ``autosectionlabel`` references.

Open questions
--------------

- "Reader experience" or "Addons" as the section name. Addons is the product
  name; Reader experience says what it is for.
- Integrations: *Setup* (PR 13451) or *Build* (dashboard today). One answer
  for both docs and dashboard.
- Front-page cards: generated from the toctrees by a small extension, or
  hand-written once and kept in sync by review.
