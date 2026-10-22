# Threat model: Read the Docs

## What this project does and where untrusted input enters
Read the Docs is a Django application that builds documentation from users' Git repositories and hosts it.
It runs as a multi-tenant service: app.readthedocs.org (Community, public projects only) and
app.readthedocs.com (Business, private projects and organizations, `ALLOW_PRIVATE_REPOS = True`).
Both run this codebase; some Business-only code lives in private repositories and is out of scope.

Untrusted input:
- Any HTTP request to the dashboard, the APIs (v2, v3, embed, search, addons), or the documentation
  server (proxito), from anonymous users and from authenticated users who should only see their own data.
- Project configuration controlled by any user: `.readthedocs.yaml`, project settings, redirects, custom
  domains, version names, branch and tag names, and the contents of their repository.
- Incoming webhooks from GitHub, GitLab, Bitbucket and generic integrations, and OAuth/SSO responses.
- Built HTML and files uploaded from builds, which are served back under the project's domain.

Trusted: site settings, staff/admin users, and the build servers' own API token.

## Components that matter most
1. **Authorization and multi-tenancy**: `readthedocs/core/permissions.py`, `readthedocs/*/querysets.py`,
   `readthedocs/organizations/`, `readthedocs/invitations/`, `readthedocs/api/v3/permissions.py`,
   `readthedocs/api/v2/`. Of interest: one user reading or changing another user's projects, versions,
   builds, organizations, teams, env vars or tokens; querysets missing a `for_user`/`api` filter; IDOR.
2. **Documentation serving (proxito)**: `readthedocs/proxito/`, `readthedocs/core/resolver.py`,
   `readthedocs/core/unresolver.py`, `readthedocs/redirects/`, `readthedocs/domains/`. Of interest:
   serving a private version or another project's files, path traversal, host/domain confusion between
   projects or custom domains, cache poisoning, open redirects, auth bypass in `serve.py`.
3. **Webhooks and integrations**: `readthedocs/api/v2/views/integrations.py`, `readthedocs/integrations/`,
   `readthedocs/oauth/`. Of interest: signature validation bypass, triggering builds or changing state on
   another project, OAuth account linking/takeover.
4. **Build pipeline**: `readthedocs/doc_builder/`, `readthedocs/projects/tasks/`, `readthedocs/vcs_support/`,
   `readthedocs/config/`. Builds run user commands inside Docker by design; of interest are escapes from
   that design: command or argument injection into commands run outside the build container, leaking
   secrets (API tokens, other projects' env vars, private env vars to pull-request builds), and writing
   outside the project's storage path when uploading output.
5. **Embed, search and addons APIs**: `readthedocs/embed/`, `readthedocs/search/`, `readthedocs/proxito/views/hosting.py`.
   Of interest: SSRF, leaking private projects through search or embed, XSS in returned content.

Also in scope, less important: notifications, analytics, audit logs, account settings.

## How to exercise it
- Tests run with pytest from `/src`, using SQLite and eager Celery. No database server is needed.
  - Main suite: `pytest --pyargs readthedocs -m "not search and not proxito and not embed_api" --nomigrations`
  - Proxito: `pytest --ds=readthedocs.settings.proxito.test --pyargs readthedocs -m "proxito and not search" --nomigrations`
  - A single package: `pytest --pyargs readthedocs.api --nomigrations`
- Search tests need Elasticsearch and are not available offline.
- Write PoCs as pytest tests using `django.test.Client` and `django_dynamic_fixture.get`; existing tests in
  `readthedocs/api/v3/tests/` and `readthedocs/proxito/tests/` show the pattern, including private projects
  (`override_settings(ALLOW_PRIVATE_REPOS=True)`) and custom domains (`HTTP_HOST`).

## How we rate severity
- **Critical**: unauthenticated or cross-tenant code execution on our servers, access to another user's
  private documentation or repository, or account takeover, with a working PoC.
- **High**: authenticated users reading or modifying another user's projects, organizations, secrets or
  tokens; stored XSS on the dashboard domain; build secrets leaking outside the project.
- **Medium**: information disclosure of non-secret private data (e.g. private project names), CSRF on
  state-changing actions, SSRF without a clear path to internal data.
- **Low**: open redirects, issues needing `DEBUG=True`, and all denial of service.

## Anything to leave alone
- Arbitrary code execution inside the build container: running user commands is the product.
- XSS inside hosted documentation: projects control their own HTML, and docs are served from separate
  domains (`*.readthedocs.io`, `*.readthedocs-hosted.com`, custom domains) for this reason.
- Rate limiting, brute force and anything mitigated by Cloudflare or AWS configuration.
- Vulnerabilities in Django, Sphinx, MkDocs or other dependencies themselves, unless Read the Docs uses
  them in an unsafe way.
- `docs/`, `common/`, `dockerfiles/` and custom (self-hosted) installations, which we don't support.
