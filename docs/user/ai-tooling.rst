AI tooling for documentation projects
====================================

.. meta::
   :description lang=en:
      A practical guide to making your documentation more discoverable,
      citeable, and maintainable for AI assistants using Read the Docs features.

This guide explains how to make documentation easier for AI assistants to
consume and cite.

Similar to SEO guidance, the goal isn't to optimize for bots at the expense of
readers. The goal is to make your docs more discoverable and understandable for
people, while also making them easier for AI tools to process correctly.

AI tooling basics
-----------------

Most AI assistants combine retrieval with language generation. In practice, this
means they need to:

* find your pages,
* identify authoritative versions,
* understand which content is primary,
* and cite stable URLs.

When those signals are missing, answers are more likely to be stale,
hallucinated, or poorly sourced.

Best practices for AI-ready documentation
-----------------------------------------

Use ``llms.txt`` as a discovery signal ✅
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:doc:`/reference/llms-txt`
  Publish ``llms.txt`` (and optionally ``llms-full.txt``) so tools can quickly
  discover a model-friendly entry point for your docs.

Keep version context explicit ✅
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:doc:`/versions`
  Keep multiple versions available so assistants can cite version-correct docs.

:doc:`/changelog`
  Publish changes over time to help tools and readers confirm freshness.

Preserve stable URLs ✅
~~~~~~~~~~~~~~~~~~~~~~

:doc:`/user-defined-redirects`
  Add redirects when pages move so historical links and citations keep working.

:doc:`/canonical-urls`
  Define canonical URLs to reduce ambiguity when similar content exists at
  multiple addresses.

Expose discoverable structure ✅
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:doc:`/reference/sitemaps`
  Use generated sitemaps so automated systems can discover your full URL graph.

:doc:`/guides/best-practice/links`
  Keep navigation and internal links strong to avoid orphaned content.

Control agent access intentionally ✅
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:doc:`/reference/robots`
  Use ``robots.txt`` policies to guide crawler access.

:doc:`/commercial/privacy-level`
  Use privacy levels to keep internal or restricted docs out of public
  retrieval.

Improve content extraction quality ✅
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:doc:`/reference/main-content-detection`
  Understand how primary content is identified for extraction and indexing.

:doc:`/guides/best-practice/links`
  Prefer clear headings, descriptive links, and focused page topics so
  retrieval systems can ground answers accurately.

Automate AI-related workflows ✅
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:doc:`/reference/agent-skills`
  Use Read the Docs agent skills to standardize common AI-agent tasks.

:doc:`/api/index`
  Connect assistants and internal tooling to your documentation workflows.

Common pitfalls
---------------

* Publishing docs without clear version context.
* Moving content without redirects.
* Letting key updates live only in chat or issue threads.
* Using weak page structure that makes retrieval ambiguous.

.. seealso::

   :doc:`/guides/technical-docs-seo-guide`
   :doc:`/guides/best-practice/index`
   :doc:`/faq`
