Automated access to Read the Docs
=================================

Read the Docs generally welcomes respectful crawlers, spiders, and bots on documentation sites.
Agent use of Read the Docs is also acceptable.

Please respect the following policies when automating access to Read the Docs:

* **Rate limits**:
  Keep to under **4 requests per second**.
  Small bursts above this will not result in rate limiting or bans.
  Many projects build their documentation as a downloadable zip file or other formats.
  Please keep these downloads to 1 request per second.
  API requests have their own rate limits (see :ref:`API rate limiting <api/v3:Rate limiting>`).
* **Product dashboards**:
  Scraping pages from our product dashboards on |org_brand| or |com_brand| is frowned upon in bulk.
* **Copyright**:
  While automated access to documentation is acceptable,
  content is the copyright of the respective project owners and contributors.
* **Account creation**:
  Automated account creation is not acceptable beyond a single personal account.
* **Bot identification**:
  Identify yourself. Put a domain or email in your user agent.
  This is very helpful and reduces your chances of being blocked.
* **Markdown format**:
  Bots can request documentation pages as Markdown directly.
  See :doc:`/reference/markdown-for-agents`.
* **Traffic analysis**:
  We analyze our traffic beyond simple IP rate limiting.
  We frown upon large amounts of traffic impersonating real browsers or traffic distributed to get around rate limits.
  Distributed traffic is far more likely to result in a ban.
* **Cloudflare verification**:
  We use Cloudflare heavily (thanks to Cloudflare for sponsoring |org_brand|).
  Cloudflare `verified bots <https://developers.cloudflare.com/bots/concepts/bot/verified-bots/>`_
  are less likely to be limited or blocked.
* **Caching**:
  Read the Docs implements most caching strategies.
  Well-behaved crawlers can take advantage of cache headers, etags, date headers, and more.
  Cached requests generally don't count against rate limits.

Please help keep the web open by respecting these policies.
Read our blog post about `AI crawler abuse <https://about.readthedocs.com/blog/2024/07/ai-crawlers-abuse/>`_ to understand the impact of poor behavior.


Special considerations
----------------------

We are open to special considerations or increased rate limits on a case-by-case basis.
Please :doc:`contact support </support>` to discuss your needs.

If you believe you have been incorrectly limited or blocked,
please :doc:`contact support </support>` with details about your user agent and the requesting IP block.
Please include the Cloudflare `Ray ID <https://developers.cloudflare.com/fundamentals/reference/cloudflare-ray-id/>`_ from the blocking page if possible.
