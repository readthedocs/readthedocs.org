Markdown for AI agents
======================

Read the Docs serves a Markdown version of documentation pages to AI agents that request it,
using HTTP content negotiation.
This makes documentation more efficient for language models to consume,
since Markdown is smaller and easier to parse than rendered HTML.

This feature is **enabled automatically** on all documentation domains hosted on Read the Docs,
with no configuration required.

How it works
------------

When a client makes a request with an ``Accept`` header that prefers Markdown,
Read the Docs returns a Markdown representation of the page instead of the HTML version.
The Markdown is generated on the fly from the built HTML output of your documentation.

For example, a request with ``Accept: text/markdown`` will return a Markdown response:

.. code-block:: bash

   $ curl -i https://docs.readthedocs.com/platform/stable/intro/sphinx.html -H "Accept: text/markdown"
   HTTP/2 200
   content-type: text/markdown; charset=utf-8
   vary: accept
   x-markdown-tokens: 1657
   content-signal: ai-train=yes, search=yes, ai-input=yes

   ---
   description: Hosting Sphinx documentation on Read the Docs.
   title: Deploying Sphinx on Read the Docs
   ---

   ...

The original HTML page is still served for normal browser requests.
Only clients that explicitly request Markdown via the ``Accept`` header will receive the Markdown version.

Benefits
--------

* **Smaller payloads**: Markdown is more compact than HTML, which reduces bandwidth and context usage for AI agents.
* **Better readability for language models**: Markdown is easier for language models to parse than HTML with styling and navigation markup.
* **No configuration required**: The feature works automatically on all documentation hosted on Read the Docs.
* **Transparent for readers**: Browsers continue to receive the regular HTML version of your documentation.

Implementation
--------------

This feature is implemented by `Cloudflare`_, which generates the Markdown representation from the HTML response.
See the `Cloudflare blog post on Markdown for agents`_ for more details about how the conversion works.

.. seealso::

   :doc:`/reference/llms-txt`
     Serve a custom ``llms.txt`` file to guide AI agents to the most relevant pages of your documentation.

   :doc:`/reference/agent-skills`
     Use Read the Docs Agent Skills to help AI agents work with Read the Docs APIs and configuration.

.. _Cloudflare: https://www.cloudflare.com/
.. _Cloudflare blog post on Markdown for agents: https://blog.cloudflare.com/markdown-for-agents/
