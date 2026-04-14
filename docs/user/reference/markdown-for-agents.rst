Markdown for AI agents
======================

Read the Docs serves a Markdown version of documentation pages to clients that request it,
using HTTP content negotiation.
Markdown is smaller and easier to parse than rendered HTML,
which makes it a better format for AI agents and language models to consume.

This feature is **enabled automatically** on all documentation domains hosted on Read the Docs,
with no configuration required.
Browsers continue to receive the regular HTML version of your documentation.

A request with ``Accept: text/markdown`` returns a Markdown response:

.. code-block:: bash

   $ curl -i https://docs.readthedocs.com/platform/stable/ -H "Accept: text/markdown"
   HTTP/2 200
   content-type: text/markdown; charset=utf-8
   vary: accept
   x-markdown-tokens: 1496
   content-signal: ai-train=yes, search=yes, ai-input=yes

   ---
   description: Automate building, versioning, and hosting of your technical documentation continuously on Read the Docs.
   title: Read the Docs: documentation simplified
   ---

   ...

This feature is powered by `Cloudflare`_.
See the `Cloudflare blog post on Markdown for agents`_ for more details about how the conversion works.

.. seealso::

   :doc:`/reference/llms-txt`
     Serve a custom ``llms.txt`` file to guide AI agents to the most relevant pages of your documentation.

   :doc:`/reference/agent-skills`
     Use Read the Docs Agent Skills to help AI agents work with Read the Docs APIs and configuration.

.. _Cloudflare: https://www.cloudflare.com/
.. _Cloudflare blog post on Markdown for agents: https://blog.cloudflare.com/markdown-for-agents/
