User docs architecture: folders by object, navigation by lifecycle
===================================================================

.. note::

   Proposal, October 2026. The first implementation of the folder rule is
   `PR 13451 <https://github.com/readthedocs/readthedocs.org/pull/13451>`_,
   which restructures the integration docs as ``projects/integrations/``.

Summary
-------

Each page in ``docs/user`` lives in the folder of the *object* it describes
(a project setting, the build, a documentation tool, an account) and is
listed in the sidebar under the *stage* a reader is at (get started, build,
host, ...). The two are independent: files stop moving when the navigation
changes, and the dashboard can link to docs by a formula instead of a lookup.
Every concept has one entry point. The front page shows only the sections.

Problem
-------

The user docs carry three overlapping structures, and readers meet all of them:

- Most features have two pages: an overview at the top level and a how-to twin
  under ``guides/`` (custom domains, subprojects, redirects, pull requests,
  automation rules; environment variables has three). Readers guess which one
  holds the steps.
- A "How-to guides" tree with eight sub-indexes repeats the feature sections.
  ``reproducible-builds`` is listed in three places. Two sub-indexes hold two pages.
- ``tutorials/index``, ``explanation/index`` and ``explanation/*`` are
  ``:orphan:`` leftovers of a Diátaxis layout that was started and then hidden.
- Sections follow the codebase, not the reader: Addons is one page under
  "Project setup" while its parts sit under "Reading" and "Maintaining";
  AI pages are split between "Hosting" and "Maintaining".
- Every nav change has moved files, so inbound links and ``autosectionlabel``
  references break each time.

Design
------

Four rules. A page that doesn't fit them changes; the rules don't.

**1. Folder = object.** A page lives with the thing it configures or explains:

.. code-block:: text

   docs/user/
     intro/           What Read the Docs is, add a project, tutorial, examples,
                      migrating/<source>
     tools/           One entry per documentation tool; sphinx/ holds its guides
     builds/          Build process, config file intro, customization,
                      direct upload, troubleshooting
     projects/        One folder per dashboard setting (see "Dashboard mapping")
     hosting/         How served pages behave: CDN, sitemaps, robots, 404,
                      canonical URLs, llms.txt, Markdown for agents
     accounts/        Connected services, login methods, 2FA
     organizations/   Teams, single sign-on, sharing, subscriptions, security log
     reference/       Config file schema, environment variables, api/,
                      glossary, FAQ, policies, changelog

**2. Navigation = lifecycle.** The sidebar has eight sections, each with a
landing page, and shows one level below it. A section draws from any folder:

- *Get started* ← ``intro/``
- *Documentation tools* ← ``tools/``
- *Build* ← ``builds/``, ``projects/{integrations, pull-requests,
  environment-variables, notifications, webhooks}``
- *Host* ← ``projects/{versions, domains, subprojects, translations,
  redirects}``, ``hosting/``
- *Reader experience* ← ``projects/{addons, search, analytics}``, offline formats
- *AI and agents* ← ``hosting/{llms-txt, markdown-for-agents,
  main-content-detection}``, ``reference/agent-skills``
- *Teams and organizations* ← ``accounts/``, ``organizations/``,
  ``projects/{maintainers, sharing}``
- *Reference and help* ← ``reference/``

There is no "How-to guides" section and no section per content type.

**3. One entry point per concept.** A concept is a single ``index.rst`` that
answers, in order: what it does, how to turn it on, what the settings mean.
It grows into a sub-tree only when it has real variants or a known failure list:

.. code-block:: text

   projects/domains/
     index.rst              the whole concept; enough for most settings
   projects/integrations/
     index.rst              landing: what, configuration methods, types
     github-app.rst         one page per variant
     webhook.rst
     guides/<task>.rst      how-tos too long for the landing
     troubleshooting.rst    only when there is a failure list

Under ``projects/`` every concept is a folder with ``index.rst``, even when it
is one page, so its URL doesn't change when a guide is added later.
Tool-specific content (Intersphinx, Jupyter, custom CSS, PDF Unicode, rST to
MyST) lives only under ``tools/sphinx/``.

**4. Front page = sitemap.** ``index.rst`` is one sentence, three ways in
(*Add your project*, *Choose your tool*, *Follow the tutorial*), eight section
cards generated from the same toctrees the sidebar uses, and a help strip.
Nothing exists only on the front page. Company copy moves to About.

Dashboard mapping
-----------------

``projects/<name>/`` matches the dashboard URL name ``projects_<name>``, so the
``project_edit_sidebar`` block in ext-theme (empty on every page today) can
link each settings page to its docs with one rule:

==================================  ============================
Dashboard                           Docs
==================================  ============================
``projects_integrations``           ``projects/integrations/``
``projects_domains``                ``projects/domains/``
``projects_redirects``              ``projects/redirects/``
``projects_subprojects``            ``projects/subprojects/``
``projects_translations``           ``projects/translations/``
``projects_pull_requests``          ``projects/pull-requests/``
``projects_notifications``          ``projects/notifications/``
``projects_webhooks``               ``projects/webhooks/``
``projects_addons``                 ``projects/addons/``
``projects_search_settings``        ``projects/search/``
``projects_*_analytics``            ``projects/analytics/``
``projects_users``                  ``projects/maintainers/``
``projects_temporary_access_list``  ``projects/sharing/``
==================================  ============================

The settings menu itself re-sorts into *Setup, Build, Host, Readers*, a subset
of the docs sections, and the page titles use the dashboard's labels
("Pull request builds", "Domains"). "Maintaining" goes away.

Prior art
---------

Read in October 2026. The pattern is common; these are the clearest cases.

- `Diátaxis: workflow <https://diataxis.fr/how-to-use-diataxis/#don-t-worry-about-structure>`_.
  Diátaxis's own guidance is not to divide the docs into four top-level
  sections ("Don't do that. It's horrible.") and to treat the four types as
  "a guide, not a plan" that changes structure "from the inside". Our
  orphaned ``tutorials/`` and ``explanation/`` indexes are the top-level
  version it warns against. Rule 3 is the inside version.
- `GitHub Actions docs <https://docs.github.com/en/actions>`_ is the
  counter-example in practice: Concepts / How-tos / Reference / Tutorials at
  the top produce a 150-item index that only works because of a curated
  "Recommended" block of nine.
- `Render <https://render.com/docs>`_: front page by verb (Create, Configure,
  Operate), sidebar by product area, settings tabs mirrored under Configure.
  The closest match to rules 1 and 2 together.
- `Netlify <https://docs.netlify.com/>`_: sidebar by lifecycle (Start, Build,
  Deploy, Manage, Extend, Reference) with a settings-shaped *Manage* group
  (Accounts & Billing, Projects, Domains, Security & access) inside it.
- `Plausible <https://plausible.io/docs>`_: the docs sidebar *is* the app's
  settings menu (Website settings, Stats dashboard, Goals, Account, Team,
  Billing). Works because the product is small; it shows the dashboard
  mapping taken to its limit.
- `Stripe <https://docs.stripe.com/>`_: "Start here" by use case, then browse
  by product, with product sections matching the Dashboard's sections.
- `Sentry product docs <https://docs.sentry.io/product/>`_: grouped by verb
  (Detect, Debug, Measure, Automate), deliberately not by the app sidebar.
  Evidence that nav by stage and folders by object can diverge without harm.
- `GitLab Pajamas: contextual help <https://design.gitlab.com/patterns/contextual-help/>`_:
  rules for UI-to-docs links (link only when the help won't fit, open in a new
  tab, phrase as a question, "Learn more" sparingly). The standard for the
  ext-theme help links.
- `Comparison pages on about.readthedocs.com <https://about.readthedocs.com/comparisons/>`_:
  seven "why" pages that end with generic setup steps. The docs own the
  "how" (``intro/migrating/<source>``) and the two link to each other.

Rollout
-------

Each step ships alone and leaves the docs better than before it.

1. Delete the orphans nothing links to: ``tutorials/index``,
   ``explanation/{index,advanced,methodology}``.
2. Merge the twins PR 13451 doesn't touch, one per PR, with a redirect for the
   old guide: domains (`PR 13461 <https://github.com/readthedocs/readthedocs.org/pull/13461>`_),
   subprojects, redirects, offline formats. Pages move into ``projects/<name>/``
   only when their content is being rewritten anyway.
3. Remove the duplicate entries from the ``guides/*/index`` sub-indexes.
4. Regroup the AI (`PR 13460 <https://github.com/readthedocs/readthedocs.org/pull/13460>`_)
   and Addons toctrees in ``index.rst``; full re-home into eight sections after
   PR 13451 merges.
5. Rebuild the front page from the toctrees with ``sphinx_design`` cards.
6. Merge the remaining twins and move tool-specific guides under ``tools/sphinx/``.
7. ext-theme: re-sort the settings menu, fill ``project_edit_sidebar`` per page,
   point the dashboard's Help topics at final ``docs.readthedocs.com`` URLs.
8. Write ``intro/migrating/<source>`` and link from the comparison pages.

Every move gets an exact redirect in the docs project. ``sphinx -W`` catches
broken ``autosectionlabel`` references.

Open questions
--------------

- "Reader experience" or "Addons" as the section name. Addons is the product
  name; Reader experience says what it is for.
- Integrations: *Setup* (PR 13451, dashboard proposal) or *Build* (dashboard
  today). One answer for both.
- Front-page cards: generated from the toctrees by a small extension, or
  hand-written once and kept in sync by review.
