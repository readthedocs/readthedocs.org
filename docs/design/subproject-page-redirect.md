# Spike: /page/ redirects for subprojects

## Background and problem

Users expect `/page/` URLs on subprojects to redirect to the default version, the same way they do for top-level projects. Today those requests return 404 because the redirect view only looks up subprojects by alias on the parent project. When the current request context already belongs to the subproject (for example, after middleware resolves the host to the child project) or when the stored alias differs from the slug, that lookup fails and the redirect short-circuits.

## Findings

* The proxito URL configuration already routes `/projects/<slug>/page/<path>` to `ServePageRedirect`, so the failure happens in the view rather than URL parsing.
* `ServePageRedirect` fetched subprojects exclusively via `project.subprojects.filter(alias=...)`, which raises `Http404` when the request context is already scoped to the subproject or when an alias mismatch occurs.
* The redirect logic ultimately just needs the correct `Project` instance to resolve the default version and build the target URL; it should tolerate being invoked from either the parent or child context.

## Proposed approach

* Expand subproject resolution in `ServePageRedirect` to handle three cases:
  * If the current project already matches the requested slug, treat it as the target subproject.
  * Otherwise, try to find a `ProjectRelationship` by alias and fall back to matching the child slug.
  * Raise `Http404` only when no relationship matches, preserving existing behavior for invalid slugs.
* Keep the rest of the redirect flow unchanged so the spike stays low risk while we validate that subproject `/page/` redirects behave like top-level projects.

## Validation plan

* Add a focused proxito test that requests `/projects/<subproject>/page/<file>` on the public domain and asserts a 302 to the subproject's default version.
* Run the proxito redirect tests locally to confirm the new lookup path fixes the 404 without affecting existing redirects.
  Use the proxito test settings so the proxito URLConf and middleware are active:

  ```
  DJANGO_SETTINGS_MODULE=readthedocs.settings.proxito.test \
  uv run pytest readthedocs/proxito/tests/test_old_redirects.py::InternalRedirectTests::test_page_redirect_on_subproject -vv -s
  ```
