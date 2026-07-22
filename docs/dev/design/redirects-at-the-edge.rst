Moving heavy redirects to the edge
==================================

Redirects are one of the most requested paths on our documentation domains,
and also one of the most expensive to serve from the origin.
A recent attack targeted our documentation domains with high volumes of
requests that resolved to redirects,
which bypassed our CDN cache and put load on the origin and the database.

This document proposes moving the *heavy* redirects out of the Python
origin (Proxito) and onto the Cloudflare edge,
so that the platform stays available and scalable under this kind of load.

.. contents::
   :local:
   :depth: 2

Goals
-----

- Serve the redirects that are cheap to evaluate but expensive to host
  entirely from the Cloudflare edge, without hitting the origin or the database.
- Make redirect serving resilient to cache-busting attacks
  (many unique URLs against our documentation domains).
- Keep the source of truth for redirect data in our database,
  and keep the user-facing experience (dashboard, API) unchanged.
- Fail open: if the edge can't make a decision, fall back to the origin,
  never serve a wrong redirect or a hard error.

Non-goals
---------

- Move *all* redirect logic to the edge.
  Some redirects depend on origin-only state (does this file exist?
  is this version private?) and must stay at the origin.
- Replace the redirects feature, models, or dashboard UX.
  This is an infrastructure change, not a product change.
- Change how users author redirects.
  The :doc:`redirects` design (status codes, ``*``/``:splat`` wildcards,
  ordering, disabling) is orthogonal and complementary to this work.

Background: why redirects are expensive at the origin
-----------------------------------------------------

Today every redirect decision is made in Python inside Proxito.
A redirect costs us a full request to the origin, and most of them also
cost one or more database queries:

- **Domain resolution.** Custom domains require a DB lookup
  (``Domain.objects.filter(domain=...)``) to map host to project.
- **Path resolution.** Resolving ``/en/latest/foo`` to a project, version,
  and filename queries translations and versions.
- **User redirect matching.** ``get_matching_redirect_with_path()`` runs a
  query against the project's redirects on every 404 and every forced redirect.
- **404 handling.** A request to a path that doesn't exist is internally
  re-routed to ``ServeError404``, which re-resolves the path, queries for a
  matching redirect, and then queries storage for a custom ``404.html``.

The important property for an attacker is that **unique URLs are cache misses**.
A flood of distinct paths against a documentation domain bypasses the CDN
cache entirely and lands on the origin, where each request can cost
several DB queries before we even decide to issue a 301/302.
The redirects that are structurally simple (HTTP→HTTPS, root→default version,
canonical domain) are exactly the ones we should never need the origin for.

Taxonomy: what can move to the edge
------------------------------------

Not all redirects are equal. We can split them into three tiers by the data
they need to make a decision.

.. list-table::
   :header-rows: 1
   :widths: 22 38 20 20

   * - Redirect
     - What it needs to decide
     - Origin state?
     - Edge tier
   * - HTTP → HTTPS
     - The request scheme only
     - No
     - Tier 0 (native)
   * - Trailing slash / double slash normalization
     - The path only
     - No
     - Tier 0 (native)
   * - Root → default version (``/`` → ``/en/latest/``)
     - Project default version + language + versioning scheme
     - No (metadata)
     - Tier 1 (Worker + KV)
   * - Canonical domain (public domain → custom domain)
     - Project's canonical domain
     - No (metadata)
     - Tier 1 (Worker + KV)
   * - Subproject domain → parent domain
     - Project's parent + prefix
     - No (metadata)
     - Tier 1 (Worker + KV)
   * - Forced user redirects (exact / page / clean-url ↔ html)
     - The project's redirect rules
     - No (metadata)
     - Tier 2 (Worker + KV)
   * - Non-forced user redirects (only fire on 404)
     - Whether the target file exists
     - **Yes**
     - Stays at origin
   * - Custom ``404.html`` serving, private version auth
     - Storage + privacy state
     - **Yes**
     - Stays at origin

The key insight: **everything except non-forced redirects and authenticated
file serving can be decided from project metadata alone.**
That metadata is small, changes infrequently, and can be replicated to the edge.

Proposed architecture
---------------------

A Cloudflare Worker sits in front of the origin on our documentation domains.
On each request it does a single key/value lookup and decides whether it can
answer with a redirect itself, or whether it should pass the request through
to the origin unchanged.

.. code-block:: text

   request ──> Cloudflare Worker
                 │
                 ├─ Tier 0: scheme/path normalization ──> 301/302 at edge
                 │
                 ├─ KV lookup: host -> project config
                 │     ├─ Tier 1: structural redirect ──> 301/302 at edge
                 │     └─ Tier 2: forced user redirect ──> 301/302 at edge
                 │
                 └─ no match / KV miss / private ──> origin (Proxito, unchanged)

Edge data store
~~~~~~~~~~~~~~~

We replicate a compact, read-optimized view of the data the edge needs into
**Cloudflare Workers KV** (eventually-consistent, globally replicated,
read-optimized — a good fit for "read on every request, write rarely").

Two logical namespaces, both keyed for O(1) lookup:

``domain:{host}`` → project routing config
   .. code-block:: json

      {
        "project": "pip",
        "canonical_domain": "pip.example.com",
        "https": true,
        "parent": null,
        "subproject_prefix": null,
        "default_version": "stable",
        "default_language": "en",
        "versioning_scheme": "multiple_versions_with_translations",
        "custom_prefix": null,
        "has_redirects": true
      }

``redirects:{project}`` → ordered list of *edge-eligible* redirect rules
   .. code-block:: json

      [
        {"type": "exact", "from": "/old/*", "to": "/new/:splat",
         "status": 301, "force": true},
        {"type": "clean_url_to_html", "status": 301, "force": true}
      ]

Only **forced** user redirects, plus the always-evaluatable
clean-url ↔ html types, are pushed to ``redirects:{project}``.
Non-forced redirects are intentionally left out, because they depend on
whether the origin can serve the file, which the edge cannot know.

Sizing: with on the order of 10⁵ projects and ~10⁶ redirect rules, the full
data set is a few hundred MB — comfortably within KV, and most projects have
no redirects at all (``has_redirects: false`` lets the Worker skip the second
lookup entirely).

Why this is not blocked by Cloudflare's rule limits
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A previous note in :doc:`redirects` dismissed edge redirects because
Cloudflare's native *Redirect Rules* have a per-zone limit
(low thousands of rules) that we'd blow past instantly.

This proposal sidesteps that entirely: redirect data lives in **KV**, and the
matching logic lives in **Worker code**. There is no per-rule platform limit —
we're limited by KV storage (gigabytes) and per-request CPU time, not by a
fixed rule count. Native Redirect Rules are still the right tool for the
Tier 0 global redirects (HTTP→HTTPS), which need no per-project data.

Matching at the edge
~~~~~~~~~~~~~~~~~~~~~

The Worker reproduces the origin's matching semantics for the edge-eligible
subset:

1. **Normalize** the path (collapse double slashes, handle trailing slash) —
   Tier 0, no data needed.
2. **Look up** ``domain:{host}``. On a miss, pass through to origin.
3. **Structural redirects** (Tier 1): if the host is non-canonical and a
   canonical domain exists, or the project is a subproject, or the path is the
   root and a default version is configured, build the target URL and redirect.
4. **Forced user redirects** (Tier 2): if ``has_redirects`` is true, fetch
   ``redirects:{project}`` and evaluate rules in order, applying ``:splat``
   wildcard substitution. First match wins, mirroring origin ordering.
5. **Otherwise**, pass through to the origin untouched.

To keep parity provable, the matching algorithm should be extracted into a
small, well-tested module that we can validate against the existing
``redirects`` test suite — ideally sharing fixtures so the edge and origin
can't silently diverge.

Reference implementation
~~~~~~~~~~~~~~~~~~~~~~~~~

A first cut lives in the ``redirects`` app:

- ``readthedocs/redirects/edge.py`` — serializes a project's routing config
  and edge-eligible redirects, a reference matcher (``match_redirect``) for
  parity testing, the ``X-RTD-Edge-Redirects`` header builder, and the
  ``EdgeStore`` abstraction (in-memory ``LocalEdgeStore`` plus the Cloudflare
  KV backend in ``edge_cloudflare.py``).
- ``readthedocs/proxito/middleware.py`` — emits the ``X-RTD-Edge-Redirects``
  header (Option A), behind ``RTD_EDGE_REDIRECTS_ENABLED``.
- ``readthedocs/redirects/edge_worker.js`` — the reference Worker, supporting
  both header learning (Option A) and pre-warmed KV (Option B).

The first cut deliberately serves only **forced exact redirects**: they match
on the whole request path, so the edge needs no version list or language
parsing. Page and clean-URL redirects need the edge to split the language and
version out of the path first, which requires more project metadata; they are
a follow-up, and until then they remain at the origin.

Getting the data to the edge
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are two ways to get the routing data from the origin to the edge.
They are complementary, and we can ship the first on its own.

**Option A — header delivery (no config).**
The origin already talks to our Cloudflare Workers through response headers
(for example ``X-RTD-Force-Addons``). We reuse that channel: the origin emits
the project's forced redirects on an ``X-RTD-Edge-Redirects`` response header,
and the Worker caches them per host (in the Cloudflare Cache API) for a short
TTL. The next requests for that host are answered at the edge.

This needs **no Cloudflare API credentials, no KV namespace, and no sync
pipeline** — the data simply rides on responses the origin is already sending,
and the edge learns it lazily. To keep this from adding a database query to
every response, the origin caches the serialized header value per project for
a short TTL, so the cost is roughly one query per project per TTL.

Under the attack we saw, the first request to a host warms the edge with that
project's forced redirects; every subsequent (unique, cache-busting) URL under
those rules is then served at the edge without touching the origin.

**Option B — pre-warmed KV (for the first request too).**
Header delivery only protects the origin *after* the edge has seen one
response for a host. To also absorb the very first request, we can push the
same data into Workers KV ahead of time via the Cloudflare API. The Worker
checks its learned cache first, then falls back to KV, then to the origin.

The trade-off: Option B removes the cold-start window but adds the operational
cost Option A avoids (credentials, a sync pipeline, and an eventually-consistent
replica to reason about). We start with Option A and add B only if the
cold-start window proves to matter under load.

Keeping the pre-warmed KV in sync
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If we adopt Option B, the database stays the source of truth and we propagate
changes to KV asynchronously so the dashboard and API are unaffected:

- On ``Project``, ``Domain``, ``Version``, and ``Redirect`` save/delete,
  enqueue a Celery task that rebuilds the affected ``domain:{host}`` and/or
  ``redirects:{project}`` entries and writes them to KV via the Cloudflare API.
- A periodic reconciliation task does a full re-sync to repair any drift from
  missed signals (belt and suspenders).
- KV is eventually consistent (propagation on the order of seconds to a minute).
  This is acceptable for redirects, and it matches the existing CDN cache
  behavior, where redirect responses are already cached and purged by tag.

This reuses the same mental model we already have for CDN cache purging by
``Cache-Tag``; we're adding a second, more granular replica of the routing data.

Why this defends against the attack
------------------------------------

Under the attack we saw, a flood of unique URLs against our documentation
domains bypassed the CDN cache and hit the origin. With this design:

- Tier 0/1 redirects (HTTPS, root, canonical, subproject) are answered by the
  Worker from a single KV read. The origin and database see **zero** of this
  traffic, regardless of how many unique URLs are requested.
- Forced user redirects are answered the same way.
- Cloudflare's edge absorbs the volume on infrastructure built to scale
  horizontally for exactly this, and the per-IP/zone protections
  (rate limiting, WAF) apply before our Worker runs.

The only traffic that still reaches the origin is the traffic that genuinely
needs origin state: real file serving, non-forced 404-driven redirects, and
authenticated private docs. Those can be protected with rate limiting
independently, and they're a small fraction of an attack made of random URLs.

Failure modes and safety
------------------------

- **KV miss or stale data.** The Worker passes the request through to the
  origin, which still has the full, authoritative redirect logic.
  Worst case we lose the edge optimization for a few seconds after a change;
  we never serve a wrong answer.
- **Worker error / timeout.** Fail open to origin. A bug in edge matching must
  never take down doc serving.
- **Edge/origin divergence.** Mitigated by sharing the matching algorithm and
  test fixtures, and by emitting the same ``X-RTD-Redirect`` header from the
  edge so we can attribute redirects in analytics.
- **Privacy.** Only public, non-authenticated routing metadata is replicated to
  KV. Private-version decisions and any auth stay at the origin; the edge never
  makes an access-control decision.

Observability
-------------

- Have the Worker set ``X-RTD-Redirect`` (and a marker like
  ``X-RTD-Redirect-Source: edge``) so existing dashboards distinguish
  edge-served from origin-served redirects.
- Track edge hit ratio, KV read latency, and pass-through rate.
- Alert on a rising origin redirect rate, which would indicate the edge is not
  catching what it should (sync lag, missing data, or a logic gap).

Rollout plan
------------

#. **Tier 0 first.** Move HTTP→HTTPS and path normalization to native
   Cloudflare rules / a thin Worker. No data sync required; immediate relief.
#. **Build the sync pipeline.** Replicate ``domain:{host}`` config to KV and
   verify it matches the origin's resolver for a sample of projects (shadow
   mode: compute the edge decision, log it, but still serve from origin).
#. **Enable Tier 1 structural redirects** behind the shadow comparison until
   the divergence rate is effectively zero.
#. **Add Tier 2 forced user redirects**, syncing ``redirects:{project}`` and
   again validating in shadow mode before serving from the edge.
#. **Keep the origin as the permanent fallback.** Non-forced redirects, custom
   404s, and private docs are explicitly out of scope and stay at the origin.

Open questions
--------------

- **KV vs. D1 vs. Durable Objects** for the redirect rules.
  KV is simplest and matches the read pattern; D1 (SQLite at the edge) may be
  worth it if we want richer matching (query-argument matching from
  :doc:`redirects`) without shipping all rules per project.
- **Per-project rule volume.** A handful of projects have thousands of
  redirects. We should cap the per-project payload pushed to KV and fall back
  to origin matching above the cap, rather than ship multi-MB values.
- **Single shared matching implementation.** Can we compile/port the Python
  matcher to the Worker runtime (or express the rules declaratively enough that
  both sides interpret them identically) to guarantee parity?
- **Non-forced redirects on 404.** Out of scope here, but a future option is to
  let the Worker catch a ``404`` from the origin and apply a redirect at the
  edge, keeping the DB query off the origin while preserving "only redirect if
  the file is missing" semantics.
