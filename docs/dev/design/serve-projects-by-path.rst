Serving multiple projects under one domain by path
==================================================

Some customers want to serve many projects under a single path on their own
domain, for example ``https://example.com/docs/<project>/``, where
``example.com`` is their main company domain.
They can't point that domain at us with a ``CNAME`` (it's their apex marketing
domain), so they reverse-proxy a single path prefix to us instead.

This document proposes a way to serve several projects under one domain by
path, **without** modeling them as subprojects.

Goals
-----

* Serve multiple, otherwise-unrelated projects under one domain, selected by a
  path segment (``/docs/<project>/``).
* Work when the customer can't delegate DNS to us, i.e. behind their own
  reverse proxy.
* Reuse the existing URL resolution logic instead of adding a parallel one.

Non-goals
---------

* Replacing subprojects. Subprojects still model an intentional parent/child
  relationship (shared flyout, aggregated search, ``/projects/`` prefix).
  This is for the flat case where that relationship doesn't exist.
* Arbitrary per-project URL layouts beyond a single mount prefix.
* Solving custom TLS certificates for the customer domain. The customer
  terminates TLS at their own proxy.

Background
----------

We already have most of the primitives needed:

Custom path prefix
   ``Project.custom_prefix`` serves a single project's docs under a prefix
   (``/docs/en/latest/``) instead of at the domain root.
   See :doc:`/url-path-prefixes`.

Subprojects
   ``Project.custom_subproject_prefix`` serves child projects under a prefix
   (``/projects/<alias>/``, or a custom one), all under the parent's domain.
   This is the closest existing mechanism to what we want, but it requires a
   ``ProjectRelationship`` for every project.

Header-based resolution
   The ``X-RTD-Slug`` header (gated by the ``RESOLVE_PROJECT_FROM_HEADER``
   feature) lets a reverse proxy tell us which project owns the domain,
   without relying on DNS or a custom domain record.

Proxied API paths under a prefix
   ``USE_PROXIED_APIS_WITH_PREFIX`` makes us generate the ``/_/*`` paths
   (addons, static, downloads, API) under the project's prefix, so a customer
   only needs to proxy a single path.

The missing piece is a way to resolve *many* projects under one domain by path
without a subproject relationship.

Terminology
-----------

Domain project
   The project associated with the incoming domain (via a custom domain,
   subdomain, or the ``X-RTD-Slug`` header). It "owns" the mount.
Served project
   The project selected by the leading path segment
   (``/docs/<slug>/``), served under the domain project's domain.

Proposed design
---------------

Add an opt-in feature, ``SERVE_PROJECTS_BY_PATH``, on the domain project.
When it is enabled, the unresolver matches the leading path segment to a
project **by slug**, mirroring how subprojects are matched today, but without
looking up a ``ProjectRelationship``.

URL structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

   https://example.com/<mount-prefix>/<project-slug>/<lang>/<version>/<filename>
                        └── /docs/ ──┘└── stripe ───┘└── en ─┘└ latest ┘

The mount prefix reuses ``custom_subproject_prefix`` on the domain project
(defaulting to ``/projects/``), so the same knob controls both subproject and
by-path serving.

Resolution flow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The domain project is resolved first, exactly as today (custom domain,
subdomain, or ``X-RTD-Slug``). Then, inside the path unresolver:

#. Try to match the domain project itself (versions/translations).
#. Try to match a **subproject** (``ProjectRelationship``).
#. **New:** if ``SERVE_PROJECTS_BY_PATH`` is enabled, strip the mount prefix
   and match the next segment to a project by slug. If found, resolve the
   rest of the path relative to that project.

Subprojects are checked first, so an existing subproject alias always wins
over a bare slug lookup.

Scoping and security
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Resolving a project by slug under a shared domain is the sensitive part: it
must not let one customer's domain serve an unrelated project.

The initial implementation scopes the lookup to projects that **share an
owner** with the domain project. This is a conservative default that is easy
to reason about, but it is almost certainly not the right long-term boundary
for |com_brand|, where the natural unit is the **organization**.

Options to decide on:

* Scope to the domain project's **organization** (recommended on |com_brand|).
* An explicit allowlist of served projects on the domain project (most
  restrictive, most configuration).
* Owner overlap (implemented first, simplest, weakest).

Relationship to subprojects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This intentionally reuses the subproject machinery (the same mount prefix and
the same path-matching), and slots in right after subproject matching. The
only real difference is *how the project is found*: a global (scoped) slug
lookup instead of a ``ProjectRelationship``.

That keeps the behavior predictable and means the two can coexist: a domain
can have a handful of "real" subprojects and still serve the rest of an
organization's projects by path.

Open questions
--------------

* **Scoping:** organization vs. explicit allowlist vs. owner overlap.
* **Mount prefix:** is overloading ``custom_subproject_prefix`` acceptable, or
  should this be a dedicated field on the ``Domain`` or the domain project?
* **Modeling:** should "projects served under this domain" be an explicit
  relation (so it's visible and manageable in the dashboard/admin) rather than
  an implicit slug lookup?
* **Collisions:** what happens when a served project's slug matches a
  subproject alias, a language code, or the domain project's own version
  layout? Subprojects take precedence today; the rest needs validation rules
  similar to the custom-prefix ones.

Implementation notes
--------------------

* No migration is required: ``Feature.feature_id`` is a plain ``CharField``
  without DB-level choices, so adding a feature constant is a code-only change.
* ``/_/*`` paths rely on ``USE_PROXIED_APIS_WITH_PREFIX`` plus the nginx rule
  that strips the prefix back off before Proxito routes the request.

.. seealso::

   :doc:`better-doc-urls-handling`
      The URL resolution redesign this builds on.

   :doc:`/url-path-prefixes`
      User-facing documentation for custom path prefixes.
