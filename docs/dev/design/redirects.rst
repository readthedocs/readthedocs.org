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

   - From: ``/prefix/$rest``
     To: ``/en/latest/``

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

  https://docs.netlify.com/routing/redirects/

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

Allow matching query arguments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We can do this in two ways:

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

Don't run redirects on domains from pull request previews
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We currently run redirects on domains from pull request previews,
this is a problem when moving a whole project to a new domain.

Do we have the need to run redirects on external domains?
They are suppose to be temporary domains.

Normalize paths with trailing slashes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Currently, if users want to redirect a path with a trailing slash and without it,
they need to create two separate redirects (``/page/`` and ``/page``).

We can simplify this by normalizing the path before matching it.

For example:

- From: ``/page/``
  To: ``/new/page``

The from path will be normalized to ``/page``,
and the filename to match will also be normalized before matching it.
This is similar to what Netlify does:
https://docs.netlify.com/routing/redirects/redirect-options/#trailing-slash.

Page and exact redirects without a wildcard at the end will be normalized,
all other redirects need to be matched as is.

Improving exact redirects
~~~~~~~~~~~~~~~~~~~~~~~~~

- Explicitly place the ``$rest`` placeholder in the target URL,
  instead of adding it automatically.

  Some times users want to redirect to a different path,
  we have been adding a query parameter in the target URL to
  prevent the old path from being added in the final path.
  For example ``/new/path/?_=``.

  Instead of adding the path automatically,
  users have to add the ``$rest`` placeholder in the target URL.
  For example:

  - From: ``/old/path/$rest``
    To: ``/new/path/$rest``

  - From: ``/old/path/$rest``
    To: ``/new/path/?page=$rest&foo=bar``

- Per-domain redirects.
  Do users have the need for this?
  The main problem is that we were applying the redirect
  to external domains, if we stop doing that, is there the need for this?
  We can also try to improve how our built-in redirects work
  (specially our canonical domain redirect).

Improving page redirects
~~~~~~~~~~~~~~~~~~~~~~~~

- Allow to redirect to external domains.
  This can be useful to apply a redirect of a well known path
  in all versions to another domain.

  For example, ``/security/`` to a their security policy page in another domain.

  This new feature isn't strictly needed,
  but it will be useful to simplify the explanation of the feature
  (one less restriction to explain).

- Allow a wildcard at the end of the from path.
  This will allow users to migrate a whole directory to a new path
  without having to create an exact redirect for each version.

  Similar to exact redirects, users need to add the ``$rest`` placeholder explicitly.
  This means that that page redirects are the same as exact redirects,
  with the only difference that they apply to all versions.

Improving Sphinx redirects
~~~~~~~~~~~~~~~~~~~~~~~~~~

These redirects are useful, but we should rename them to something more general,
since they apply to all types of projects, not just Sphinx projects.

Proposed names:

- HTML URL to clean URL redirect (``file.html`` to ``file/``)
- Clean URL to HTML URL redirect (``file/`` to ``file.html``)

Other ideas to improve redirects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

- Merge prefix redirects with exact redirects.
  Prefix redirects are the same as exact redirects with a wildcard at the end.

- Placeholders.
  I haven't seen users requesting this feature.
  We can consider adding it in the future.
  Maybe we can expose the current language and version as placeholders.

- Replace ``$rest`` with ``*`` in the from_url.
  This will be more consistent with other services,
  but it will require users to re-learn the feature.

- Per-protocol redirects.
  We should push users to always use HTTPS.

- Allow a prefix wildcard.
  We currently only allow a suffix wildcard,
  adding support for a prefix wildcard should be easy.
  But do users need this feature?

Migration
---------

Most of the proposed improvements are backwards compatible,
and just need a data migration to normalize existing redirects.

For the exception of adding the ``$rest`` placeholder in the target URL explicitly,
that needs users to re-learn how this feature works, i.e, they may be expecting
to have the path added automatically in the target URL.

We can create a small blog post explaining the changes.
