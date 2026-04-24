Improving redirects
===================

Redirects are a core feature of Read the Docs,
they allow users to keep old URLs working when they rename or move a page.

The current implementation lacks some features and has some undefined/undocumented behaviors.

.. contents::
   :local:
   :depth: 3

Goals
-----

- Improve the user experience when creating redirects.
- Improve the current implementation without big breaking changes.

Non-goals
---------

- Replicate every feature of other services without
  having a clear use case for them.
- Improve the performance of redirects.
  This can be discussed in an issue or pull request.
  Performance should be considered when implementing new improvements.
- Allow importing redirects.
  We should push users to use our API instead.
- Allow specifying redirects in the RTD config file.
  We have had several discussions around this,
  but we haven't reached a consensus.

Current implementation
----------------------

We have five types of redirects:

Prefix redirect:
   Allows to redirect all the URLs that start with a prefix to a new URL
   using the default version and language of the project.
   For example: a prefix redirect with the value ``/prefix/``
   will redirect ``/prefix/foo/bar`` to ``/en/latest/foo/bar``.

   They are basically the same as an exact redirect with a wildcard at the end.
   They are a shortcut for a redirect like:

   From:
     ``/prefix/$rest``
   To:
     ``/en/latest/``

   Or maybe we could use a prefix redirect to replace the exact redirect with a wildcard?

Page redirect:
   Allows to redirect a single page to a new URL using the current version and language.
   For example: a page redirect with the value ``/old/page.html``
   will redirect ``/en/latest/old/page.html`` to ``/en/latest/new/page.html``.

   Cross domain redirects are not allowed in page redirects.
   They apply to all versions,
   if you want it to apply only to a specific version you can use an exact redirect.

   A whole directory can't be redirected with a page redirect,
   an exact redirect with a wildcard at the end needs to be used instead.

   A page redirect on a single version project is the same as an exact redirect.

Exact redirect:
   Allows to redirect an exact URL to a new URL,
   it allows a wildcard at the end to redirect.
   For example: an exact redirect with the value ``/en/latest/page.html``
   will redirect ``/en/latest/page.html`` to the new URL.

   If an exact redirect with the value ``/en/latest/dir/$rest``
   is created, it will redirect all paths that start with ``/en/latest/dir/``,
   the rest of the path will be added to the new URL automatically.

   - Cross domain redirects are allowed in exact redirects.
   - They apply to all versions.
   - A wildcard is allowed at the end of the URL.
   - If a wildcard is used, the rest of the path will be added to the new URL automatically.

Sphinx HTMLDir to HTML:
   Allows to redirect clean-URLs to HTML URLs.
   Useful in case a project changed the style of their URLs.

   They apply to all projects, not just Sphinx projects.

Sphinx HTML to HTMLDir:
   Allows to redirect HTML URLs to clean-URLs.
   Useful in case a project changed the style of their URLs.

   They apply to all projects, not just Sphinx projects.

How other services implement redirects
--------------------------------------

- Gitbook implementation is very basic,
  they only allow page redirects.

  https://docs.gitbook.com/integrations/git-sync/content-configuration#redirects

- Cloudflare pages allow to capture placeholders and one wildcard (in any part of the URL).
  They also allow you to set the status code of the redirect,
  and redirects can be specific in a ``_redirects`` file.

  https://developers.cloudflare.com/pages/platform/redirects/

  They have a limit of 2100 redirects.
  In case of multiple matches, the topmost redirect will be used.

- Netlify allows to capture placeholders and a wildcard (only allowed at the end).
  They also allow you to set the status code of the redirect,
  and redirects can be specific in a ``_redirects`` file.

  - Forced redirects
  - Match query arguments
  - Match by country/language and cookies
  - Per-domain and protocol redirects
  - In case of multiple matches, the topmost redirect will be used.
  - Rewrites, serve a different file without redirecting.

  https://docs.netlify.com/routing/redirects/

- GitLab pages supports the same syntax as Netlify,
  and supports a subset of their features:

  - ``_redirects`` config file
  - Status codes
  - Rewrites
  - Wildcards (splats)
  - Placeholders

  https://docs.gitlab.com/ee/user/project/pages/redirects.html

Improvements
------------

General improvements
~~~~~~~~~~~~~~~~~~~~

The following improvements will be applied to all types of redirects.

- Allow choosing the status code of the redirect.
  We already have a field for this, but it's not exposed to users.
- Allow to explicitly define the order of redirects.
  This will be similar to the automation rules feature,
  where users can reorder the rules so the most specific ones are first.
  We currently rely on the implicit order of the redirects (updated_at).
- Allow to disable redirects.
  It's useful when testing redirects, or when debugging a problem.
  Instead of having to re-create the redirect,
  we can just disable it and re-enable it later.
- Allow to add a short description.
  It's useful to document why the redirect was created.

Don't run redirects on domains from pull request previews
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We currently run redirects on domains from pull request previews,
this is a problem when moving a whole project to a new domain.

We don't the need to run redirects on external domains, they
should be treated as temporary domains.

Normalize paths with trailing slashes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Currently, if users want to redirect a path with a trailing slash and without it,
they need to create two separate redirects (``/page/`` and ``/page``).

We can simplify this by normalizing the path before matching it, or before saving it.

For example:

From:
  ``/page/``
To:
  ``/new/page``

The from path will be normalized to ``/page``,
and the filename to match will also be normalized before matching it.
This is similar to what Netlify does:
https://docs.netlify.com/routing/redirects/redirect-options/#trailing-slash.

Page and exact redirects without a wildcard at the end will be normalized,
all other redirects need to be matched as is.

This makes it impossible to match a path with a trailing slash.

Use ``*`` and ``:splat`` for wildcards
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Currently we are using ``$rest`` at the end of the ``From URL``
to indicate that the rest of the path should be added to the target URL.

A similar feature is implemented in other services using ``*`` and ``:splat``.

Instead of using ``$rest`` in the URL for the suffix wildcard, we now will use ``*``,
and ``:splat`` as a placeholder in the target URL to be more consistent with other services.
Existing redirects can be migrated automatically.

Explicit ``:splat`` placeholder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Explicitly place the ``:splat`` placeholder in the target URL,
instead of adding it automatically.

Some times users want to redirect to a different path,
we have been adding a query parameter in the target URL to
prevent the old path from being added in the final path.
For example ``/new/path/?_=``.

Instead of adding the path automatically,
users have to add the ``:splat`` placeholder in the target URL.
For example:

From:
  ``/old/path/*``
To:
  ``/new/path/:splat``

From:
  ``/old/path/*``
To:
  ``/new/path/?page=:splat&foo=bar``

Improving page redirects
~~~~~~~~~~~~~~~~~~~~~~~~

- Allow to redirect to external domains.
  This can be useful to apply a redirect of a well known path
  in all versions to another domain.

  For example, ``/security/`` to a their security policy page in another domain.

  This new feature isn't strictly needed,
  but it will be useful to simplify the explanation of the feature
  (one less restriction to explain).

  Example:

  From:
    ``/security/``
  To:
    ``https://example.com/security/``

- Allow a wildcard at the end of the from path.
  This will allow users to migrate a whole directory to a new path
  without having to create an exact redirect for each version.

  Similar to exact redirects, users need to add the ``:splat`` placeholder explicitly.
  This means that page redirects are the same as exact redirects,
  with the only difference that they apply to all versions.

  Example:

  From:
    ``/old/path/*``
  To:
    ``/new/path/:splat``

Merge prefix redirects with exact redirects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Prefix redirects are the same as exact redirects with a wildcard at the end.
We will migrate all prefix redirects to exact redirects with a wildcard at the end.

For example:

From:
   ``/prefix/``

Will be migrated to:

From:
   ``/prefix/*``
To:
   ``/en/latest/:splat``

Where ``/en/latest`` is the default version and language of the project.
For single version projects, the redirect will be:

From:
   ``/prefix/*``
To:
   ``/:splat``

Improving Sphinx redirects
~~~~~~~~~~~~~~~~~~~~~~~~~~

These redirects are useful, but we should rename them to something more general,
since they apply to all types of projects, not just Sphinx projects.

Proposed names:

- HTML URL to clean URL redirect (``file.html`` to ``file/``)
- Clean URL to HTML URL redirect (``file/`` to ``file.html``)

Other ideas to improve redirects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following improvements will not be implemented in the first iteration.

- Run forced redirects before built-in redirects.
  We currently run built-in redirects before forced redirects,
  this is a problem when moving a whole project to a new domain.
  For example, a forced redirect like ``/$rest``,
  won't work for the root URL of the project,
  since ``/`` will first redirect to ``/en/latest/``.

  But shouldn't be a real problem, since users will still need to
  handle the ``/en/latest/file/`` paths.

- Run redirects on the edge.
  Cloudflare allow us to create redirects on the edge,
  but they have some limitations around the number of
  redirect rules that can be created.

  And they will be useful for forced exact redirects only,
  since we can't match a redirect based on the response of the origin server.

- Merge all redirects into a single type.
  This may simplify the implementation,
  but it will make it harder to explain the feature to users.
  And to replace some redirects we need to implement some new features.

- Placeholders.
  I haven't seen users requesting this feature.
  We can consider adding it in the future.
  Maybe we can expose the current language and version as placeholders.

- Per-protocol redirects.
  We should push users to always use HTTPS.

- Allow a prefix wildcard.
  We currently only allow a suffix wildcard,
  adding support for a prefix wildcard should be easy.
  But do users need this feature?

- Per-domain redirects.
  The main problem that originated this request was that we were applying redirects on external domains,
  if we stop doing that, there is no need for this feature.
  We can also try to improve how our built-in redirects work
  (specially our canonical domain redirect).

Allow matching query arguments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We can do this in three ways:

- At the DB level with some restrictions.
  If done at the DB level,
  we would need to have a different field
  with just the path, and other with the query arguments normalized and sorted.

  For example, if we have a redirect with the value ``/foo?blue=1&yellow=2&red=3``,
  if would be normalized in the DB as ``/foo`` and ``blue=1&red=3&yellow=2``.
  This implies that the URL to be matched must have the exact same query arguments,
  it can't have more or less.

  I believe the implementation described here is the same being used by Netlify,
  since they have that same restriction.

      If the URL contains other parameters in addition to or instead of id, the request doesn't match that rule.

      https://docs.netlify.com/routing/redirects/redirect-options/#query-parameters

- At the DB level using a JSONField.
  All query arguments will be saved normalized as a dictionary.
  When matching the URL, we will need to normalize the query arguments,
  and use some a combination of ``has_keys`` and ``contained_by`` to match the exact number of query arguments.

- At the Python level.
  If done at the DB level,
  we would need to have a different field
  with just the path, and other with query arguments.

  The matching of the path would be done at the DB level,
  and the matching of the query arguments would be done at the Python level.
  Here we can be more flexible, allowing any query arguments in the matched URL.

  We had some performance problems in the past,
  but I believe it was mainly due to the use of regex instead of using string operations.
  And matching the path is still done at the DB level.
  We could limit the number of redirects that can be created with query arguments,
  or the number of redirects in general.

We have had only one user requesting this feature,
so this is not a priority.

Migration
---------

Most of the proposed improvements are backwards compatible,
and just need a data migration to normalize existing redirects.

For the exception of adding the ``$rest`` placeholder in the target URL explicitly,
that needs users to re-learn how this feature works, i.e, they may be expecting
to have the path added automatically in the target URL.

We can create a small blog post explaining the changes.
