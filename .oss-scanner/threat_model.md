# Threat model: Read the Docs

## What this project does and where untrusted input enters

Read the Docs is a Django application that builds documentation from users' Git repositories and hosts it.
This codebase runs two separate sites: app.readthedocs.org (Community, public projects only) and
app.readthedocs.com (Business, private projects and organizations). Business behavior is enabled with
`ALLOW_PRIVATE_REPOS=True`.
Some Business-only code lives in private repositories and is out of scope.

Untrusted input:

- Any HTTP request to the dashboard, the APIs (v2, v3, embed, search, addons), or the documentation
  server (proxito), from anonymous users and from authenticated users who should only see their own data.
- Project configuration controlled by any user: `.readthedocs.yaml`, project settings, redirects, custom
  domains, version names, branch and tag names, and the contents of their repository.
- Incoming webhooks from GitHub, GitLab, Bitbucket and generic integrations, and OAuth/SSO responses.
- Built HTML and files uploaded from builds, which are served back under the project's domain.
- Requests made with a build API key (`readthedocs/api/v2/models.py`). Each build gets a key scoped to its
  project, with write access to API v2; using one to read or change anything outside that project is in scope.

Trusted: site settings and staff/admin users.

## Components that matter most

1. **Authorization**: permissions for projects, organizations, teams and invitations, across the dashboard
   and APIs v2 and v3. Most access checks live in `readthedocs/core/permissions.py` and the apps'
   `querysets.py` files. Of interest: one user reading or changing another user's projects, versions, builds,
   organizations, teams, env vars or tokens; querysets missing a `for_user`/`api` filter; IDOR.
2. **Documentation serving**: the documentation server (`readthedocs/proxito/`), redirects and custom
   domains. URLs are mapped back to a project and version in `readthedocs/core/unresolver.py`. Of interest:
   serving a private version or another project's files, path traversal, host/domain confusion between
   projects or custom domains, cache poisoning, open redirects, auth bypass in `serve.py`, and XSS in
   responses we generate (not in the project's own files).
3. **Webhooks and integrations**: incoming webhooks from Git providers and OAuth account connections.
   Of interest: signature validation bypass, triggering builds or changing state on another project,
   OAuth account linking/takeover.
4. **Build pipeline**: cloning repositories, parsing `.readthedocs.yaml`, running builds and uploading
   their output to storage, plus the upload API. Builds run user commands inside Docker by design; of
   interest are escapes from that design: escaping the build container itself (through the mounts,
   resource limits and other Docker options we set in `readthedocs/doc_builder/environments.py`), command
   or argument injection into commands run outside the build container, leaking secrets (API tokens,
   other projects' env vars, private env vars to pull-request builds), and writing outside the project's
   storage path, from a build or through the upload API.
   Builds are moving to a new builder (github.com/readthedocs/readthedocs-builder). It works like the
   current one, but runs as its own Celery task instead of depending on the whole application, so the
   same concerns apply.
5. **Embed, search and addons APIs**: the addons API lives in `readthedocs/proxito/views/hosting.py`.
   Of interest: SSRF, leaking private projects through search or embed, XSS in returned content.
6. **Dashboard templates**: the dashboard's templates, template tags and JavaScript come from
   github.com/readthedocs/ext-theme, installed in the image at
   `/opt/venv/lib/python3.14/site-packages/readthedocsext/theme/`. Of interest: any XSS (stored,
   reflected or DOM-based), for example from user-controlled data (project names, version names, build
   output, notifications) or request parameters rendered there.

Also in scope: notifications, analytics, audit logs, account settings, SSO and Stripe
event handling.

## How to exercise it

- Tests run with pytest from `/src`, using SQLite and eager Celery. No database server is needed.
  - Main suite: `pytest --pyargs readthedocs -m "not search and not proxito and not embed_api" --nomigrations`
  - Proxito: `pytest --ds=readthedocs.settings.proxito.test --pyargs readthedocs -m "proxito and not search" --nomigrations`
  - Embed API: `pytest --pyargs readthedocs -m embed_api --nomigrations`
  - A single package: `pytest --pyargs readthedocs.api --nomigrations`
- Search tests need Elasticsearch and are not available offline.
- Four tests in the main suite fail in the image and can be ignored: the two `test_domain_creation` tests
  in `readthedocs/projects/tests/test_domain_views.py` need DNS, and two tests in
  `readthedocs/projects/tests/test_clean_build.py` expect permission errors that don't happen as root.
- Write PoCs as pytest tests using `django.test.Client` and `django_dynamic_fixture.get`; existing tests in
  `readthedocs/api/v3/tests/` and `readthedocs/proxito/tests/` show the pattern, including private projects
  (`override_settings(ALLOW_PRIVATE_REPOS=True)`) and custom domains (`HTTP_HOST`).

## How we rate severity

Reports without a working PoC are rated one level lower.

- **Critical**: code execution on our servers outside the build container (including escaping the build
  container), reading another user's private documentation or repository (the content itself), or
  account takeover.
- **High**: authenticated users reading or modifying another user's project settings, organizations,
  secrets or tokens; any XSS on the dashboard domain; XSS on documentation domains coming from our own responses,
  especially on private documentation, where it can read content the attacker shouldn't see; build
  secrets leaking outside the project.
- **Medium**: information disclosure of non-secret private data (e.g. private project names), CSRF on
  state-changing actions.
- **Low**: open redirects, issues needing `DEBUG=True`, and all denial of service.
- **Informational**:
  - SSRF, unless a working PoC shows bigger impact (e.g. reading internal services or cloud
    credentials); then rate it by that impact.
  - TOCTOU, unless a fully working PoC is attached; then rate it by its impact.
  - Timing attacks.

## Anything to leave alone

- Arbitrary code execution inside the build container: running user commands is the product.
- XSS from a project's own files: projects control their own HTML, and docs are served from separate
  domains (`*.readthedocs.io`, `*.readthedocs-hosted.com`, custom domains) for this reason. XSS on those
  domains that comes from our own responses (error pages, redirects, the addons API and its injected
  JavaScript, embed and search results) is in scope.
- Rate limiting, brute force and anything mitigated by Cloudflare or AWS configuration.
- Missing security headers, clickjacking on pages without sensitive actions, self-XSS, logout CSRF, and
  username or email enumeration, unless a PoC shows a bigger impact.
- `docs/`, `common/`, `dockerfiles/` and custom (self-hosted) installations, which we don't support.
