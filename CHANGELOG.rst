Version 9.9.0
-------------

:Date: March 14, 2023

* `@github-actions[bot] <https://github.com/github-actions[bot]>`__: Dependencies: all packages updated via pip-tools (`#10139 <https://github.com/readthedocs/readthedocs.org/pull/10139>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix typo (`#10130 <https://github.com/readthedocs/readthedocs.org/pull/10130>`__)
* `@humitos <https://github.com/humitos>`__: Lint: one step forward through linting our code (`#10129 <https://github.com/readthedocs/readthedocs.org/pull/10129>`__)
* `@humitos <https://github.com/humitos>`__: Build: check for `_build/html` directory and fail if exists (`#10126 <https://github.com/readthedocs/readthedocs.org/pull/10126>`__)
* `@humitos <https://github.com/humitos>`__: Telemetry: typo on Celery task (`#10125 <https://github.com/readthedocs/readthedocs.org/pull/10125>`__)
* `@stsewd <https://github.com/stsewd>`__: Proxito: actually cache robots.txt and sitemap.xml (`#10123 <https://github.com/readthedocs/readthedocs.org/pull/10123>`__)
* `@humitos <https://github.com/humitos>`__: Proxito: add another model to cacheops (`#10121 <https://github.com/readthedocs/readthedocs.org/pull/10121>`__)
* `@humitos <https://github.com/humitos>`__: Build: pass shell commands directly (`build.jobs` / `build.commands)` (`#10119 <https://github.com/readthedocs/readthedocs.org/pull/10119>`__)
* `@humitos <https://github.com/humitos>`__: Release 9.8.0 (`#10116 <https://github.com/readthedocs/readthedocs.org/pull/10116>`__)
* `@humitos <https://github.com/humitos>`__: Downloadable artifacts: make PDF and ePub opt-in by default (`#10115 <https://github.com/readthedocs/readthedocs.org/pull/10115>`__)
* `@humitos <https://github.com/humitos>`__: Build: fail PDF command (`latexmk`) if exit code != 0 (`#10113 <https://github.com/readthedocs/readthedocs.org/pull/10113>`__)
* `@humitos <https://github.com/humitos>`__: pre-commit: move `prospector` inside pre-commit (`#10105 <https://github.com/readthedocs/readthedocs.org/pull/10105>`__)
* `@stsewd <https://github.com/stsewd>`__: Proxito: use unresolver in 404 handler (`#10074 <https://github.com/readthedocs/readthedocs.org/pull/10074>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Add beta version of doc diff library for testing (`#9546 <https://github.com/readthedocs/readthedocs.org/pull/9546>`__)

Version 9.8.0
-------------

:Date: March 07, 2023

* `@humitos <https://github.com/humitos>`__: Downloadable artifacts: make PDF and ePub opt-in by default (`#10115 <https://github.com/readthedocs/readthedocs.org/pull/10115>`__)
* `@humitos <https://github.com/humitos>`__: Proxito: cacheops right model (`#10111 <https://github.com/readthedocs/readthedocs.org/pull/10111>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: fix term reference (`#10110 <https://github.com/readthedocs/readthedocs.org/pull/10110>`__)
* `@humitos <https://github.com/humitos>`__: Development: allow to define the logging level via an env variable (`#10109 <https://github.com/readthedocs/readthedocs.org/pull/10109>`__)
* `@humitos <https://github.com/humitos>`__: Celery: cheat `job_status` view to return `finished` after 5 polls (`#10107 <https://github.com/readthedocs/readthedocs.org/pull/10107>`__)
* `@humitos <https://github.com/humitos>`__: Proxito: use cacheops for 2 more models (`#10106 <https://github.com/readthedocs/readthedocs.org/pull/10106>`__)
* `@github-actions[bot] <https://github.com/github-actions[bot]>`__: Dependencies: all packages updated via pip-tools (`#10104 <https://github.com/readthedocs/readthedocs.org/pull/10104>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove unused tests (`#10099 <https://github.com/readthedocs/readthedocs.org/pull/10099>`__)
* `@stsewd <https://github.com/stsewd>`__: Canonical redirects: check if the project supports custom domains (`#10098 <https://github.com/readthedocs/readthedocs.org/pull/10098>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix .com tests (`#10097 <https://github.com/readthedocs/readthedocs.org/pull/10097>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix migration (`#10096 <https://github.com/readthedocs/readthedocs.org/pull/10096>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Move a reference and remove an empty paranthesis (`#10093 <https://github.com/readthedocs/readthedocs.org/pull/10093>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Update documentation for search.ignore (`#10091 <https://github.com/readthedocs/readthedocs.org/pull/10091>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Fix intersphinx references to myst-parser (updated in myst-parser 0.19) (`#10090 <https://github.com/readthedocs/readthedocs.org/pull/10090>`__)
* `@stsewd <https://github.com/stsewd>`__: Update changelog with security fixes (`#10088 <https://github.com/readthedocs/readthedocs.org/pull/10088>`__)
* `@humitos <https://github.com/humitos>`__: Analytics: add Plausible to our dashboard (`#10087 <https://github.com/readthedocs/readthedocs.org/pull/10087>`__)
* `@humitos <https://github.com/humitos>`__: Docs: add Plausible (`#10086 <https://github.com/readthedocs/readthedocs.org/pull/10086>`__)
* `@stsewd <https://github.com/stsewd>`__: Proxito: refactor canonical redirects (`#10069 <https://github.com/readthedocs/readthedocs.org/pull/10069>`__)
* `@stsewd <https://github.com/stsewd>`__: Proxito: simplify caching logic (`#10067 <https://github.com/readthedocs/readthedocs.org/pull/10067>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add X-Content-Type-Options as a custom domain header (`#10062 <https://github.com/readthedocs/readthedocs.org/pull/10062>`__)
* `@stsewd <https://github.com/stsewd>`__: Proxito V2 (`#10044 <https://github.com/readthedocs/readthedocs.org/pull/10044>`__)
* `@stsewd <https://github.com/stsewd>`__: Proxito: adapt unresolver to make it usable for proxito (`#10037 <https://github.com/readthedocs/readthedocs.org/pull/10037>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Add beta version of doc diff library for testing (`#9546 <https://github.com/readthedocs/readthedocs.org/pull/9546>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Support the new Google analytics gtag.js (`#7691 <https://github.com/readthedocs/readthedocs.org/pull/7691>`__)

Version 9.7.0
-------------

**This release contains one security fix. For more information, see:**

- `GHSA-h4cf-8gv8-4chf <https://github.com/readthedocs/readthedocs.org/security/advisories/GHSA-h4cf-8gv8-4chf>`__

:Date: February 28, 2023

* `@humitos <https://github.com/humitos>`__: Celery: delete Telemetry data that's at most 3 months older (`#10079 <https://github.com/readthedocs/readthedocs.org/pull/10079>`__)
* `@humitos <https://github.com/humitos>`__: Celery: consider only `PageView` from the last 3 months (`#10078 <https://github.com/readthedocs/readthedocs.org/pull/10078>`__)
* `@humitos <https://github.com/humitos>`__: Celery: limit `archive_builds_task` query to last 90 day ago (`#10077 <https://github.com/readthedocs/readthedocs.org/pull/10077>`__)
* `@humitos <https://github.com/humitos>`__: Celery: bugfix when deleting pidbox keys (`#10076 <https://github.com/readthedocs/readthedocs.org/pull/10076>`__)
* `@humitos <https://github.com/humitos>`__: Proxito: use `django-cacheops` to cache some querysets (`#10075 <https://github.com/readthedocs/readthedocs.org/pull/10075>`__)
* `@github-actions[bot] <https://github.com/github-actions[bot]>`__: Dependencies: all packages updated via pip-tools (`#10072 <https://github.com/readthedocs/readthedocs.org/pull/10072>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Docs: Add opengraph (`#10066 <https://github.com/readthedocs/readthedocs.org/pull/10066>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Subscriptions: Set organization name in Stripe (`#10064 <https://github.com/readthedocs/readthedocs.org/pull/10064>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Support delisting of projects (`#10060 <https://github.com/readthedocs/readthedocs.org/pull/10060>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Fix undeclared labels after refactor + fix root causes (`#10059 <https://github.com/readthedocs/readthedocs.org/pull/10059>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Replace duplicate information about staff and contributors with a seealso:: (`#10056 <https://github.com/readthedocs/readthedocs.org/pull/10056>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Use "Sentence case" for titles (`#10055 <https://github.com/readthedocs/readthedocs.org/pull/10055>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Make fancy new build failed email (`#10054 <https://github.com/readthedocs/readthedocs.org/pull/10054>`__)
* `@humitos <https://github.com/humitos>`__:  Metric: define build latency metric  (`#10053 <https://github.com/readthedocs/readthedocs.org/pull/10053>`__)
* `@humitos <https://github.com/humitos>`__: Revert "Requirements: unpin `newrelic` (#10041)" (`#10052 <https://github.com/readthedocs/readthedocs.org/pull/10052>`__)
* `@humitos <https://github.com/humitos>`__: Release 9.6.0 (`#10050 <https://github.com/readthedocs/readthedocs.org/pull/10050>`__)
* `@humitos <https://github.com/humitos>`__: Metrics: update URL for latency metric (`#10048 <https://github.com/readthedocs/readthedocs.org/pull/10048>`__)
* `@humitos <https://github.com/humitos>`__: Build: log usage of old output directory `_build/html` (`#10038 <https://github.com/readthedocs/readthedocs.org/pull/10038>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Pin django-filter (`#2499 <https://github.com/readthedocs/readthedocs.org/pull/2499>`__)

Version 9.6.0
-------------

:Date: February 21, 2023

* `@humitos <https://github.com/humitos>`__: Metrics: update URL for latency metric (`#10048 <https://github.com/readthedocs/readthedocs.org/pull/10048>`__)
* `@github-actions[bot] <https://github.com/github-actions[bot]>`__: Dependencies: all packages updated via pip-tools (`#10045 <https://github.com/readthedocs/readthedocs.org/pull/10045>`__)
* `@humitos <https://github.com/humitos>`__: Submodule: update common (`#10043 <https://github.com/readthedocs/readthedocs.org/pull/10043>`__)
* `@humitos <https://github.com/humitos>`__: Requirements: unpin `newrelic` (`#10041 <https://github.com/readthedocs/readthedocs.org/pull/10041>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: emojis in TOC captions, FontAwesome on external links in TOC (Diátaxis) (`#10039 <https://github.com/readthedocs/readthedocs.org/pull/10039>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Merge Diataxis into `main`! (`#10034 <https://github.com/readthedocs/readthedocs.org/pull/10034>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Docs: Upgrade Sphinx & sphinx_rtd_theme (`#10033 <https://github.com/readthedocs/readthedocs.org/pull/10033>`__)
* `@stsewd <https://github.com/stsewd>`__: Proxito: use unresolved domain on page redirect view (`#10032 <https://github.com/readthedocs/readthedocs.org/pull/10032>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Docs: Refactor Reproducible Builds page (Diátaxis) (`#10030 <https://github.com/readthedocs/readthedocs.org/pull/10030>`__)
* `@stsewd <https://github.com/stsewd>`__: Proxito: make use un project from unresolved_domain in some views (`#10029 <https://github.com/readthedocs/readthedocs.org/pull/10029>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Docs: Refactor the build & build customization pages (Diátaxis) (`#10028 <https://github.com/readthedocs/readthedocs.org/pull/10028>`__)
* `@stsewd <https://github.com/stsewd>`__: Proxito: move "canonicalizing" logic to docs view (`#10027 <https://github.com/readthedocs/readthedocs.org/pull/10027>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Navigation reorder (Diátaxis) (`#10026 <https://github.com/readthedocs/readthedocs.org/pull/10026>`__)
* `@humitos <https://github.com/humitos>`__: APIv2: better build command sanitization (`#10025 <https://github.com/readthedocs/readthedocs.org/pull/10025>`__)
* `@humitos <https://github.com/humitos>`__: Embed API: Glossary terms sharing description (Sphinx) (`#10024 <https://github.com/readthedocs/readthedocs.org/pull/10024>`__)
* `@humitos <https://github.com/humitos>`__: Builds: ignore cancelling the build at "Uploading" state (`#10006 <https://github.com/readthedocs/readthedocs.org/pull/10006>`__)
* `@humitos <https://github.com/humitos>`__: Build: expose `READTHEDOCS_VIRTUALENV_PATH` variable (`#9971 <https://github.com/readthedocs/readthedocs.org/pull/9971>`__)

Version 9.5.0
-------------

**This release contains one security fix. For more information, see:**

- `GHSA-mp38-vprc-7hf5 <https://github.com/readthedocs/readthedocs.org/security/advisories/GHSA-mp38-vprc-7hf5>`__

:Date: February 13, 2023

* `@agjohnson <https://github.com/agjohnson>`__: Bump to latest common (`#10019 <https://github.com/readthedocs/readthedocs.org/pull/10019>`__)
* `@github-actions[bot] <https://github.com/github-actions[bot]>`__: Dependencies: all packages updated via pip-tools (`#10014 <https://github.com/readthedocs/readthedocs.org/pull/10014>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Very small text update (`#10012 <https://github.com/readthedocs/readthedocs.org/pull/10012>`__)
* `@sondalex <https://github.com/sondalex>`__: Fix code block indentation in Jupyter user guide (`#10008 <https://github.com/readthedocs/readthedocs.org/pull/10008>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Refactor all business features into feature reference + change "privacy level" page (Diátaxis) (`#10007 <https://github.com/readthedocs/readthedocs.org/pull/10007>`__)
* `@humitos <https://github.com/humitos>`__: Redis: use `django-redis` and add password (`#10005 <https://github.com/readthedocs/readthedocs.org/pull/10005>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Relabel SEO guide as explanation (Diátaxis) (`#10004 <https://github.com/readthedocs/readthedocs.org/pull/10004>`__)
* `@humitos <https://github.com/humitos>`__: Celery: cleanup `pidbox` keys (`#10002 <https://github.com/readthedocs/readthedocs.org/pull/10002>`__)
* `@stsewd <https://github.com/stsewd>`__: Use new maintained django-cors-headers package (`#10000 <https://github.com/readthedocs/readthedocs.org/pull/10000>`__)
* `@stsewd <https://github.com/stsewd>`__: Document about cross-site request (`#9999 <https://github.com/readthedocs/readthedocs.org/pull/9999>`__)
* `@stsewd <https://github.com/stsewd>`__: Analytics API: catch unresolver exceptions (`#9998 <https://github.com/readthedocs/readthedocs.org/pull/9998>`__)
* `@humitos <https://github.com/humitos>`__: Requirements: remove `django-kombu` (`#9996 <https://github.com/readthedocs/readthedocs.org/pull/9996>`__)
* `@humitos <https://github.com/humitos>`__: Release 9.4.0 (`#9994 <https://github.com/readthedocs/readthedocs.org/pull/9994>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Fix ordering of filter for most recently built project (`#9992 <https://github.com/readthedocs/readthedocs.org/pull/9992>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Refactor security logs as reference (Diátaxis) (`#9985 <https://github.com/readthedocs/readthedocs.org/pull/9985>`__)
* `@humitos <https://github.com/humitos>`__: Proxito: always check `404/index.hmtml` (`#9983 <https://github.com/readthedocs/readthedocs.org/pull/9983>`__)
* `@stsewd <https://github.com/stsewd>`__: Proxito: save one queryset (`#9980 <https://github.com/readthedocs/readthedocs.org/pull/9980>`__)
* `@humitos <https://github.com/humitos>`__: Settings: simplify all the settings removing a whole old layer (`dev`) (`#9978 <https://github.com/readthedocs/readthedocs.org/pull/9978>`__)
* `@humitos <https://github.com/humitos>`__: Build: expose `READTHEDOCS_VIRTUALENV_PATH` variable (`#9971 <https://github.com/readthedocs/readthedocs.org/pull/9971>`__)
* `@humitos <https://github.com/humitos>`__: Build: remove `pdflatex` support (`#9967 <https://github.com/readthedocs/readthedocs.org/pull/9967>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Refactor "Environment variables" into 3 articles (Diátaxis) (`#9966 <https://github.com/readthedocs/readthedocs.org/pull/9966>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Split "Automation rules" into reference and how-to (Diátaxis) (`#9953 <https://github.com/readthedocs/readthedocs.org/pull/9953>`__)
* `@stsewd <https://github.com/stsewd>`__: Test new readthedocs-sphinx-search release (`#9934 <https://github.com/readthedocs/readthedocs.org/pull/9934>`__)
* `@stsewd <https://github.com/stsewd>`__: Subscriptions: use getattr for getting related organization (`#9932 <https://github.com/readthedocs/readthedocs.org/pull/9932>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Allow searching & filtering VersionAutomationRuleAdmin (`#9917 <https://github.com/readthedocs/readthedocs.org/pull/9917>`__)
* `@humitos <https://github.com/humitos>`__: Build: use environment variable `$READTHEDOCS_OUTPUT` to define output directory (`#9913 <https://github.com/readthedocs/readthedocs.org/pull/9913>`__)

Version 9.4.0
-------------

**This release contains one security fix. For more information, see:**

- `GHSA-5w8m-r7jm-mhp9 <https://github.com/readthedocs/readthedocs.org/security/advisories/GHSA-5w8m-r7jm-mhp9>`__

:Date: February 07, 2023

* `@agjohnson <https://github.com/agjohnson>`__: Fix ordering of filter for most recently built project (`#9992 <https://github.com/readthedocs/readthedocs.org/pull/9992>`__)
* `@github-actions[bot] <https://github.com/github-actions[bot]>`__: Dependencies: all packages updated via pip-tools (`#9987 <https://github.com/readthedocs/readthedocs.org/pull/9987>`__)
* `@humitos <https://github.com/humitos>`__: Proxito: always check `404/index.hmtml` (`#9983 <https://github.com/readthedocs/readthedocs.org/pull/9983>`__)
* `@humitos <https://github.com/humitos>`__: Docs: remove outdated and complex code and dependencies (`#9981 <https://github.com/readthedocs/readthedocs.org/pull/9981>`__)
* `@stsewd <https://github.com/stsewd>`__: Proxito: save one queryset (`#9980 <https://github.com/readthedocs/readthedocs.org/pull/9980>`__)
* `@humitos <https://github.com/humitos>`__: Common: update `common/` submodule (`#9979 <https://github.com/readthedocs/readthedocs.org/pull/9979>`__)
* `@humitos <https://github.com/humitos>`__: Settings: simplify all the settings removing a whole old layer (`dev`) (`#9978 <https://github.com/readthedocs/readthedocs.org/pull/9978>`__)
* `@humitos <https://github.com/humitos>`__: Development: use `gunicorn` for `web` and `proxito` (`#9977 <https://github.com/readthedocs/readthedocs.org/pull/9977>`__)
* `@stsewd <https://github.com/stsewd>`__: Subscriptions: match stripe customer description with org name (`#9976 <https://github.com/readthedocs/readthedocs.org/pull/9976>`__)
* `@stsewd <https://github.com/stsewd>`__: Update security docs (`#9973 <https://github.com/readthedocs/readthedocs.org/pull/9973>`__)
* `@humitos <https://github.com/humitos>`__: Management commands: remove unused ones (`#9972 <https://github.com/readthedocs/readthedocs.org/pull/9972>`__)
* `@humitos <https://github.com/humitos>`__: Build: expose `READTHEDOCS_VIRTUALENV_PATH` variable (`#9971 <https://github.com/readthedocs/readthedocs.org/pull/9971>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove custom CORS logic (`#9945 <https://github.com/readthedocs/readthedocs.org/pull/9945>`__)
* `@stsewd <https://github.com/stsewd>`__: Proxito: refactor middleware (`#9933 <https://github.com/readthedocs/readthedocs.org/pull/9933>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Remove html_theme_path from conf.py (`#9923 <https://github.com/readthedocs/readthedocs.org/pull/9923>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Relabel Automatic Redirects as "Incoming links: Best practices and redirects" (Diátaxis) (`#9896 <https://github.com/readthedocs/readthedocs.org/pull/9896>`__)
* `@mwtoews <https://github.com/mwtoews>`__: Docs: add warning that pull requests only build HTML and not other formats (`#9892 <https://github.com/readthedocs/readthedocs.org/pull/9892>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix status reporting on PRs with the magic exit code (`#9807 <https://github.com/readthedocs/readthedocs.org/pull/9807>`__)
* `@stsewd <https://github.com/stsewd>`__: Proxito: refactor doc serving (`#9726 <https://github.com/readthedocs/readthedocs.org/pull/9726>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Do not assign html_theme_path (`#9654 <https://github.com/readthedocs/readthedocs.org/pull/9654>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Switch to universal analytics (`#3495 <https://github.com/readthedocs/readthedocs.org/pull/3495>`__)

Version 9.3.1
-------------

:Date: January 30, 2023

* `@ericholscher <https://github.com/ericholscher>`__: Add documentation page on Commercial subscriptions (`#9963 <https://github.com/readthedocs/readthedocs.org/pull/9963>`__)
* `@humitos <https://github.com/humitos>`__: MkDocs builder: use proper relative path for `--site-dir` (`#9962 <https://github.com/readthedocs/readthedocs.org/pull/9962>`__)
* `@github-actions[bot] <https://github.com/github-actions[bot]>`__: Dependencies: all packages updated via pip-tools (`#9960 <https://github.com/readthedocs/readthedocs.org/pull/9960>`__)
* `@humitos <https://github.com/humitos>`__: Requirements: reduce complexity (`#9956 <https://github.com/readthedocs/readthedocs.org/pull/9956>`__)
* `@humitos <https://github.com/humitos>`__: Build: rclone retries when uploading artifacts (`#9954 <https://github.com/readthedocs/readthedocs.org/pull/9954>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Relabel badges as feature reference (Diátaxis) (`#9951 <https://github.com/readthedocs/readthedocs.org/pull/9951>`__)
* `@humitos <https://github.com/humitos>`__: Build: improve `concurent` queryset (`#9950 <https://github.com/readthedocs/readthedocs.org/pull/9950>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Make the GSOC page orphaned (Diátaxis) (`#9949 <https://github.com/readthedocs/readthedocs.org/pull/9949>`__)
* `@humitos <https://github.com/humitos>`__: Celery: ignore task results (`#9944 <https://github.com/readthedocs/readthedocs.org/pull/9944>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Translations: a few copy issues and translator requests (`#9937 <https://github.com/readthedocs/readthedocs.org/pull/9937>`__)
* `@humitos <https://github.com/humitos>`__: Release 9.3.0 (`#9929 <https://github.com/readthedocs/readthedocs.org/pull/9929>`__)
* `@humitos <https://github.com/humitos>`__: Logging: log slugs when at least one of their builds was finished (`#9928 <https://github.com/readthedocs/readthedocs.org/pull/9928>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Relabel pages to new top-level "Reference/Policies and legal documents" (Diátaxis) (`#9916 <https://github.com/readthedocs/readthedocs.org/pull/9916>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Move Main Features and Feature Flags to "Reference/Features" (Diátaxis) (`#9915 <https://github.com/readthedocs/readthedocs.org/pull/9915>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Add new section "How-to / Troubleshooting" and move 2 existing troubleshooting pages (`#9914 <https://github.com/readthedocs/readthedocs.org/pull/9914>`__)
* `@stsewd <https://github.com/stsewd>`__: Logs: fix exception logging (`#9912 <https://github.com/readthedocs/readthedocs.org/pull/9912>`__)
* `@stsewd <https://github.com/stsewd>`__: CORS: don't allow to pass credentials by default (`#9904 <https://github.com/readthedocs/readthedocs.org/pull/9904>`__)
* `@benjaoming <https://github.com/benjaoming>`__: CI: Add option `--show-diff-on-failure`  to pre-commit (`#9893 <https://github.com/readthedocs/readthedocs.org/pull/9893>`__)
* `@stsewd <https://github.com/stsewd>`__: Build storage: add additional checks for the source dir (`#9890 <https://github.com/readthedocs/readthedocs.org/pull/9890>`__)
* `@stsewd <https://github.com/stsewd>`__: Build: use rclone for sync (`#9842 <https://github.com/readthedocs/readthedocs.org/pull/9842>`__)
* `@humitos <https://github.com/humitos>`__: Git backend: make `default_branch` to point to VCS' default branch (`#9424 <https://github.com/readthedocs/readthedocs.org/pull/9424>`__)
* `@stsewd <https://github.com/stsewd>`__: Subscriptions: avoid double deletion (`#9341 <https://github.com/readthedocs/readthedocs.org/pull/9341>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Make Build models default to `triggered` (`#8031 <https://github.com/readthedocs/readthedocs.org/pull/8031>`__)

Version 9.3.0
-------------

:Date: January 24, 2023

* `@github-actions[bot] <https://github.com/github-actions[bot]>`__: Dependencies: all packages updated via pip-tools (`#9925 <https://github.com/readthedocs/readthedocs.org/pull/9925>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: FAQ title/question tweak (`#9919 <https://github.com/readthedocs/readthedocs.org/pull/9919>`__)
* `@stsewd <https://github.com/stsewd>`__: Logs: fix exception logging (`#9912 <https://github.com/readthedocs/readthedocs.org/pull/9912>`__)
* `@stsewd <https://github.com/stsewd>`__: Add new allauth templates (`#9909 <https://github.com/readthedocs/readthedocs.org/pull/9909>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Move and update FAQ (Diátaxis) (`#9908 <https://github.com/readthedocs/readthedocs.org/pull/9908>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 9.2.0 (`#9905 <https://github.com/readthedocs/readthedocs.org/pull/9905>`__)
* `@stsewd <https://github.com/stsewd>`__: CORS: don't allow to pass credentials by default (`#9904 <https://github.com/readthedocs/readthedocs.org/pull/9904>`__)
* `@abe-101 <https://github.com/abe-101>`__: rm mention of docs/requirements.txt from tutorial (`#9902 <https://github.com/readthedocs/readthedocs.org/pull/9902>`__)
* `@github-actions[bot] <https://github.com/github-actions[bot]>`__: Dependencies: all packages updated via pip-tools (`#9898 <https://github.com/readthedocs/readthedocs.org/pull/9898>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Relabel Server Side Search (`#9897 <https://github.com/readthedocs/readthedocs.org/pull/9897>`__)
* `@humitos <https://github.com/humitos>`__: Build: standardize output directory for artifacts (`#9888 <https://github.com/readthedocs/readthedocs.org/pull/9888>`__)
* `@humitos <https://github.com/humitos>`__: Command `contact_owners`: add support to filter by usernames (`#9882 <https://github.com/readthedocs/readthedocs.org/pull/9882>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Park resolutions to common build problems in FAQ (`#9472 <https://github.com/readthedocs/readthedocs.org/pull/9472>`__)
* `@stsewd <https://github.com/stsewd>`__: Subscriptions: avoid double deletion (`#9341 <https://github.com/readthedocs/readthedocs.org/pull/9341>`__)

Version 9.2.0
-------------

**This release contains two security fixes. For more information, see our GitHub advisories:**

- `GHSA-7fcx-wwr3-99jv <https://github.com/readthedocs/readthedocs.org/security/advisories/GHSA-7fcx-wwr3-99jv>`__
- `GHSA-hqwg-gjqw-h5wg <https://github.com/readthedocs/readthedocs.org/security/advisories/GHSA-hqwg-gjqw-h5wg>`__

:Date: January 16, 2023

* `@github-actions[bot] <https://github.com/github-actions[bot]>`__: Dependencies: all packages updated via pip-tools (`#9898 <https://github.com/readthedocs/readthedocs.org/pull/9898>`__)
* `@benjaoming <https://github.com/benjaoming>`__: UI updates to Connected Accounts (`#9891 <https://github.com/readthedocs/readthedocs.org/pull/9891>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Replace DPA text with link to our presigned DPA (`#9883 <https://github.com/readthedocs/readthedocs.org/pull/9883>`__)
* `@humitos <https://github.com/humitos>`__: Release 9.1.3 (`#9881 <https://github.com/readthedocs/readthedocs.org/pull/9881>`__)
* `@sethfischer <https://github.com/sethfischer>`__: Docs: correct Python console block type (`#9880 <https://github.com/readthedocs/readthedocs.org/pull/9880>`__)
* `@sethfischer <https://github.com/sethfischer>`__: Docs: update build customization Poetry example (`#9879 <https://github.com/readthedocs/readthedocs.org/pull/9879>`__)
* `@stsewd <https://github.com/stsewd>`__: Embedded JS: Conditionally inject jQuery (`#9861 <https://github.com/readthedocs/readthedocs.org/pull/9861>`__)
* `@humitos <https://github.com/humitos>`__: EmbedAPI: decode filepath before open them from S3 storage (`#9860 <https://github.com/readthedocs/readthedocs.org/pull/9860>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Additions to style guide - placeholders, seealso::, Diátaxis and new word list entry (`#9840 <https://github.com/readthedocs/readthedocs.org/pull/9840>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Relabel and move explanation and how-tos around OAuth (Diátaxis) (`#9834 <https://github.com/readthedocs/readthedocs.org/pull/9834>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Split Custom Domains as Explanation and How-to Guide (Diátaxis) (`#9676 <https://github.com/readthedocs/readthedocs.org/pull/9676>`__)

Version 9.1.3
-------------

:Date: January 10, 2023

* `@stsewd <https://github.com/stsewd>`__: Explicitly set JQuery globals on main site (`#9877 <https://github.com/readthedocs/readthedocs.org/pull/9877>`__)
* `@github-actions[bot] <https://github.com/github-actions[bot]>`__: Dependencies: all packages updated via pip-tools (`#9872 <https://github.com/readthedocs/readthedocs.org/pull/9872>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Move reference labels outside of tabs (`#9866 <https://github.com/readthedocs/readthedocs.org/pull/9866>`__)
* `@stsewd <https://github.com/stsewd>`__: Embedded JS: Conditionally inject jQuery (`#9861 <https://github.com/readthedocs/readthedocs.org/pull/9861>`__)
* `@humitos <https://github.com/humitos>`__: EmbedAPI: decode filepath before open them from S3 storage (`#9860 <https://github.com/readthedocs/readthedocs.org/pull/9860>`__)
* `@humitos <https://github.com/humitos>`__: Release 9.1.2 (`#9858 <https://github.com/readthedocs/readthedocs.org/pull/9858>`__)
* `@github-actions[bot] <https://github.com/github-actions[bot]>`__: Dependencies: all packages updated via pip-tools (`#9853 <https://github.com/readthedocs/readthedocs.org/pull/9853>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Remove intercom from our DPA list (`#9846 <https://github.com/readthedocs/readthedocs.org/pull/9846>`__)
* `@agjohnson <https://github.com/agjohnson>`__: API: add project name/slug filters (`#9843 <https://github.com/readthedocs/readthedocs.org/pull/9843>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Relabel Organizations as Explanation (Diátaxis) (`#9836 <https://github.com/readthedocs/readthedocs.org/pull/9836>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Docs: Add subset of tests to testing docs (`#9817 <https://github.com/readthedocs/readthedocs.org/pull/9817>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Docs: Refactor downloadable docs (`#9768 <https://github.com/readthedocs/readthedocs.org/pull/9768>`__)

Version 9.1.2
-------------

:Date: January 03, 2023

* `@github-actions[bot] <https://github.com/github-actions[bot]>`__: Dependencies: all packages updated via pip-tools (`#9845 <https://github.com/readthedocs/readthedocs.org/pull/9845>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Update common submodule (`#9841 <https://github.com/readthedocs/readthedocs.org/pull/9841>`__)
* `@humitos <https://github.com/humitos>`__: Docs: update versions on config file page (`#9838 <https://github.com/readthedocs/readthedocs.org/pull/9838>`__)
* `@stsewd <https://github.com/stsewd>`__: Invitations: fix model name (object_type) (`#9837 <https://github.com/readthedocs/readthedocs.org/pull/9837>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Relabel Organizations as Explanation (Diátaxis) (`#9836 <https://github.com/readthedocs/readthedocs.org/pull/9836>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Relabel "Single version documentation" documentation from feature to explanation (Diátaxis) (`#9835 <https://github.com/readthedocs/readthedocs.org/pull/9835>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Relabel the "Science" page as Explanation (`#9832 <https://github.com/readthedocs/readthedocs.org/pull/9832>`__)
* `@humitos <https://github.com/humitos>`__: Build details page: normalize/trim command paths (second attempt) (`#9831 <https://github.com/readthedocs/readthedocs.org/pull/9831>`__)
* `@stsewd <https://github.com/stsewd>`__: Config file: update JSON schema (`#9830 <https://github.com/readthedocs/readthedocs.org/pull/9830>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Label for subproject select renamed "Child" => "Subproject" + help text added (`#9829 <https://github.com/readthedocs/readthedocs.org/pull/9829>`__)
* `@stsewd <https://github.com/stsewd>`__: Search API V3: fix view description (`#9828 <https://github.com/readthedocs/readthedocs.org/pull/9828>`__)
* `@stsewd <https://github.com/stsewd>`__: API V2: test that command is actually saved (`#9827 <https://github.com/readthedocs/readthedocs.org/pull/9827>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Removes fetching of main branch (`#9826 <https://github.com/readthedocs/readthedocs.org/pull/9826>`__)
* `@humitos <https://github.com/humitos>`__: Test: path is trimmed when returned by the API (`#9824 <https://github.com/readthedocs/readthedocs.org/pull/9824>`__)
* `@humitos <https://github.com/humitos>`__: Release 9.1.1 (`#9823 <https://github.com/readthedocs/readthedocs.org/pull/9823>`__)
* `@humitos <https://github.com/humitos>`__: Dependencies: use backtracking pip's resolver (`#9821 <https://github.com/readthedocs/readthedocs.org/pull/9821>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Split Subprojects in Explanation and How-to (Diátaxis) (`#9785 <https://github.com/readthedocs/readthedocs.org/pull/9785>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Split Traffic Analytics to a How-to guide and a Feature entry (Diátaxis) (`#9677 <https://github.com/readthedocs/readthedocs.org/pull/9677>`__)

Version 9.1.1
-------------

:Date: December 20, 2022

* `@humitos <https://github.com/humitos>`__: Dependencies: use backtracking pip's resolver (`#9821 <https://github.com/readthedocs/readthedocs.org/pull/9821>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Use sphinx-rtd-theme 1.2.0rc1 (`#9818 <https://github.com/readthedocs/readthedocs.org/pull/9818>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add subset of tests to testing docs (`#9817 <https://github.com/readthedocs/readthedocs.org/pull/9817>`__)
* `@humitos <https://github.com/humitos>`__: Build details page: normalize/trim command paths (`#9815 <https://github.com/readthedocs/readthedocs.org/pull/9815>`__)
* `@DelazJ <https://github.com/DelazJ>`__: Add link to the build notifications guide (`#9814 <https://github.com/readthedocs/readthedocs.org/pull/9814>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Break documentation style guide out into its own file (`#9813 <https://github.com/readthedocs/readthedocs.org/pull/9813>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Disable Sphinx mimetype errors on epub (`#9812 <https://github.com/readthedocs/readthedocs.org/pull/9812>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Docs: Update security log wording (`#9811 <https://github.com/readthedocs/readthedocs.org/pull/9811>`__)
* `@humitos <https://github.com/humitos>`__: Docs: configure linkcheck (`#9810 <https://github.com/readthedocs/readthedocs.org/pull/9810>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Fix build 3 warnings (`#9809 <https://github.com/readthedocs/readthedocs.org/pull/9809>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Fix silent, then loud failure after Tox 4 upgrade (`#9803 <https://github.com/readthedocs/readthedocs.org/pull/9803>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Docs: Split SSO docs into HowTo/Explanation (Diátaxis) (`#9801 <https://github.com/readthedocs/readthedocs.org/pull/9801>`__)
* `@juantocamidokura <https://github.com/juantocamidokura>`__: Docs: Remove outdated and misleading Poetry guide (`#9794 <https://github.com/readthedocs/readthedocs.org/pull/9794>`__)
* `@benjaoming <https://github.com/benjaoming>`__: CI builds: Checkout main branch in a robust way (`#9793 <https://github.com/readthedocs/readthedocs.org/pull/9793>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 9.1.0 (`#9792 <https://github.com/readthedocs/readthedocs.org/pull/9792>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Relabel Localization as Explanation (Diátaxis) (`#9790 <https://github.com/readthedocs/readthedocs.org/pull/9790>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Fix Circle CI builds: Tox 4 compatibility, add external commands to allowlist (`#9789 <https://github.com/readthedocs/readthedocs.org/pull/9789>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Do not build documentation in Circle CI, Read the Docs handles that :100: (`#9788 <https://github.com/readthedocs/readthedocs.org/pull/9788>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Move "Choosing between our two platforms" to Explanation (Diátaxis) (`#9784 <https://github.com/readthedocs/readthedocs.org/pull/9784>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Change "downloadable" to "offline" (`#9782 <https://github.com/readthedocs/readthedocs.org/pull/9782>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Adds missing translation strings (`#9770 <https://github.com/readthedocs/readthedocs.org/pull/9770>`__)
* `@humitos <https://github.com/humitos>`__: Admin: install `debug_toolbar` (`#9753 <https://github.com/readthedocs/readthedocs.org/pull/9753>`__)
* `@benjaoming <https://github.com/benjaoming>`__:  Docs: Split up Pull Request Builds into a how-to guide and reference (Diátaxis) (`#9679 <https://github.com/readthedocs/readthedocs.org/pull/9679>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Split Custom Domains as Explanation and How-to Guide (Diátaxis) (`#9676 <https://github.com/readthedocs/readthedocs.org/pull/9676>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Split and relabel VCS integration as explanation and how-to (Diátaxis) (`#9675 <https://github.com/readthedocs/readthedocs.org/pull/9675>`__)

Version 9.1.0
-------------

**This release contains an important security fix**. See more information `on the GitHub advisory <https://github.com/readthedocs/readthedocs.org/security/advisories/GHSA-368m-86q9-m99w>`_.

:Date: December 08, 2022

* `@benjaoming <https://github.com/benjaoming>`__: Docs: Move "Choosing between our two platforms" to Explanation (Diátaxis) (`#9784 <https://github.com/readthedocs/readthedocs.org/pull/9784>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Abandoned Projects policy: Relax reachability requirement (`#9783 <https://github.com/readthedocs/readthedocs.org/pull/9783>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Change "downloadable" to "offline" (`#9782 <https://github.com/readthedocs/readthedocs.org/pull/9782>`__)
* `@humitos <https://github.com/humitos>`__: Docs: fix raw directive (`#9778 <https://github.com/readthedocs/readthedocs.org/pull/9778>`__)
* `@github-actions[bot] <https://github.com/github-actions[bot]>`__: Dependencies: all packages updated via pip-tools (`#9775 <https://github.com/readthedocs/readthedocs.org/pull/9775>`__)
* `@humitos <https://github.com/humitos>`__: Settings: define default MailerLite setting (`#9769 <https://github.com/readthedocs/readthedocs.org/pull/9769>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Refactor downloadable docs (`#9768 <https://github.com/readthedocs/readthedocs.org/pull/9768>`__)
* `@humitos <https://github.com/humitos>`__: Docs: fix minor issues (`#9765 <https://github.com/readthedocs/readthedocs.org/pull/9765>`__)
* `@humitos <https://github.com/humitos>`__: Docs: validate Mastodon link (`#9764 <https://github.com/readthedocs/readthedocs.org/pull/9764>`__)

Version 9.0.0
-------------

This version upgrades our Search API experience to a v3.

:Date: November 28, 2022

* `@Jean-Maupas <https://github.com/Jean-Maupas>`__: A few text updates (`#9761 <https://github.com/readthedocs/readthedocs.org/pull/9761>`__)
* `@github-actions[bot] <https://github.com/github-actions[bot]>`__: Dependencies: all packages updated via pip-tools (`#9760 <https://github.com/readthedocs/readthedocs.org/pull/9760>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: 4 diátaxis categories at the top of the navigation sidebar (Diátaxis iteration 0) (`#9758 <https://github.com/readthedocs/readthedocs.org/pull/9758>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Be more explicit where go to in VCS intstructions (`#9757 <https://github.com/readthedocs/readthedocs.org/pull/9757>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Adding a pattern for reusing "Only on Read the Docs for Business" admonition (Diátaxis refactor) (`#9754 <https://github.com/readthedocs/readthedocs.org/pull/9754>`__)
* `@stsewd <https://github.com/stsewd>`__: Subscriptions: attach stripe subscription to organizations (`#9751 <https://github.com/readthedocs/readthedocs.org/pull/9751>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: fix parsing of parameters inside sphinx domains (`#9750 <https://github.com/readthedocs/readthedocs.org/pull/9750>`__)
* `@eltociear <https://github.com/eltociear>`__: Fix typo in private.py (`#9744 <https://github.com/readthedocs/readthedocs.org/pull/9744>`__)
* `@browniebroke <https://github.com/browniebroke>`__: Docs: update instructions to install deps with Poetry (`#9743 <https://github.com/readthedocs/readthedocs.org/pull/9743>`__)
* `@github-actions[bot] <https://github.com/github-actions[bot]>`__: Dependencies: all packages updated via pip-tools (`#9742 <https://github.com/readthedocs/readthedocs.org/pull/9742>`__)
* `@humitos <https://github.com/humitos>`__: Telemetry: include all the PyPI packages (`#9737 <https://github.com/readthedocs/readthedocs.org/pull/9737>`__)
* `@humitos <https://github.com/humitos>`__: Docs: cancel PR builds if there is no documentation changes (`#9734 <https://github.com/readthedocs/readthedocs.org/pull/9734>`__)
* `@humitos <https://github.com/humitos>`__: Docs: add an example for custom domain input (`#9733 <https://github.com/readthedocs/readthedocs.org/pull/9733>`__)
* `@humitos <https://github.com/humitos>`__: Release 8.9.0 (`#9732 <https://github.com/readthedocs/readthedocs.org/pull/9732>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add an initial policy for delisting unmaintained projects (`#9731 <https://github.com/readthedocs/readthedocs.org/pull/9731>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Admin: Make `VersionInline` Read-only (`#9697 <https://github.com/readthedocs/readthedocs.org/pull/9697>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: API V3 (`#9625 <https://github.com/readthedocs/readthedocs.org/pull/9625>`__)
* `@stsewd <https://github.com/stsewd>`__: Audit log: log invitations (`#9607 <https://github.com/readthedocs/readthedocs.org/pull/9607>`__)
* `@stsewd <https://github.com/stsewd>`__: Design doc: new search API (`#9533 <https://github.com/readthedocs/readthedocs.org/pull/9533>`__)
* `@humitos <https://github.com/humitos>`__: Docs: `poetry` example on `build.jobs` section (`#9445 <https://github.com/readthedocs/readthedocs.org/pull/9445>`__)

Version 8.9.0
-------------

:Date: November 15, 2022

* `@github-actions[bot] <https://github.com/github-actions[bot]>`__: Dependencies: all packages updated via pip-tools (`#9728 <https://github.com/readthedocs/readthedocs.org/pull/9728>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix tests (`#9725 <https://github.com/readthedocs/readthedocs.org/pull/9725>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 8.8.1 (`#9724 <https://github.com/readthedocs/readthedocs.org/pull/9724>`__)
* `@stsewd <https://github.com/stsewd>`__: Update security policy (`#9723 <https://github.com/readthedocs/readthedocs.org/pull/9723>`__)
* `@humitos <https://github.com/humitos>`__: Docs: refactor "skipping a build" section (`#9717 <https://github.com/readthedocs/readthedocs.org/pull/9717>`__)
* `@stsewd <https://github.com/stsewd>`__: Proxito: don't depend on attributes injected in the request (`#9711 <https://github.com/readthedocs/readthedocs.org/pull/9711>`__)
* `@stsewd <https://github.com/stsewd>`__: Unresolver: support external versions for single version projects (`#9709 <https://github.com/readthedocs/readthedocs.org/pull/9709>`__)
* `@stsewd <https://github.com/stsewd>`__: Domains: add expired queryset (`#9667 <https://github.com/readthedocs/readthedocs.org/pull/9667>`__)
* `@humitos <https://github.com/humitos>`__: Build: skip build based on commands' exit codes (`#9649 <https://github.com/readthedocs/readthedocs.org/pull/9649>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Change mailing list subscription to when the user validates their email (`#9384 <https://github.com/readthedocs/readthedocs.org/pull/9384>`__)

Version 8.8.1
-------------

This release contains a security fix, which is the most important part of the update.

:Date: November 09, 2022

* Security fix: https://github.com/readthedocs/readthedocs.org/security/advisories/GHSA-98pf-gfh3-x3mp
* `@stsewd <https://github.com/stsewd>`__: Unresolver: support external versions for single version projects (`#9709 <https://github.com/readthedocs/readthedocs.org/pull/9709>`__)

Version 8.8.0
-------------

:Date: November 08, 2022

* `@github-actions[bot] <https://github.com/github-actions[bot]>`__: Dependencies: all packages updated via pip-tools (`#9714 <https://github.com/readthedocs/readthedocs.org/pull/9714>`__)
* `@humitos <https://github.com/humitos>`__: Build: bump `readthedocs-sphinx-ext` to `<2.3` (`#9707 <https://github.com/readthedocs/readthedocs.org/pull/9707>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Bump to sphinx-rtd-theme to 1.1.0 (`#9701 <https://github.com/readthedocs/readthedocs.org/pull/9701>`__)
* `@humitos <https://github.com/humitos>`__: GHA: only run the preview links action on `docs/` path (`#9696 <https://github.com/readthedocs/readthedocs.org/pull/9696>`__)
* `@humitos <https://github.com/humitos>`__: Telemetry: not collect Sphinx data if there is no `conf.py` (`#9695 <https://github.com/readthedocs/readthedocs.org/pull/9695>`__)
* `@stsewd <https://github.com/stsewd>`__: Static files: don't 500 on invalid paths (`#9694 <https://github.com/readthedocs/readthedocs.org/pull/9694>`__)
* `@stsewd <https://github.com/stsewd>`__: Subscriptions: don't remove stripe id on canceled subscriptions (`#9693 <https://github.com/readthedocs/readthedocs.org/pull/9693>`__)
* `@humitos <https://github.com/humitos>`__: Build tools: upgrade all versions (`#9692 <https://github.com/readthedocs/readthedocs.org/pull/9692>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 8.7.1 (`#9691 <https://github.com/readthedocs/readthedocs.org/pull/9691>`__)
* `@github-actions[bot] <https://github.com/github-actions[bot]>`__: Dependencies: all packages updated via pip-tools (`#9688 <https://github.com/readthedocs/readthedocs.org/pull/9688>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Split up Build Notifications into feature/reference and how-to (Diátaxis) (`#9686 <https://github.com/readthedocs/readthedocs.org/pull/9686>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Run `blacken-docs` precommit hook on all files (`#9672 <https://github.com/readthedocs/readthedocs.org/pull/9672>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Proposal for sphinxcontrib-jquery (`#9665 <https://github.com/readthedocs/readthedocs.org/pull/9665>`__)
* `@stsewd <https://github.com/stsewd>`__: Subscriptions: use djstripe events to mail owners (`#9661 <https://github.com/readthedocs/readthedocs.org/pull/9661>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Use current year instead of hard-coded 2010 (`#9660 <https://github.com/readthedocs/readthedocs.org/pull/9660>`__)
* `@SyedMa3 <https://github.com/SyedMa3>`__: API v3: added support for tags in API (`#9513 <https://github.com/readthedocs/readthedocs.org/pull/9513>`__)

Version 8.7.1
-------------

:Date: October 24, 2022

* `@benjaoming <https://github.com/benjaoming>`__: Docs: Comment out the science contact form (`#9674 <https://github.com/readthedocs/readthedocs.org/pull/9674>`__)
* `@github-actions[bot] <https://github.com/github-actions[bot]>`__: Dependencies: all packages updated via pip-tools (`#9663 <https://github.com/readthedocs/readthedocs.org/pull/9663>`__)
* `@humitos <https://github.com/humitos>`__: Template: fix build details page link (`#9662 <https://github.com/readthedocs/readthedocs.org/pull/9662>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Use current year instead of hard-coded 2010 (`#9660 <https://github.com/readthedocs/readthedocs.org/pull/9660>`__)
* `@humitos <https://github.com/humitos>`__: Clean up some old code that's not used (`#9659 <https://github.com/readthedocs/readthedocs.org/pull/9659>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Adds more basic info to the default 404 page (`#9656 <https://github.com/readthedocs/readthedocs.org/pull/9656>`__)
* `@humitos <https://github.com/humitos>`__: Release 8.7.0 (`#9655 <https://github.com/readthedocs/readthedocs.org/pull/9655>`__)
* `@stsewd <https://github.com/stsewd>`__: Subscriptions: Use djstripe event handlers (`#9651 <https://github.com/readthedocs/readthedocs.org/pull/9651>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: use path for API URL (`#9646 <https://github.com/readthedocs/readthedocs.org/pull/9646>`__)
* `@humitos <https://github.com/humitos>`__: Settings: enable `django-debug-toolbar` when Django Admin is enabled (`#9641 <https://github.com/readthedocs/readthedocs.org/pull/9641>`__)
* `@humitos <https://github.com/humitos>`__: Telemetry: track Sphinx `extensions` and `html_theme` variables (`#9639 <https://github.com/readthedocs/readthedocs.org/pull/9639>`__)
* `@humitos <https://github.com/humitos>`__: Run django-upgrade (`#9628 <https://github.com/readthedocs/readthedocs.org/pull/9628>`__)
* `@evildmp <https://github.com/evildmp>`__: Docs: Made some small changes to the MyST migration how-to (`#9620 <https://github.com/readthedocs/readthedocs.org/pull/9620>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Add admin functions for wiping a version (`#5140 <https://github.com/readthedocs/readthedocs.org/pull/5140>`__)

Version 8.7.0
-------------

:Date: October 11, 2022

* `@github-actions[bot] <https://github.com/github-actions[bot]>`__: Dependencies: all packages updated via pip-tools (`#9648 <https://github.com/readthedocs/readthedocs.org/pull/9648>`__)
* `@humitos <https://github.com/humitos>`__: Settings: enable `django-debug-toolbar` when Django Admin is enabled (`#9641 <https://github.com/readthedocs/readthedocs.org/pull/9641>`__)
* `@stsewd <https://github.com/stsewd>`__: Subscriptions: use stripe price instead of relying on plan object (`#9640 <https://github.com/readthedocs/readthedocs.org/pull/9640>`__)
* `@github-actions[bot] <https://github.com/github-actions[bot]>`__: Dependencies: all packages updated via pip-tools (`#9636 <https://github.com/readthedocs/readthedocs.org/pull/9636>`__)
* `@humitos <https://github.com/humitos>`__: Query: minor improvement (`#9634 <https://github.com/readthedocs/readthedocs.org/pull/9634>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 8.6.0 (`#9630 <https://github.com/readthedocs/readthedocs.org/pull/9630>`__)
* `@humitos <https://github.com/humitos>`__: Run django-upgrade (`#9628 <https://github.com/readthedocs/readthedocs.org/pull/9628>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: refactor serializer's context (`#9624 <https://github.com/readthedocs/readthedocs.org/pull/9624>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Re-scope Intersphinx article as a how-to (`#9622 <https://github.com/readthedocs/readthedocs.org/pull/9622>`__)
* `@evildmp <https://github.com/evildmp>`__: Made some small changes to the MyST migration how-to (`#9620 <https://github.com/readthedocs/readthedocs.org/pull/9620>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: move api.py into a module (`#9616 <https://github.com/readthedocs/readthedocs.org/pull/9616>`__)
* `@humitos <https://github.com/humitos>`__: Build: remove `DEDUPLICATE_BUILDS` feature (`#9591 <https://github.com/readthedocs/readthedocs.org/pull/9591>`__)
* `@stsewd <https://github.com/stsewd>`__: Email: render template before sending it to the task (`#9538 <https://github.com/readthedocs/readthedocs.org/pull/9538>`__)

Version 8.6.0
-------------

:Date: September 28, 2022

* `@github-actions[bot] <https://github.com/github-actions[bot]>`__: Dependencies: all packages updated via pip-tools (`#9621 <https://github.com/readthedocs/readthedocs.org/pull/9621>`__)
* `@evildmp <https://github.com/evildmp>`__: Made some small changes to the MyST migration how-to (`#9620 <https://github.com/readthedocs/readthedocs.org/pull/9620>`__)
* `@boahc077 <https://github.com/boahc077>`__: ci: add minimum GitHub at the workflow level for pip-tools.yaml (`#9617 <https://github.com/readthedocs/readthedocs.org/pull/9617>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: refactor API view (`#9613 <https://github.com/readthedocs/readthedocs.org/pull/9613>`__)
* `@sashashura <https://github.com/sashashura>`__: GitHub Workflows security hardening (`#9609 <https://github.com/readthedocs/readthedocs.org/pull/9609>`__)
* `@stsewd <https://github.com/stsewd>`__: Redirects: test with/without organizations (`#9605 <https://github.com/readthedocs/readthedocs.org/pull/9605>`__)
* `@humitos <https://github.com/humitos>`__: Builds: concurrency small optimization (`#9602 <https://github.com/readthedocs/readthedocs.org/pull/9602>`__)
* `@uvidyadharan <https://github.com/uvidyadharan>`__: Update intersphinx.rst (`#9601 <https://github.com/readthedocs/readthedocs.org/pull/9601>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 8.5.0 (`#9600 <https://github.com/readthedocs/readthedocs.org/pull/9600>`__)
* `@github-actions[bot] <https://github.com/github-actions[bot]>`__: Dependencies: all packages updated via pip-tools (`#9596 <https://github.com/readthedocs/readthedocs.org/pull/9596>`__)
* `@stsewd <https://github.com/stsewd>`__: OAuth: save refresh token (`#9594 <https://github.com/readthedocs/readthedocs.org/pull/9594>`__)
* `@stsewd <https://github.com/stsewd>`__: Redirects: allow update (`#9593 <https://github.com/readthedocs/readthedocs.org/pull/9593>`__)
* `@stsewd <https://github.com/stsewd>`__: Unresolver: strict validation for external versions and other fixes (`#9534 <https://github.com/readthedocs/readthedocs.org/pull/9534>`__)
* `@stsewd <https://github.com/stsewd>`__: New unresolver implementation (`#9500 <https://github.com/readthedocs/readthedocs.org/pull/9500>`__)
* `@stsewd <https://github.com/stsewd>`__: API v3: fix organizations permissions (`#8771 <https://github.com/readthedocs/readthedocs.org/pull/8771>`__)

Version 8.5.0
-------------

:Date: September 12, 2022

* `@github-actions[bot] <https://github.com/github-actions[bot]>`__: Dependencies: all packages updated via pip-tools (`#9596 <https://github.com/readthedocs/readthedocs.org/pull/9596>`__)
* `@stsewd <https://github.com/stsewd>`__: OAuth: save refresh token (`#9594 <https://github.com/readthedocs/readthedocs.org/pull/9594>`__)
* `@humitos <https://github.com/humitos>`__: OAuth: add logging for imported GitHub RemoteRepository (`#9590 <https://github.com/readthedocs/readthedocs.org/pull/9590>`__)
* `@humitos <https://github.com/humitos>`__: Telemetry: lowercase JSON keys (`#9587 <https://github.com/readthedocs/readthedocs.org/pull/9587>`__)
* `@stsewd <https://github.com/stsewd>`__: Embedded js: fix no-sphinx docs (`#9586 <https://github.com/readthedocs/readthedocs.org/pull/9586>`__)
* `@humitos <https://github.com/humitos>`__: Release 8.4.3 (`#9584 <https://github.com/readthedocs/readthedocs.org/pull/9584>`__)
* `@github-actions[bot] <https://github.com/github-actions[bot]>`__: Dependencies: all packages updated via pip-tools (`#9583 <https://github.com/readthedocs/readthedocs.org/pull/9583>`__)
* `@stsewd <https://github.com/stsewd>`__: Invitations: delete related invitations when deleting an object (`#9582 <https://github.com/readthedocs/readthedocs.org/pull/9582>`__)
* `@stsewd <https://github.com/stsewd>`__: New unresolver implementation (`#9500 <https://github.com/readthedocs/readthedocs.org/pull/9500>`__)

Version 8.4.3
-------------

:Date: September 06, 2022

* `@github-actions[bot] <https://github.com/github-actions[bot]>`__: Dependencies: all packages updated via pip-tools (`#9583 <https://github.com/readthedocs/readthedocs.org/pull/9583>`__)
* `@stsewd <https://github.com/stsewd>`__: Invitations: delete related invitations when deleting an object (`#9582 <https://github.com/readthedocs/readthedocs.org/pull/9582>`__)
* `@humitos <https://github.com/humitos>`__: Docs: improve "Badges" page (`#9580 <https://github.com/readthedocs/readthedocs.org/pull/9580>`__)
* `@stsewd <https://github.com/stsewd>`__: Use utility function domReady instead of JQuery's .ready (`#9579 <https://github.com/readthedocs/readthedocs.org/pull/9579>`__)
* `@humitos <https://github.com/humitos>`__: Development: disable NGINX logs (`#9569 <https://github.com/readthedocs/readthedocs.org/pull/9569>`__)
* `@humitos <https://github.com/humitos>`__: Logging: log time spent to upload build artifacts (`#9568 <https://github.com/readthedocs/readthedocs.org/pull/9568>`__)
* `@humitos <https://github.com/humitos>`__: Docs: recommend using `pip` instead of `setuptools` (`#9567 <https://github.com/readthedocs/readthedocs.org/pull/9567>`__)
* `@stsewd <https://github.com/stsewd>`__: Embed API: strip leading `/` before joining path (`#9565 <https://github.com/readthedocs/readthedocs.org/pull/9565>`__)
* `@stsewd <https://github.com/stsewd>`__: Embed API: fix CORS check (`#9564 <https://github.com/readthedocs/readthedocs.org/pull/9564>`__)
* `@humitos <https://github.com/humitos>`__: Build: upgrade `commonmark` to 0.9.1 (`#9563 <https://github.com/readthedocs/readthedocs.org/pull/9563>`__)
* `@humitos <https://github.com/humitos>`__: Templates: minor typo (`#9560 <https://github.com/readthedocs/readthedocs.org/pull/9560>`__)
* `@stsewd <https://github.com/stsewd>`__: Proxito: unskip test (`#9559 <https://github.com/readthedocs/readthedocs.org/pull/9559>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 8.4.2 (`#9558 <https://github.com/readthedocs/readthedocs.org/pull/9558>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Proxito redirects: pass full_path instead of re-creating it.  (`#9557 <https://github.com/readthedocs/readthedocs.org/pull/9557>`__)
* `@stsewd <https://github.com/stsewd>`__: Embed js: use fetch API for footer (`#9551 <https://github.com/readthedocs/readthedocs.org/pull/9551>`__)
* `@stsewd <https://github.com/stsewd>`__: Subscriptions: use stripe subscriptions to show details (`#9550 <https://github.com/readthedocs/readthedocs.org/pull/9550>`__)
* `@humitos <https://github.com/humitos>`__: Build: cancel old builds  (`#9549 <https://github.com/readthedocs/readthedocs.org/pull/9549>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: HTML form for getting in touch with Read the Docs for Science (`#9543 <https://github.com/readthedocs/readthedocs.org/pull/9543>`__)
* `@humitos <https://github.com/humitos>`__: Dependencies: pin deploy dependencies (`#9537 <https://github.com/readthedocs/readthedocs.org/pull/9537>`__)
* `@humitos <https://github.com/humitos>`__: Code comment (`#9518 <https://github.com/readthedocs/readthedocs.org/pull/9518>`__)
* `@stsewd <https://github.com/stsewd>`__: Avoid jquery in rtd data (`#9493 <https://github.com/readthedocs/readthedocs.org/pull/9493>`__)
* `@stsewd <https://github.com/stsewd>`__: Use djstripe models for organization subscriptions (`#9486 <https://github.com/readthedocs/readthedocs.org/pull/9486>`__)
* `@stsewd <https://github.com/stsewd>`__: Ask for confirmation when adding a user to a project/organization/team (`#9440 <https://github.com/readthedocs/readthedocs.org/pull/9440>`__)
* `@stsewd <https://github.com/stsewd>`__: Design doc: Better handling of docs URLs (`#9425 <https://github.com/readthedocs/readthedocs.org/pull/9425>`__)
* `@stsewd <https://github.com/stsewd>`__: Security logs: delete old user security logs (`#8620 <https://github.com/readthedocs/readthedocs.org/pull/8620>`__)

Version 8.4.2
-------------

:Date: August 29, 2022

* `@ericholscher <https://github.com/ericholscher>`__: Proxito redirects: pass full_path instead of re-creating it.  (`#9557 <https://github.com/readthedocs/readthedocs.org/pull/9557>`__)
* `@humitos <https://github.com/humitos>`__: Build: cancel old builds  (`#9549 <https://github.com/readthedocs/readthedocs.org/pull/9549>`__)
* `@stsewd <https://github.com/stsewd>`__: Embedded js: update docstring (`#9547 <https://github.com/readthedocs/readthedocs.org/pull/9547>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: HTML form for getting in touch with Read the Docs for Science (`#9543 <https://github.com/readthedocs/readthedocs.org/pull/9543>`__)
* `@stsewd <https://github.com/stsewd>`__: Unresolver: port changes from #9540 (`#9542 <https://github.com/readthedocs/readthedocs.org/pull/9542>`__)
* `@stsewd <https://github.com/stsewd>`__: Domains: test tasks with organizations (`#9541 <https://github.com/readthedocs/readthedocs.org/pull/9541>`__)
* `@stsewd <https://github.com/stsewd>`__: Proxito: set logging to debug (`#9540 <https://github.com/readthedocs/readthedocs.org/pull/9540>`__)
* `@humitos <https://github.com/humitos>`__: Dependencies: pin deploy dependencies (`#9537 <https://github.com/readthedocs/readthedocs.org/pull/9537>`__)
* `@humitos <https://github.com/humitos>`__: Release 8.4.1 (`#9536 <https://github.com/readthedocs/readthedocs.org/pull/9536>`__)
* `@humitos <https://github.com/humitos>`__: Dependencies: pin django-structlog to 2.2.1 (`#9535 <https://github.com/readthedocs/readthedocs.org/pull/9535>`__)
* `@humitos <https://github.com/humitos>`__: Code comment (`#9518 <https://github.com/readthedocs/readthedocs.org/pull/9518>`__)
* `@stsewd <https://github.com/stsewd>`__: Embedded js: remove more dependency on jquery (`#9515 <https://github.com/readthedocs/readthedocs.org/pull/9515>`__)
* `@humitos <https://github.com/humitos>`__: Telemetry: collect user's requirements (`#9514 <https://github.com/readthedocs/readthedocs.org/pull/9514>`__)
* `@stsewd <https://github.com/stsewd>`__: Embedded js: remove some dependency from jquery (`#9508 <https://github.com/readthedocs/readthedocs.org/pull/9508>`__)
* `@stsewd <https://github.com/stsewd>`__: New unresolver implementation (`#9500 <https://github.com/readthedocs/readthedocs.org/pull/9500>`__)
* `@stsewd <https://github.com/stsewd>`__: Use djstripe models for organization subscriptions (`#9486 <https://github.com/readthedocs/readthedocs.org/pull/9486>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Park resolutions to common build problems in FAQ (`#9472 <https://github.com/readthedocs/readthedocs.org/pull/9472>`__)

Version 8.4.1
-------------

:Date: August 23, 2022

* `@humitos <https://github.com/humitos>`__: Dependencies: pin django-structlog to 2.2.1 (`#9535 <https://github.com/readthedocs/readthedocs.org/pull/9535>`__)
* `@xk999 <https://github.com/xk999>`__: Update Transifex link (`#9531 <https://github.com/readthedocs/readthedocs.org/pull/9531>`__)
* `@dependabot[bot] <https://github.com/dependabot[bot]>`__: Bump actions/setup-python from 3 to 4 (`#9529 <https://github.com/readthedocs/readthedocs.org/pull/9529>`__)
* `@github-actions[bot] <https://github.com/github-actions[bot]>`__: Dependencies: all packages updated via pip-tools (`#9528 <https://github.com/readthedocs/readthedocs.org/pull/9528>`__)
* `@humitos <https://github.com/humitos>`__: Telemetry: collect user's requirements (`#9514 <https://github.com/readthedocs/readthedocs.org/pull/9514>`__)
* `@stsewd <https://github.com/stsewd>`__: Teams: don't send email notification when users adds themselves to a team (`#9511 <https://github.com/readthedocs/readthedocs.org/pull/9511>`__)
* `@humitos <https://github.com/humitos>`__: Preview: escape characters (`#9509 <https://github.com/readthedocs/readthedocs.org/pull/9509>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Removes rstcheck (`#9505 <https://github.com/readthedocs/readthedocs.org/pull/9505>`__)
* `@humitos <https://github.com/humitos>`__: Release 8.4.0 (`#9504 <https://github.com/readthedocs/readthedocs.org/pull/9504>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: sphinxcontrib-video was added incorrectly (`#9501 <https://github.com/readthedocs/readthedocs.org/pull/9501>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Fix typo in build concurrency logging (`#9499 <https://github.com/readthedocs/readthedocs.org/pull/9499>`__)
* `@stsewd <https://github.com/stsewd>`__: Update template from documentation preview (`#9495 <https://github.com/readthedocs/readthedocs.org/pull/9495>`__)
* `@humitos <https://github.com/humitos>`__: Dependencies: use pip-tools for all our files  (`#9480 <https://github.com/readthedocs/readthedocs.org/pull/9480>`__)
* `@humitos <https://github.com/humitos>`__: Dependencies: use GitHub Action + pip-tools (`#9479 <https://github.com/readthedocs/readthedocs.org/pull/9479>`__)
* `@stsewd <https://github.com/stsewd>`__: Proxito: separate project slug extraction from request manipulation (`#9462 <https://github.com/readthedocs/readthedocs.org/pull/9462>`__)
* `@stsewd <https://github.com/stsewd>`__: Ask for confirmation when adding a user to a project/organization/team (`#9440 <https://github.com/readthedocs/readthedocs.org/pull/9440>`__)
* `@stsewd <https://github.com/stsewd>`__: Custom domains: track validation process (`#9428 <https://github.com/readthedocs/readthedocs.org/pull/9428>`__)

Version 8.4.0
-------------

:Date: August 16, 2022

* `@benjaoming <https://github.com/benjaoming>`__: Docs: sphinxcontrib-video was added incorrectly (`#9501 <https://github.com/readthedocs/readthedocs.org/pull/9501>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Fix typo in build concurrency logging (`#9499 <https://github.com/readthedocs/readthedocs.org/pull/9499>`__)
* `@stsewd <https://github.com/stsewd>`__: Embedded js: fix flyout click event (`#9498 <https://github.com/readthedocs/readthedocs.org/pull/9498>`__)
* `@stsewd <https://github.com/stsewd>`__: Custom urlconf: support serving static files (`#9496 <https://github.com/readthedocs/readthedocs.org/pull/9496>`__)
* `@stsewd <https://github.com/stsewd>`__: Avoid jquery in rtd data (`#9493 <https://github.com/readthedocs/readthedocs.org/pull/9493>`__)
* `@humitos <https://github.com/humitos>`__: Preview: add links to `dev` documentation (`#9491 <https://github.com/readthedocs/readthedocs.org/pull/9491>`__)
* `@humitos <https://github.com/humitos>`__: Use Read the Docs action v1 (`#9487 <https://github.com/readthedocs/readthedocs.org/pull/9487>`__)
* `@humitos <https://github.com/humitos>`__: Release 8.3.7 (`#9484 <https://github.com/readthedocs/readthedocs.org/pull/9484>`__)
* `@stsewd <https://github.com/stsewd>`__: Disable sphinx domains (`#9483 <https://github.com/readthedocs/readthedocs.org/pull/9483>`__)
* `@stsewd <https://github.com/stsewd>`__: Sphinx domain: change type of ID field (`#9482 <https://github.com/readthedocs/readthedocs.org/pull/9482>`__)
* `@humitos <https://github.com/humitos>`__: Build: unpin Pillow for unsupported Python versions (`#9473 <https://github.com/readthedocs/readthedocs.org/pull/9473>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Read the Docs for Science - new alternative with sphinx-design (`#9460 <https://github.com/readthedocs/readthedocs.org/pull/9460>`__)
* `@stsewd <https://github.com/stsewd>`__: Ask for confirmation when adding a user to a project/organization/team (`#9440 <https://github.com/readthedocs/readthedocs.org/pull/9440>`__)

Version 8.3.7
-------------

:Date: August 09, 2022

* `@stsewd <https://github.com/stsewd>`__: Sphinx domain: change type of ID field (`#9482 <https://github.com/readthedocs/readthedocs.org/pull/9482>`__)
* `@humitos <https://github.com/humitos>`__: Build: unpin Pillow for unsupported Python versions (`#9473 <https://github.com/readthedocs/readthedocs.org/pull/9473>`__)
* `@humitos <https://github.com/humitos>`__: Release 8.3.6 (`#9465 <https://github.com/readthedocs/readthedocs.org/pull/9465>`__)
* `@stsewd <https://github.com/stsewd>`__: Redirects: check only for hostname and path for infinite redirects (`#9463 <https://github.com/readthedocs/readthedocs.org/pull/9463>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Fix missing indentation on reStructuredText badge code (`#9404 <https://github.com/readthedocs/readthedocs.org/pull/9404>`__)
* `@stsewd <https://github.com/stsewd>`__: Embed JS: fix incompatibilities with sphinx 6.x (jquery removal) (`#9359 <https://github.com/readthedocs/readthedocs.org/pull/9359>`__)

Version 8.3.6
-------------

:Date: August 02, 2022

* `@stsewd <https://github.com/stsewd>`__: Build: use correct build environment for build.commands (`#9454 <https://github.com/readthedocs/readthedocs.org/pull/9454>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Fixes warnings and other noisy build messages (`#9453 <https://github.com/readthedocs/readthedocs.org/pull/9453>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 8.3.5 (`#9452 <https://github.com/readthedocs/readthedocs.org/pull/9452>`__)
* `@humitos <https://github.com/humitos>`__: GitHub Action: add link to Pull Request preview (`#9450 <https://github.com/readthedocs/readthedocs.org/pull/9450>`__)
* `@humitos <https://github.com/humitos>`__: OAuth: add logging for GitHub RemoteRepository (`#9449 <https://github.com/readthedocs/readthedocs.org/pull/9449>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Adds Jupyter Book to examples table (`#9446 <https://github.com/readthedocs/readthedocs.org/pull/9446>`__)
* `@humitos <https://github.com/humitos>`__: Docs: `poetry` example on `build.jobs` section (`#9445 <https://github.com/readthedocs/readthedocs.org/pull/9445>`__)

Version 8.3.5
-------------

:Date: July 25, 2022

* `@humitos <https://github.com/humitos>`__: GitHub Action: add link to Pull Request preview (`#9450 <https://github.com/readthedocs/readthedocs.org/pull/9450>`__)
* `@humitos <https://github.com/humitos>`__: OAuth: add logging for GitHub RemoteRepository (`#9449 <https://github.com/readthedocs/readthedocs.org/pull/9449>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Adds Jupyter Book to examples table (`#9446 <https://github.com/readthedocs/readthedocs.org/pull/9446>`__)
* `@humitos <https://github.com/humitos>`__: Docs: `poetry` example on `build.jobs` section (`#9445 <https://github.com/readthedocs/readthedocs.org/pull/9445>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Update env var docs (`#9443 <https://github.com/readthedocs/readthedocs.org/pull/9443>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Update dev domain to `devthedocs.org` (`#9442 <https://github.com/readthedocs/readthedocs.org/pull/9442>`__)
* `@humitos <https://github.com/humitos>`__: Docs: mention `docsify` on "Build customization" (`#9439 <https://github.com/readthedocs/readthedocs.org/pull/9439>`__)
* `@humitos <https://github.com/humitos>`__: Release 8.3.4 (`#9436 <https://github.com/readthedocs/readthedocs.org/pull/9436>`__)
* `@stsewd <https://github.com/stsewd>`__: Custom domains: don't allow IPs (`#9429 <https://github.com/readthedocs/readthedocs.org/pull/9429>`__)
* `@stsewd <https://github.com/stsewd>`__: Audit logs: truncate browser (`#9417 <https://github.com/readthedocs/readthedocs.org/pull/9417>`__)

Version 8.3.4
-------------

:Date: July 19, 2022

* `@stsewd <https://github.com/stsewd>`__: Fix docs (`#9432 <https://github.com/readthedocs/readthedocs.org/pull/9432>`__)
* `@stsewd <https://github.com/stsewd>`__: Build: check for self.data.version being None (`#9430 <https://github.com/readthedocs/readthedocs.org/pull/9430>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 8.3.3 (`#9427 <https://github.com/readthedocs/readthedocs.org/pull/9427>`__)
* `@stsewd <https://github.com/stsewd>`__: Redirects: merge query params from the redirect and original request (`#9420 <https://github.com/readthedocs/readthedocs.org/pull/9420>`__)
* `@stsewd <https://github.com/stsewd>`__: Audit logs: truncate browser (`#9417 <https://github.com/readthedocs/readthedocs.org/pull/9417>`__)

Version 8.3.3
-------------

:Date: July 12, 2022

* `@davidfischer <https://github.com/davidfischer>`__: Stickybox ad fix (`#9421 <https://github.com/readthedocs/readthedocs.org/pull/9421>`__)
* `@humitos <https://github.com/humitos>`__: Logging: add extra log info for oauth (`#9416 <https://github.com/readthedocs/readthedocs.org/pull/9416>`__)
* `@humitos <https://github.com/humitos>`__: OAuth: unify the exception used for the user message (`#9415 <https://github.com/readthedocs/readthedocs.org/pull/9415>`__)
* `@humitos <https://github.com/humitos>`__: Docs: improve the flyout page to include a full example (`#9413 <https://github.com/readthedocs/readthedocs.org/pull/9413>`__)
* `@humitos <https://github.com/humitos>`__: OAuth: resync `RemoteRepository` weekly for active users (`#9410 <https://github.com/readthedocs/readthedocs.org/pull/9410>`__)
* `@humitos <https://github.com/humitos>`__: OAuth: re-sync `RemoteRepository` on login (`#9409 <https://github.com/readthedocs/readthedocs.org/pull/9409>`__)
* `@stsewd <https://github.com/stsewd>`__: Analytics: make sure there is only one record with version=None (`#9408 <https://github.com/readthedocs/readthedocs.org/pull/9408>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Add frontend team codeowners rules (`#9407 <https://github.com/readthedocs/readthedocs.org/pull/9407>`__)
* `@humitos <https://github.com/humitos>`__: Telemetry: delete old `BuildData` models (`#9403 <https://github.com/readthedocs/readthedocs.org/pull/9403>`__)
* `@humitos <https://github.com/humitos>`__: Sessions: do not save on each request (`#9402 <https://github.com/readthedocs/readthedocs.org/pull/9402>`__)
* `@humitos <https://github.com/humitos>`__: Release 8.3.2 (`#9400 <https://github.com/readthedocs/readthedocs.org/pull/9400>`__)
* `@naveensrinivasan <https://github.com/naveensrinivasan>`__: chore: Included githubactions in the dependabot config (`#9396 <https://github.com/readthedocs/readthedocs.org/pull/9396>`__)
* `@stsewd <https://github.com/stsewd>`__: Build: refactor TaskData (`#9389 <https://github.com/readthedocs/readthedocs.org/pull/9389>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Add an examples section (`#9371 <https://github.com/readthedocs/readthedocs.org/pull/9371>`__)

Version 8.3.2
-------------

:Date: July 05, 2022

* `@neilnaveen <https://github.com/neilnaveen>`__: chore: Set permissions for GitHub actions (`#9394 <https://github.com/readthedocs/readthedocs.org/pull/9394>`__)
* `@humitos <https://github.com/humitos>`__: Logging: do not log the token itself (`#9393 <https://github.com/readthedocs/readthedocs.org/pull/9393>`__)
* `@stsewd <https://github.com/stsewd>`__: Test explicitly with/out organizations (`#9391 <https://github.com/readthedocs/readthedocs.org/pull/9391>`__)
* `@stsewd <https://github.com/stsewd>`__: Telemetry: skip listing conda packages on non-conda envs (`#9390 <https://github.com/readthedocs/readthedocs.org/pull/9390>`__)
* `@stsewd <https://github.com/stsewd>`__: Enable djstripe again (`#9385 <https://github.com/readthedocs/readthedocs.org/pull/9385>`__)
* `@ericholscher <https://github.com/ericholscher>`__: UX: Improve DUPLICATED_RESERVED_VERSIONS error (`#9383 <https://github.com/readthedocs/readthedocs.org/pull/9383>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 8.3.1 (`#9379 <https://github.com/readthedocs/readthedocs.org/pull/9379>`__)
* `@humitos <https://github.com/humitos>`__: Docs: remove old feature flags (`#9377 <https://github.com/readthedocs/readthedocs.org/pull/9377>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Properly log build exceptions in Celery (`#9375 <https://github.com/readthedocs/readthedocs.org/pull/9375>`__)
* `@humitos <https://github.com/humitos>`__: Middleware: use regular `HttpResponse` and log the suspicious operation (`#9366 <https://github.com/readthedocs/readthedocs.org/pull/9366>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add an explicit flyout placement option (`#9357 <https://github.com/readthedocs/readthedocs.org/pull/9357>`__)
* `@stsewd <https://github.com/stsewd>`__: PR previews: Warn users when enabling the feature on incompatible projects (`#9291 <https://github.com/readthedocs/readthedocs.org/pull/9291>`__)

Version 8.3.1
-------------

:Date: June 27, 2022

* `@ericholscher <https://github.com/ericholscher>`__: Properly log build exceptions in Celery (`#9375 <https://github.com/readthedocs/readthedocs.org/pull/9375>`__)
* `@humitos <https://github.com/humitos>`__: Docs: remove old FAQ entry (`#9374 <https://github.com/readthedocs/readthedocs.org/pull/9374>`__)
* `@humitos <https://github.com/humitos>`__: CSP header: enforce mode (`#9373 <https://github.com/readthedocs/readthedocs.org/pull/9373>`__)
* `@humitos <https://github.com/humitos>`__: Development: default value for environment variable (`#9370 <https://github.com/readthedocs/readthedocs.org/pull/9370>`__)
* `@humitos <https://github.com/humitos>`__: Middleware: use regular `HttpResponse` and log the suspicious operation (`#9366 <https://github.com/readthedocs/readthedocs.org/pull/9366>`__)
* `@humitos <https://github.com/humitos>`__: Development: remove silent and use long attribute name (`#9363 <https://github.com/readthedocs/readthedocs.org/pull/9363>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix glossary ordering (`#9362 <https://github.com/readthedocs/readthedocs.org/pull/9362>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Do not list feature overview twice (`#9361 <https://github.com/readthedocs/readthedocs.org/pull/9361>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Release 8.3.0 (`#9358 <https://github.com/readthedocs/readthedocs.org/pull/9358>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add an explicit flyout placement option (`#9357 <https://github.com/readthedocs/readthedocs.org/pull/9357>`__)
* `@humitos <https://github.com/humitos>`__: Development: allow to pass `--ngrok` when starting up (`#9353 <https://github.com/readthedocs/readthedocs.org/pull/9353>`__)
* `@humitos <https://github.com/humitos>`__: Development: avoid path collision when running multiple builders (`#9352 <https://github.com/readthedocs/readthedocs.org/pull/9352>`__)
* `@humitos <https://github.com/humitos>`__: Security: avoid requests with NULL characters (0x00) on GET (`#9350 <https://github.com/readthedocs/readthedocs.org/pull/9350>`__)
* `@humitos <https://github.com/humitos>`__: Logging: reduce log verbosity (`#9348 <https://github.com/readthedocs/readthedocs.org/pull/9348>`__)
* `@humitos <https://github.com/humitos>`__: Build: handle 422 response on send build status (`#9347 <https://github.com/readthedocs/readthedocs.org/pull/9347>`__)
* `@humitos <https://github.com/humitos>`__: Build: truncate command output (`#9346 <https://github.com/readthedocs/readthedocs.org/pull/9346>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Updates and fixes to Development Install guide (`#9319 <https://github.com/readthedocs/readthedocs.org/pull/9319>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Add DMCA takedown request for project dicom-standard (`#9311 <https://github.com/readthedocs/readthedocs.org/pull/9311>`__)

Version 8.3.0
-------------

:Date: June 20, 2022

* `@humitos <https://github.com/humitos>`__: Security: avoid requests with NULL characters (0x00) on GET (`#9350 <https://github.com/readthedocs/readthedocs.org/pull/9350>`__)
* `@humitos <https://github.com/humitos>`__: Logging: reduce log verbosity (`#9348 <https://github.com/readthedocs/readthedocs.org/pull/9348>`__)
* `@humitos <https://github.com/humitos>`__: Build: truncate command output (`#9346 <https://github.com/readthedocs/readthedocs.org/pull/9346>`__)
* `@stsewd <https://github.com/stsewd>`__: Update common (`#9345 <https://github.com/readthedocs/readthedocs.org/pull/9345>`__)
* `@stsewd <https://github.com/stsewd>`__: Subscriptions: log subscription id when canceling (`#9340 <https://github.com/readthedocs/readthedocs.org/pull/9340>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: support section titles inside header tags (`#9339 <https://github.com/readthedocs/readthedocs.org/pull/9339>`__)
* `@humitos <https://github.com/humitos>`__: Local development: use `nodemon` to watch files instead of `watchmedo` (`#9338 <https://github.com/readthedocs/readthedocs.org/pull/9338>`__)
* `@humitos <https://github.com/humitos>`__:  EmbedAPI: clean images (`src`) properly from inside a tooltip  (`#9337 <https://github.com/readthedocs/readthedocs.org/pull/9337>`__)
* `@humitos <https://github.com/humitos>`__: Development: update `common/` submodule (`#9336 <https://github.com/readthedocs/readthedocs.org/pull/9336>`__)
* `@stsewd <https://github.com/stsewd>`__: Gold: log if the subscription has more than one item (`#9334 <https://github.com/readthedocs/readthedocs.org/pull/9334>`__)
* `@humitos <https://github.com/humitos>`__: EmbedAPI: handle special case for Sphinx manual references (`#9333 <https://github.com/readthedocs/readthedocs.org/pull/9333>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Add `mc` client to `web` container (`#9331 <https://github.com/readthedocs/readthedocs.org/pull/9331>`__)
* `@humitos <https://github.com/humitos>`__: Translations: migrate `.tx/config` to new client's version format (`#9327 <https://github.com/readthedocs/readthedocs.org/pull/9327>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: index generic doctype (`#9322 <https://github.com/readthedocs/readthedocs.org/pull/9322>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Docs: Improve scoping of two potentially overlapping Triage sections (`#9302 <https://github.com/readthedocs/readthedocs.org/pull/9302>`__)

Version 8.2.0
-------------

:Date: June 14, 2022

* `@ericholscher <https://github.com/ericholscher>`__: Docs: Small edits to add a couple keywords and clarify headings (`#9329 <https://github.com/readthedocs/readthedocs.org/pull/9329>`__)
* `@humitos <https://github.com/humitos>`__: Translations: integrate Transifex into our Docker tasks (`#9326 <https://github.com/readthedocs/readthedocs.org/pull/9326>`__)
* `@humitos <https://github.com/humitos>`__: EmbedAPIv3: make usage of CDN (`#9321 <https://github.com/readthedocs/readthedocs.org/pull/9321>`__)
* `@stsewd <https://github.com/stsewd>`__: Subscriptions: handle subscriptions with multiple products/plans/items (`#9320 <https://github.com/readthedocs/readthedocs.org/pull/9320>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Update the team page (`#9309 <https://github.com/readthedocs/readthedocs.org/pull/9309>`__)
* `@stsewd <https://github.com/stsewd>`__: Stripe: use new api version (`#9308 <https://github.com/readthedocs/readthedocs.org/pull/9308>`__)
* `@humitos <https://github.com/humitos>`__: Build: avoid overwriting a variable (`#9305 <https://github.com/readthedocs/readthedocs.org/pull/9305>`__)
* `@humitos <https://github.com/humitos>`__: Integrations: handle `ping` event on GitHub (`#9303 <https://github.com/readthedocs/readthedocs.org/pull/9303>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 8.1.2 (`#9300 <https://github.com/readthedocs/readthedocs.org/pull/9300>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix Docs CI (`#9299 <https://github.com/readthedocs/readthedocs.org/pull/9299>`__)
* `@stsewd <https://github.com/stsewd>`__: Tests: test build views with organizations (`#9298 <https://github.com/readthedocs/readthedocs.org/pull/9298>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Update mentions of our roadmap to be current (`#9293 <https://github.com/readthedocs/readthedocs.org/pull/9293>`__)
* `@stsewd <https://github.com/stsewd>`__: lsremote: set max split when parsing remotes (`#9292 <https://github.com/readthedocs/readthedocs.org/pull/9292>`__)
* `@humitos <https://github.com/humitos>`__: Tests: make `tests-embedapi` require regular `tests` first (`#9289 <https://github.com/readthedocs/readthedocs.org/pull/9289>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Truncate output that we log from commands to 10 lines (`#9286 <https://github.com/readthedocs/readthedocs.org/pull/9286>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: update custom domains docs (`#9266 <https://github.com/readthedocs/readthedocs.org/pull/9266>`__)
* `@stsewd <https://github.com/stsewd>`__: Requirements: update django-allauth (`#9249 <https://github.com/readthedocs/readthedocs.org/pull/9249>`__)

Version 8.1.2
-------------

:Date: June 06, 2022

* `@ericholscher <https://github.com/ericholscher>`__: Fix Docs CI (`#9299 <https://github.com/readthedocs/readthedocs.org/pull/9299>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Update mentions of our roadmap to be current (`#9293 <https://github.com/readthedocs/readthedocs.org/pull/9293>`__)
* `@stsewd <https://github.com/stsewd>`__: lsremote: set max split when parsing remotes (`#9292 <https://github.com/readthedocs/readthedocs.org/pull/9292>`__)
* `@humitos <https://github.com/humitos>`__: Tests: make `tests-embedapi` require regular `tests` first (`#9289 <https://github.com/readthedocs/readthedocs.org/pull/9289>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Update 8.1.1 changelog with hotfixes (`#9288 <https://github.com/readthedocs/readthedocs.org/pull/9288>`__)
* `@stsewd <https://github.com/stsewd>`__: Cancel build: get build from the current project (`#9287 <https://github.com/readthedocs/readthedocs.org/pull/9287>`__)
* `@stsewd <https://github.com/stsewd>`__: Python: increase 3.11 beta version (`#9284 <https://github.com/readthedocs/readthedocs.org/pull/9284>`__)
* `@stsewd <https://github.com/stsewd>`__: Disable djstripe (`#9282 <https://github.com/readthedocs/readthedocs.org/pull/9282>`__)
* `@stsewd <https://github.com/stsewd>`__: Python: use 3.11.0b2 (`#9278 <https://github.com/readthedocs/readthedocs.org/pull/9278>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Remote repository: Add user admin action for syncing remote repositories (`#9272 <https://github.com/readthedocs/readthedocs.org/pull/9272>`__)
* `@stsewd <https://github.com/stsewd>`__: Requirements: update django-allauth (`#9249 <https://github.com/readthedocs/readthedocs.org/pull/9249>`__)
* `@humitos <https://github.com/humitos>`__: Build: implementation of `build.commands` (`#9150 <https://github.com/readthedocs/readthedocs.org/pull/9150>`__)

Version 8.1.1
-------------

:Date: Jun 1, 2022

* `@stsewd <https://github.com/stsewd>`__: Cancel build: get build from the current project (`#9287 <https://github.com/readthedocs/readthedocs.org/pull/9287>`__)
* `@stsewd <https://github.com/stsewd>`__: Disable djstripe (`#9282 <https://github.com/readthedocs/readthedocs.org/pull/9282>`__)
* `@stsewd <https://github.com/stsewd>`__: Python: increase 3.11 beta version (`#9284 <https://github.com/readthedocs/readthedocs.org/pull/9284>`__)
* `@stsewd <https://github.com/stsewd>`__: Python: use 3.11.0b2 (`#9278 <https://github.com/readthedocs/readthedocs.org/pull/9278>`__)
* `@yarons <https://github.com/yarons>`__: Typo fix (`#9271 <https://github.com/readthedocs/readthedocs.org/pull/9271>`__)
* `@stsewd <https://github.com/stsewd>`__: Update json schema (`#9270 <https://github.com/readthedocs/readthedocs.org/pull/9270>`__)
* `@stsewd <https://github.com/stsewd>`__: Build tools: update versions (`#9268 <https://github.com/readthedocs/readthedocs.org/pull/9268>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix docs (`#9264 <https://github.com/readthedocs/readthedocs.org/pull/9264>`__)
* `@stsewd <https://github.com/stsewd>`__: Update commmon (`#9248 <https://github.com/readthedocs/readthedocs.org/pull/9248>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 18 (`#9157 <https://github.com/readthedocs/readthedocs.org/pull/9157>`__)

Version 8.1.0
-------------

:Date: May 24, 2022

* `@humitos <https://github.com/humitos>`__: Assets: update `package-lock.json` with newer versions (`#9262 <https://github.com/readthedocs/readthedocs.org/pull/9262>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Improve contributing dev doc (`#9260 <https://github.com/readthedocs/readthedocs.org/pull/9260>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Update translations, pull from Transifex (`#9259 <https://github.com/readthedocs/readthedocs.org/pull/9259>`__)
* `@humitos <https://github.com/humitos>`__: Build: solve problem with sanitized output (`#9257 <https://github.com/readthedocs/readthedocs.org/pull/9257>`__)
* `@humitos <https://github.com/humitos>`__: Docs: improve "Environment Variables" page (`#9256 <https://github.com/readthedocs/readthedocs.org/pull/9256>`__)
* `@humitos <https://github.com/humitos>`__: Logging: reduce noise on working features (`#9255 <https://github.com/readthedocs/readthedocs.org/pull/9255>`__)
* `@humitos <https://github.com/humitos>`__: Docs: jsdoc example using `build.jobs` and `build.tools` (`#9241 <https://github.com/readthedocs/readthedocs.org/pull/9241>`__)
* `@stsewd <https://github.com/stsewd>`__: Docker environment: check for None on stdout/stderr response (`#9238 <https://github.com/readthedocs/readthedocs.org/pull/9238>`__)
* `@stsewd <https://github.com/stsewd>`__: Proxied static files: use its own storage class (`#9237 <https://github.com/readthedocs/readthedocs.org/pull/9237>`__)
* `@humitos <https://github.com/humitos>`__: Docs: gitlab integration update (`#9236 <https://github.com/readthedocs/readthedocs.org/pull/9236>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 8.0.2 (`#9234 <https://github.com/readthedocs/readthedocs.org/pull/9234>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix tests on .com (`#9233 <https://github.com/readthedocs/readthedocs.org/pull/9233>`__)
* `@humitos <https://github.com/humitos>`__: Development: only pull the images required (`#9182 <https://github.com/readthedocs/readthedocs.org/pull/9182>`__)
* `@stsewd <https://github.com/stsewd>`__: Proxito: serve static files from the same domain as the docs (`#9168 <https://github.com/readthedocs/readthedocs.org/pull/9168>`__)
* `@humitos <https://github.com/humitos>`__: Build: add a new "Cancelled" final state (`#9145 <https://github.com/readthedocs/readthedocs.org/pull/9145>`__)
* `@stsewd <https://github.com/stsewd>`__: Collect build data (`#9113 <https://github.com/readthedocs/readthedocs.org/pull/9113>`__)
* `@humitos <https://github.com/humitos>`__: Project: use `RemoteRepository` to define `default_branch` (`#8988 <https://github.com/readthedocs/readthedocs.org/pull/8988>`__)
* `@humitos <https://github.com/humitos>`__: Design doc: forward path to a future builder (`#8190 <https://github.com/readthedocs/readthedocs.org/pull/8190>`__)

Version 8.0.2
-------------

:Date: May 16, 2022

* `@stsewd <https://github.com/stsewd>`__: Fix tests on .com (`#9233 <https://github.com/readthedocs/readthedocs.org/pull/9233>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Disable codecov annotations (`#9186 <https://github.com/readthedocs/readthedocs.org/pull/9186>`__)
* `@choldgraf <https://github.com/choldgraf>`__: Note sub-folders with a single domain. (`#9185 <https://github.com/readthedocs/readthedocs.org/pull/9185>`__)
* `@stsewd <https://github.com/stsewd>`__: BuildCommand: add option to merge or not stderr with stdout (`#9184 <https://github.com/readthedocs/readthedocs.org/pull/9184>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Fix bumpver issue (`#9181 <https://github.com/readthedocs/readthedocs.org/pull/9181>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Release 8.0.1 (`#9180 <https://github.com/readthedocs/readthedocs.org/pull/9180>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Spruce up docs on pull request builds (`#9177 <https://github.com/readthedocs/readthedocs.org/pull/9177>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix RTD branding in the code (`#9175 <https://github.com/readthedocs/readthedocs.org/pull/9175>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Fix copy issues on model fields (`#9170 <https://github.com/readthedocs/readthedocs.org/pull/9170>`__)
* `@stsewd <https://github.com/stsewd>`__: Proxito: serve static files from the same domain as the docs (`#9168 <https://github.com/readthedocs/readthedocs.org/pull/9168>`__)
* `@stsewd <https://github.com/stsewd>`__: User: delete organizations where the user is the last owner (`#9164 <https://github.com/readthedocs/readthedocs.org/pull/9164>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add a basic djstripe integration (`#9087 <https://github.com/readthedocs/readthedocs.org/pull/9087>`__)
* `@stsewd <https://github.com/stsewd>`__: Custom domains: don't allow adding a custom domain on subprojects (`#8953 <https://github.com/readthedocs/readthedocs.org/pull/8953>`__)

Version 8.0.1
-------------

:Date: May 09, 2022

* `@ericholscher <https://github.com/ericholscher>`__: Fix RTD branding in the code (`#9175 <https://github.com/readthedocs/readthedocs.org/pull/9175>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Remove our old out-dated architecture diagram (`#9169 <https://github.com/readthedocs/readthedocs.org/pull/9169>`__)
* `@humitos <https://github.com/humitos>`__: Docs: mention `ubuntu-22.04` as a valid option (`#9166 <https://github.com/readthedocs/readthedocs.org/pull/9166>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Initial test of adding plan to CDN (`#9163 <https://github.com/readthedocs/readthedocs.org/pull/9163>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix links in docs from the build page refactor (`#9162 <https://github.com/readthedocs/readthedocs.org/pull/9162>`__)
* `@stsewd <https://github.com/stsewd>`__: Analytics: skip requests from bots on 404s (`#9161 <https://github.com/readthedocs/readthedocs.org/pull/9161>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Note build.jobs required other keys (`#9160 <https://github.com/readthedocs/readthedocs.org/pull/9160>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add docs showing pip-tools usage on dependencies (`#9158 <https://github.com/readthedocs/readthedocs.org/pull/9158>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Expierment with pip-tools for our docs.txt requirements (`#9124 <https://github.com/readthedocs/readthedocs.org/pull/9124>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add a basic djstripe integration (`#9087 <https://github.com/readthedocs/readthedocs.org/pull/9087>`__)

Version 8.0.0
-------------

:Date: May 03, 2022


.. note::

   We are upgrading to Ubuntu 22.04 LTS and also to Python 3.10.


Projects using Mamba with the old feature flag, and now removed, ``CONDA_USES_MAMBA``,
have to update their ``.readthedocs.yaml`` file to use ``build.tools.python: mambaforge-4.10``
to continue using Mamba to create their environment.
See more about ``build.tools.python`` at https://docs.readthedocs.io/en/stable/config-file/v2.html#build-tools-python

* `@stsewd <https://github.com/stsewd>`__: Search: fix parsing of footnotes (`#9154 <https://github.com/readthedocs/readthedocs.org/pull/9154>`__)
* `@humitos <https://github.com/humitos>`__: Mamba: remove CONDA_USES_MAMBA feature flag (`#9153 <https://github.com/readthedocs/readthedocs.org/pull/9153>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Remove prebuild step so docs keep working (`#9143 <https://github.com/readthedocs/readthedocs.org/pull/9143>`__)
* `@stsewd <https://github.com/stsewd>`__: lsremote: fix incorrect kwarg (`#9142 <https://github.com/readthedocs/readthedocs.org/pull/9142>`__)
* `@stsewd <https://github.com/stsewd>`__: Rebase of #9136 (`#9141 <https://github.com/readthedocs/readthedocs.org/pull/9141>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 7.6.2 (`#9140 <https://github.com/readthedocs/readthedocs.org/pull/9140>`__)
* `@humitos <https://github.com/humitos>`__: Docs: feature documentation for `build.jobs` (`#9138 <https://github.com/readthedocs/readthedocs.org/pull/9138>`__)
* `@stsewd <https://github.com/stsewd>`__: Builds: fix retry (`#9133 <https://github.com/readthedocs/readthedocs.org/pull/9133>`__)
* `@humitos <https://github.com/humitos>`__: External versions: save state (open / closed) (`#9128 <https://github.com/readthedocs/readthedocs.org/pull/9128>`__)
* `@stsewd <https://github.com/stsewd>`__: Resolver: allow to ignore custom domains (`#9089 <https://github.com/readthedocs/readthedocs.org/pull/9089>`__)
* `@humitos <https://github.com/humitos>`__: Update project to use Ubuntu 22.04 LTS (`#9010 <https://github.com/readthedocs/readthedocs.org/pull/9010>`__)
* `@OriolAbril <https://github.com/OriolAbril>`__: add note on setting locale_dirs (`#8972 <https://github.com/readthedocs/readthedocs.org/pull/8972>`__)
* `@stsewd <https://github.com/stsewd>`__: Design doc: collect data about builds (`#8124 <https://github.com/readthedocs/readthedocs.org/pull/8124>`__)

Version 7.6.2
-------------

:Date: April 25, 2022

* `@stsewd <https://github.com/stsewd>`__: Builds: fix retry (`#9133 <https://github.com/readthedocs/readthedocs.org/pull/9133>`__)
* `@stsewd <https://github.com/stsewd>`__: Build: log more data (`#9132 <https://github.com/readthedocs/readthedocs.org/pull/9132>`__)
* `@stsewd <https://github.com/stsewd>`__: Analytics: add feature flag to skip tracking 404s (`#9131 <https://github.com/readthedocs/readthedocs.org/pull/9131>`__)
* `@humitos <https://github.com/humitos>`__: External versions: save state (open / closed) (`#9128 <https://github.com/readthedocs/readthedocs.org/pull/9128>`__)
* `@stsewd <https://github.com/stsewd>`__: Build: log more attributes (`#9127 <https://github.com/readthedocs/readthedocs.org/pull/9127>`__)
* `@stsewd <https://github.com/stsewd>`__: git: respect SKIP_SYNC_* flags when using lsremote (`#9125 <https://github.com/readthedocs/readthedocs.org/pull/9125>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Release 7.6.1 (`#9123 <https://github.com/readthedocs/readthedocs.org/pull/9123>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 16 (`#9121 <https://github.com/readthedocs/readthedocs.org/pull/9121>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix docs (`#9120 <https://github.com/readthedocs/readthedocs.org/pull/9120>`__)
* `@thomasrockhu-codecov <https://github.com/thomasrockhu-codecov>`__: ci: add informational Codecov status checks (`#9119 <https://github.com/readthedocs/readthedocs.org/pull/9119>`__)
* `@stsewd <https://github.com/stsewd>`__: Build: use gvisor for projects using build.jobs (`#9114 <https://github.com/readthedocs/readthedocs.org/pull/9114>`__)
* `@humitos <https://github.com/humitos>`__: Docs: call `linkcheck` Sphinx builder for our docs (`#9091 <https://github.com/readthedocs/readthedocs.org/pull/9091>`__)

Version 7.6.1
-------------

:Date: April 19, 2022

* `@humitos <https://github.com/humitos>`__: Logging: reduce verbosity (`#9107 <https://github.com/readthedocs/readthedocs.org/pull/9107>`__)
* `@stsewd <https://github.com/stsewd>`__: Analytics: Don't use full_path in get_or_create (`#9099 <https://github.com/readthedocs/readthedocs.org/pull/9099>`__)
* `@humitos <https://github.com/humitos>`__: Build: do not upload `build.tool` to production S3 (`#9098 <https://github.com/readthedocs/readthedocs.org/pull/9098>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Cleanup Redirects docs (`#9095 <https://github.com/readthedocs/readthedocs.org/pull/9095>`__)

Version 7.6.0
-------------

:Date: April 12, 2022

* `@stsewd <https://github.com/stsewd>`__: Celery: workaround fix for bug on retrying builds (`#9096 <https://github.com/readthedocs/readthedocs.org/pull/9096>`__)
* `@stsewd <https://github.com/stsewd>`__: CI: use circle api v2 to trigger builds (`#9094 <https://github.com/readthedocs/readthedocs.org/pull/9094>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Try to fix .com tests (`#9092 <https://github.com/readthedocs/readthedocs.org/pull/9092>`__)
* `@humitos <https://github.com/humitos>`__: Notification: don't send it on build retry (`#9086 <https://github.com/readthedocs/readthedocs.org/pull/9086>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: add notes about gvisor on Fedora (`#9085 <https://github.com/readthedocs/readthedocs.org/pull/9085>`__)
* `@stsewd <https://github.com/stsewd>`__: Update common (`#9084 <https://github.com/readthedocs/readthedocs.org/pull/9084>`__)
* `@humitos <https://github.com/humitos>`__: Build: bugfix `RepositoryError.CLONE_ERROR` message (`#9083 <https://github.com/readthedocs/readthedocs.org/pull/9083>`__)
* `@stsewd <https://github.com/stsewd>`__: Redirects: remove unused code (`#9080 <https://github.com/readthedocs/readthedocs.org/pull/9080>`__)
* `@stsewd <https://github.com/stsewd>`__: Proxito: only check for index files if there is a version (`#9079 <https://github.com/readthedocs/readthedocs.org/pull/9079>`__)
* `@stsewd <https://github.com/stsewd>`__: Adapt scripts and docs to make use of the new github personal tokens (`#9078 <https://github.com/readthedocs/readthedocs.org/pull/9078>`__)
* `@stsewd <https://github.com/stsewd>`__: Redirects: avoid using re.sub (`#9077 <https://github.com/readthedocs/readthedocs.org/pull/9077>`__)
* `@stsewd <https://github.com/stsewd>`__: Proxito: fix URL parsing (`#9075 <https://github.com/readthedocs/readthedocs.org/pull/9075>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 7.5.1 (`#9074 <https://github.com/readthedocs/readthedocs.org/pull/9074>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 14 (`#9073 <https://github.com/readthedocs/readthedocs.org/pull/9073>`__)
* `@humitos <https://github.com/humitos>`__: Github: use probot auto-assign bot (`#9069 <https://github.com/readthedocs/readthedocs.org/pull/9069>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Add gVisor runtime option for build containers (`#9066 <https://github.com/readthedocs/readthedocs.org/pull/9066>`__)
* `@humitos <https://github.com/humitos>`__: Docs: `build.jobs` reference documentation (`#9056 <https://github.com/readthedocs/readthedocs.org/pull/9056>`__)
* `@humitos <https://github.com/humitos>`__: Proxito: do not serve non-existent versions (`#9048 <https://github.com/readthedocs/readthedocs.org/pull/9048>`__)
* `@stsewd <https://github.com/stsewd>`__: Traffic analytics: track 404s (`#9027 <https://github.com/readthedocs/readthedocs.org/pull/9027>`__)
* `@humitos <https://github.com/humitos>`__: SyncRepositoryTask: rate limit to 1 per minute per project (`#9021 <https://github.com/readthedocs/readthedocs.org/pull/9021>`__)
* `@stsewd <https://github.com/stsewd>`__: Sync versions: filter by type on update (`#9019 <https://github.com/readthedocs/readthedocs.org/pull/9019>`__)
* `@humitos <https://github.com/humitos>`__: Build: implement `build.jobs` config file key (`#9016 <https://github.com/readthedocs/readthedocs.org/pull/9016>`__)

Version 7.5.1
-------------

:Date: April 04, 2022

* `@humitos <https://github.com/humitos>`__: Github: use probot auto-assign bot (`#9069 <https://github.com/readthedocs/readthedocs.org/pull/9069>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: update sphinx-tabs (`#9061 <https://github.com/readthedocs/readthedocs.org/pull/9061>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: use sphinx-multiproject (`#9057 <https://github.com/readthedocs/readthedocs.org/pull/9057>`__)
* `@humitos <https://github.com/humitos>`__: Docs: `build.jobs` reference documentation (`#9056 <https://github.com/readthedocs/readthedocs.org/pull/9056>`__)
* `@humitos <https://github.com/humitos>`__: Build: use same hack for VCS and build environments (`#9055 <https://github.com/readthedocs/readthedocs.org/pull/9055>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix jinja2 on embed tests (`#9053 <https://github.com/readthedocs/readthedocs.org/pull/9053>`__)
* `@jsquyres <https://github.com/jsquyres>`__: director.py: restore READTHEDOCS_VERSION_[TYPE|NAME] (`#9052 <https://github.com/readthedocs/readthedocs.org/pull/9052>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix tests around jinja2 (`#9050 <https://github.com/readthedocs/readthedocs.org/pull/9050>`__)
* `@humitos <https://github.com/humitos>`__: Build: do not send VCS build status on specific exceptions (`#9049 <https://github.com/readthedocs/readthedocs.org/pull/9049>`__)
* `@humitos <https://github.com/humitos>`__: Proxito: do not serve non-existent versions (`#9048 <https://github.com/readthedocs/readthedocs.org/pull/9048>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Release 7.5.0 (`#9047 <https://github.com/readthedocs/readthedocs.org/pull/9047>`__)
* `@humitos <https://github.com/humitos>`__: Build: Mercurial (`hg`) compatibility with old versions (`#9042 <https://github.com/readthedocs/readthedocs.org/pull/9042>`__)
* `@eyllanesc <https://github.com/eyllanesc>`__: Fixes link (`#9041 <https://github.com/readthedocs/readthedocs.org/pull/9041>`__)
* `@ericholscher <https://github.com/ericholscher>`__:     Fix jinja2 pinning on Sphinx 1.8 feature flagged projects (`#9036 <https://github.com/readthedocs/readthedocs.org/pull/9036>`__)
* `@humitos <https://github.com/humitos>`__: Copyright date (`#9022 <https://github.com/readthedocs/readthedocs.org/pull/9022>`__)
* `@humitos <https://github.com/humitos>`__: SyncRepositoryTask: rate limit to 1 per minute per project (`#9021 <https://github.com/readthedocs/readthedocs.org/pull/9021>`__)
* `@humitos <https://github.com/humitos>`__: Build: use same build environment for setup and build (`#9018 <https://github.com/readthedocs/readthedocs.org/pull/9018>`__)
* `@stsewd <https://github.com/stsewd>`__: Git: fix annotated tags on lsremote (`#9017 <https://github.com/readthedocs/readthedocs.org/pull/9017>`__)
* `@humitos <https://github.com/humitos>`__: Build: implement `build.jobs` config file key (`#9016 <https://github.com/readthedocs/readthedocs.org/pull/9016>`__)
* `@abravalheri <https://github.com/abravalheri>`__: Improve displayed version name when building from PR (`#8237 <https://github.com/readthedocs/readthedocs.org/pull/8237>`__)

Version 7.5.0
-------------

:Date: March 28, 2022

* `@humitos <https://github.com/humitos>`__: Build: Mercurial (`hg`) compatibility with old versions (`#9042 <https://github.com/readthedocs/readthedocs.org/pull/9042>`__)
* `@eyllanesc <https://github.com/eyllanesc>`__: Fixes link (`#9041 <https://github.com/readthedocs/readthedocs.org/pull/9041>`__)
* `@ericholscher <https://github.com/ericholscher>`__:     Fix jinja2 pinning on Sphinx 1.8 feature flagged projects (`#9036 <https://github.com/readthedocs/readthedocs.org/pull/9036>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Add bumpver configuration (`#9029 <https://github.com/readthedocs/readthedocs.org/pull/9029>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Update the community ads application link (`#9028 <https://github.com/readthedocs/readthedocs.org/pull/9028>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Don't use master branch explicitly in requirements (`#9025 <https://github.com/readthedocs/readthedocs.org/pull/9025>`__)
* `@humitos <https://github.com/humitos>`__: Copyright date (`#9022 <https://github.com/readthedocs/readthedocs.org/pull/9022>`__)
* `@humitos <https://github.com/humitos>`__: GitHub OAuth: use bigger pages to make fewer requests (`#9020 <https://github.com/readthedocs/readthedocs.org/pull/9020>`__)
* `@humitos <https://github.com/humitos>`__: Build: use same build environment for setup and build (`#9018 <https://github.com/readthedocs/readthedocs.org/pull/9018>`__)
* `@stsewd <https://github.com/stsewd>`__: Git: fix annotated tags on lsremote (`#9017 <https://github.com/readthedocs/readthedocs.org/pull/9017>`__)
* `@humitos <https://github.com/humitos>`__: Build: log when a build is reset (`#9015 <https://github.com/readthedocs/readthedocs.org/pull/9015>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 11 (`#9012 <https://github.com/readthedocs/readthedocs.org/pull/9012>`__)
* `@humitos <https://github.com/humitos>`__: Build: allow users to use Ubuntu 22.04 LTS (`#9009 <https://github.com/readthedocs/readthedocs.org/pull/9009>`__)
* `@humitos <https://github.com/humitos>`__: Build: proof of concept for pre/post build commands (`build.jobs`) (`#9002 <https://github.com/readthedocs/readthedocs.org/pull/9002>`__)

Version 7.4.2
-------------

:Date: March 14, 2022

* `@stsewd <https://github.com/stsewd>`__: CI: fix codecov again (`#9007 <https://github.com/readthedocs/readthedocs.org/pull/9007>`__)
* `@stsewd <https://github.com/stsewd>`__: CI: fix codecov (`#9006 <https://github.com/readthedocs/readthedocs.org/pull/9006>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Release 7.4.1 (`#9004 <https://github.com/readthedocs/readthedocs.org/pull/9004>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 10 (`#9003 <https://github.com/readthedocs/readthedocs.org/pull/9003>`__)
* `@humitos <https://github.com/humitos>`__: Upgrade common submodule (`#9001 <https://github.com/readthedocs/readthedocs.org/pull/9001>`__)
* `@humitos <https://github.com/humitos>`__: Build: `RepositoryError` message (`#8999 <https://github.com/readthedocs/readthedocs.org/pull/8999>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: fix integration with latest sphinx (`#8994 <https://github.com/readthedocs/readthedocs.org/pull/8994>`__)
* `@humitos <https://github.com/humitos>`__: API: validate `RemoteRepository` when creating a `Project` (`#8983 <https://github.com/readthedocs/readthedocs.org/pull/8983>`__)
* `@stsewd <https://github.com/stsewd>`__: Tests: fix mock.patch order (`#8909 <https://github.com/readthedocs/readthedocs.org/pull/8909>`__)
* `@humitos <https://github.com/humitos>`__: Celery: remove queue priority (`#8848 <https://github.com/readthedocs/readthedocs.org/pull/8848>`__)
* `@dogukanteber <https://github.com/dogukanteber>`__: Use django-storages' manifest files class instead of the overriden class (`#8781 <https://github.com/readthedocs/readthedocs.org/pull/8781>`__)
* `@abravalheri <https://github.com/abravalheri>`__: Improve displayed version name when building from PR (`#8237 <https://github.com/readthedocs/readthedocs.org/pull/8237>`__)

Version 7.4.1
-------------

:Date: March 07, 2022

* `@humitos <https://github.com/humitos>`__: Upgrade common submodule (`#9001 <https://github.com/readthedocs/readthedocs.org/pull/9001>`__)
* `@humitos <https://github.com/humitos>`__: Build: `RepositoryError` message (`#8999 <https://github.com/readthedocs/readthedocs.org/pull/8999>`__)
* `@humitos <https://github.com/humitos>`__: Requirements: remove `django-permissions-policy` (`#8987 <https://github.com/readthedocs/readthedocs.org/pull/8987>`__)
* `@stsewd <https://github.com/stsewd>`__: Archive builds: avoid filtering by commands__isnull (`#8986 <https://github.com/readthedocs/readthedocs.org/pull/8986>`__)
* `@humitos <https://github.com/humitos>`__: Build: cancel error message (`#8984 <https://github.com/readthedocs/readthedocs.org/pull/8984>`__)
* `@humitos <https://github.com/humitos>`__: API: validate `RemoteRepository` when creating a `Project` (`#8983 <https://github.com/readthedocs/readthedocs.org/pull/8983>`__)
* `@humitos <https://github.com/humitos>`__: Celery: trigger `archive_builds` frequently with a lower limit (`#8981 <https://github.com/readthedocs/readthedocs.org/pull/8981>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 09 (`#8977 <https://github.com/readthedocs/readthedocs.org/pull/8977>`__)
* `@stsewd <https://github.com/stsewd>`__: MkDocs: allow None on extra_css/extra_javascript (`#8976 <https://github.com/readthedocs/readthedocs.org/pull/8976>`__)
* `@stsewd <https://github.com/stsewd>`__: CDN: avoid cache tags collision (`#8969 <https://github.com/readthedocs/readthedocs.org/pull/8969>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: warn about custom domains on subprojects (`#8945 <https://github.com/readthedocs/readthedocs.org/pull/8945>`__)
* `@humitos <https://github.com/humitos>`__: Code style: format the code using `darker` (`#8875 <https://github.com/readthedocs/readthedocs.org/pull/8875>`__)
* `@dogukanteber <https://github.com/dogukanteber>`__: Use django-storages' manifest files class instead of the overriden class (`#8781 <https://github.com/readthedocs/readthedocs.org/pull/8781>`__)
* `@nienn <https://github.com/nienn>`__: Docs: Add links to documentation on creating custom classes (`#8466 <https://github.com/readthedocs/readthedocs.org/pull/8466>`__)
* `@stsewd <https://github.com/stsewd>`__: Integrations: allow to pass more data about external versions (`#7692 <https://github.com/readthedocs/readthedocs.org/pull/7692>`__)

Version 7.4.0
-------------

:Date: March 01, 2022

* `@stsewd <https://github.com/stsewd>`__: Fix typo on exception (`#8975 <https://github.com/readthedocs/readthedocs.org/pull/8975>`__)
* `@humitos <https://github.com/humitos>`__: Celery: increase timeout limit for `sync_remote_repositories` task (`#8974 <https://github.com/readthedocs/readthedocs.org/pull/8974>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Fix a couple integration admin bugs (`#8964 <https://github.com/readthedocs/readthedocs.org/pull/8964>`__)
* `@humitos <https://github.com/humitos>`__: Build: allow NULL when updating the config (`#8962 <https://github.com/readthedocs/readthedocs.org/pull/8962>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Release 7.3.0 (`#8957 <https://github.com/readthedocs/readthedocs.org/pull/8957>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 08 (`#8954 <https://github.com/readthedocs/readthedocs.org/pull/8954>`__)
* `@humitos <https://github.com/humitos>`__: Celery: upgrade to latest version (`#8952 <https://github.com/readthedocs/readthedocs.org/pull/8952>`__)
* `@humitos <https://github.com/humitos>`__: Requirements: upgrade gitpython because of security issue (`#8950 <https://github.com/readthedocs/readthedocs.org/pull/8950>`__)
* `@humitos <https://github.com/humitos>`__: Test: remove verbose warnings (`#8949 <https://github.com/readthedocs/readthedocs.org/pull/8949>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Pin storages with boto3 (`#8947 <https://github.com/readthedocs/readthedocs.org/pull/8947>`__)
* `@stsewd <https://github.com/stsewd>`__: Optimize archive_builds task (`#8944 <https://github.com/readthedocs/readthedocs.org/pull/8944>`__)
* `@humitos <https://github.com/humitos>`__: Build: reset build error before start building (`#8943 <https://github.com/readthedocs/readthedocs.org/pull/8943>`__)
* `@humitos <https://github.com/humitos>`__: Build: comment `record=False` usage (`#8939 <https://github.com/readthedocs/readthedocs.org/pull/8939>`__)
* `@humitos <https://github.com/humitos>`__: Django3: use new JSON fields instead of old TextFields (`#8934 <https://github.com/readthedocs/readthedocs.org/pull/8934>`__)
* `@humitos <https://github.com/humitos>`__: Build: ability to cancel a running build from dashboard (`#8850 <https://github.com/readthedocs/readthedocs.org/pull/8850>`__)
* `@humitos <https://github.com/humitos>`__: Celery: remove queue priority (`#8848 <https://github.com/readthedocs/readthedocs.org/pull/8848>`__)

Version 7.3.0
-------------

:Date: February 21, 2022

* `@humitos <https://github.com/humitos>`__: Requirements: upgrade gitpython because of security issue (`#8950 <https://github.com/readthedocs/readthedocs.org/pull/8950>`__)
* `@humitos <https://github.com/humitos>`__: Test: remove verbose warnings (`#8949 <https://github.com/readthedocs/readthedocs.org/pull/8949>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Pin storages with boto3 (`#8947 <https://github.com/readthedocs/readthedocs.org/pull/8947>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix codeowners (`#8946 <https://github.com/readthedocs/readthedocs.org/pull/8946>`__)
* `@stsewd <https://github.com/stsewd>`__: Optimize archive_builds task (`#8944 <https://github.com/readthedocs/readthedocs.org/pull/8944>`__)
* `@humitos <https://github.com/humitos>`__: Build: reset build error before start building (`#8943 <https://github.com/readthedocs/readthedocs.org/pull/8943>`__)
* `@humitos <https://github.com/humitos>`__: Build: comment `record=False` usage (`#8939 <https://github.com/readthedocs/readthedocs.org/pull/8939>`__)
* `@humitos <https://github.com/humitos>`__: Django3: use new JSON fields instead of old TextFields (`#8934 <https://github.com/readthedocs/readthedocs.org/pull/8934>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Tune build config migration (`#8931 <https://github.com/readthedocs/readthedocs.org/pull/8931>`__)
* `@humitos <https://github.com/humitos>`__: Build: use `ubuntu-20.04` image for setup VCS step (`#8930 <https://github.com/readthedocs/readthedocs.org/pull/8930>`__)
* `@humitos <https://github.com/humitos>`__: Celery: remove duplication of task names (`#8929 <https://github.com/readthedocs/readthedocs.org/pull/8929>`__)
* `@humitos <https://github.com/humitos>`__: Sentry and Celery: do not log `RepositoryError` in Sentry (`#8928 <https://github.com/readthedocs/readthedocs.org/pull/8928>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add x-hoverxref-version to CORS (`#8927 <https://github.com/readthedocs/readthedocs.org/pull/8927>`__)
* `@humitos <https://github.com/humitos>`__: Deploy: avoid locking the table when adding new JSON field (`#8926 <https://github.com/readthedocs/readthedocs.org/pull/8926>`__)
* `@humitos <https://github.com/humitos>`__: Build: access valid arguments (`#8925 <https://github.com/readthedocs/readthedocs.org/pull/8925>`__)
* `@humitos <https://github.com/humitos>`__: Comment: add comment from PR review (`#8921 <https://github.com/readthedocs/readthedocs.org/pull/8921>`__)
* `@stsewd <https://github.com/stsewd>`__: Move subscription tasks (`#8916 <https://github.com/readthedocs/readthedocs.org/pull/8916>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 07 (`#8915 <https://github.com/readthedocs/readthedocs.org/pull/8915>`__)
* `@stsewd <https://github.com/stsewd>`__: Proxito: add top-level docs (`#8913 <https://github.com/readthedocs/readthedocs.org/pull/8913>`__)
* `@humitos <https://github.com/humitos>`__: Celery: remove queue priority (`#8848 <https://github.com/readthedocs/readthedocs.org/pull/8848>`__)

Version 7.2.1
-------------

:Date: February 15, 2022

* `@humitos <https://github.com/humitos>`__: Sentry: ignore logging known exceptions (`#8919 <https://github.com/readthedocs/readthedocs.org/pull/8919>`__)
* `@humitos <https://github.com/humitos>`__: Build: do not send notifications on known failed builds (`#8918 <https://github.com/readthedocs/readthedocs.org/pull/8918>`__)
* `@humitos <https://github.com/humitos>`__: Celery: use `on_retry` to handle `BuildMaxConcurrencyError` (`#8917 <https://github.com/readthedocs/readthedocs.org/pull/8917>`__)
* `@lkeegan <https://github.com/lkeegan>`__: typo fix (`#8911 <https://github.com/readthedocs/readthedocs.org/pull/8911>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix tests (`#8908 <https://github.com/readthedocs/readthedocs.org/pull/8908>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Throw an exception from Celery retry() (`#8905 <https://github.com/readthedocs/readthedocs.org/pull/8905>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Reduce verbose logging on generic command failure (`#8904 <https://github.com/readthedocs/readthedocs.org/pull/8904>`__)
* `@humitos <https://github.com/humitos>`__: Build: define missing variable (`#8903 <https://github.com/readthedocs/readthedocs.org/pull/8903>`__)
* `@humitos <https://github.com/humitos>`__: Search: call apply_async to fix the issue (`#8900 <https://github.com/readthedocs/readthedocs.org/pull/8900>`__)
* `@humitos <https://github.com/humitos>`__: Build: allow to not record commands on sync_repository_task (`#8899 <https://github.com/readthedocs/readthedocs.org/pull/8899>`__)
* `@humitos <https://github.com/humitos>`__: Release 7.2.0 (`#8898 <https://github.com/readthedocs/readthedocs.org/pull/8898>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix linter (`#8897 <https://github.com/readthedocs/readthedocs.org/pull/8897>`__)
* `@stsewd <https://github.com/stsewd>`__: Support for CDN when privacy levels are enabled (`#8896 <https://github.com/readthedocs/readthedocs.org/pull/8896>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Don't be so excited always in our emails :) (`#8888 <https://github.com/readthedocs/readthedocs.org/pull/8888>`__)
* `@humitos <https://github.com/humitos>`__: Docs: reduce visibility of Config File V1 (`#8887 <https://github.com/readthedocs/readthedocs.org/pull/8887>`__)
* `@humitos <https://github.com/humitos>`__: Builder: unpin pip (`#8886 <https://github.com/readthedocs/readthedocs.org/pull/8886>`__)
* `@stsewd <https://github.com/stsewd>`__: Dependencies: remove unused packages (`#8881 <https://github.com/readthedocs/readthedocs.org/pull/8881>`__)
* `@stsewd <https://github.com/stsewd>`__: Subscriptions: move some querysets (`#8876 <https://github.com/readthedocs/readthedocs.org/pull/8876>`__)
* `@humitos <https://github.com/humitos>`__: Django3: delete old JSONField and use the new ones (`#8869 <https://github.com/readthedocs/readthedocs.org/pull/8869>`__)
* `@humitos <https://github.com/humitos>`__: Django3: add new `django.db.models.JSONField` (`#8868 <https://github.com/readthedocs/readthedocs.org/pull/8868>`__)

Version 7.2.0
-------------

:Date: February 08, 2022

* `@stsewd <https://github.com/stsewd>`__: Fix linter (`#8897 <https://github.com/readthedocs/readthedocs.org/pull/8897>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Don't be so excited always in our emails :) (`#8888 <https://github.com/readthedocs/readthedocs.org/pull/8888>`__)
* `@stsewd <https://github.com/stsewd>`__: CI: Don't install debug tools when running tests (`#8882 <https://github.com/readthedocs/readthedocs.org/pull/8882>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Fix issue with build task routing and config argument (`#8877 <https://github.com/readthedocs/readthedocs.org/pull/8877>`__)
* `@humitos <https://github.com/humitos>`__: Celery: use an internal namespace to store build task's data (`#8874 <https://github.com/readthedocs/readthedocs.org/pull/8874>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Release 7.1.2 (`#8873 <https://github.com/readthedocs/readthedocs.org/pull/8873>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Release 7.1.1 (`#8872 <https://github.com/readthedocs/readthedocs.org/pull/8872>`__)
* `@humitos <https://github.com/humitos>`__: Build: pin pip as workaround (`#8865 <https://github.com/readthedocs/readthedocs.org/pull/8865>`__)
* `@humitos <https://github.com/humitos>`__: Logging: reduce verbosity (`#8856 <https://github.com/readthedocs/readthedocs.org/pull/8856>`__)
* `@humitos <https://github.com/humitos>`__: Task router: check new config `build.tools.python` for conda (`#8855 <https://github.com/readthedocs/readthedocs.org/pull/8855>`__)
* `@humitos <https://github.com/humitos>`__: Logging: reduce logs in task router (`#8854 <https://github.com/readthedocs/readthedocs.org/pull/8854>`__)
* `@humitos <https://github.com/humitos>`__: Build process: use Celery handlers (`#8815 <https://github.com/readthedocs/readthedocs.org/pull/8815>`__)

Version 7.1.2
-------------

:Date: January 31, 2022

* `@humitos <https://github.com/humitos>`__: Build: pin pip as workaround (`#8865 <https://github.com/readthedocs/readthedocs.org/pull/8865>`__)

Version 7.1.1
-------------

:Date: January 31, 2022

* `@humitos <https://github.com/humitos>`__: Task router: check new config `build.tools.python` for conda (`#8855 <https://github.com/readthedocs/readthedocs.org/pull/8855>`__)
* `@humitos <https://github.com/humitos>`__: Logging: reduce logs in task router (`#8854 <https://github.com/readthedocs/readthedocs.org/pull/8854>`__)
* `@humitos <https://github.com/humitos>`__: django-storages: upgrade (`#8853 <https://github.com/readthedocs/readthedocs.org/pull/8853>`__)
* `@humitos <https://github.com/humitos>`__: Config: remove pipfile from schema (`#8851 <https://github.com/readthedocs/readthedocs.org/pull/8851>`__)
* `@stsewd <https://github.com/stsewd>`__: AuditLog: always fill organization id & slug (`#8846 <https://github.com/readthedocs/readthedocs.org/pull/8846>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs (dev): fix server side search (`#8845 <https://github.com/readthedocs/readthedocs.org/pull/8845>`__)
* `@humitos <https://github.com/humitos>`__: Docs: remove beta warning from config file's `build` key (`#8843 <https://github.com/readthedocs/readthedocs.org/pull/8843>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Fix more casing issues (`#8842 <https://github.com/readthedocs/readthedocs.org/pull/8842>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Update choosing a platform doc (`#8837 <https://github.com/readthedocs/readthedocs.org/pull/8837>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 04 (`#8835 <https://github.com/readthedocs/readthedocs.org/pull/8835>`__)
* `@humitos <https://github.com/humitos>`__: Django3: use `BooleanField(null=True)` (`#8834 <https://github.com/readthedocs/readthedocs.org/pull/8834>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: fix edit on links (`#8833 <https://github.com/readthedocs/readthedocs.org/pull/8833>`__)

Version 7.1.0
-------------

:Date: January 25, 2022

* `@astrojuanlu <https://github.com/astrojuanlu>`__: Detail what URLs are expected in issue template (`#8832 <https://github.com/readthedocs/readthedocs.org/pull/8832>`__)
* `@humitos <https://github.com/humitos>`__: Cleanup: delete unused Django management commands (`#8830 <https://github.com/readthedocs/readthedocs.org/pull/8830>`__)
* `@simonw <https://github.com/simonw>`__: Canonical can point as stable, not just latest (`#8828 <https://github.com/readthedocs/readthedocs.org/pull/8828>`__)
* `@humitos <https://github.com/humitos>`__: Docs: remove `USE_TESTING_BUILD_IMAGE` (`#8824 <https://github.com/readthedocs/readthedocs.org/pull/8824>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Use stickybox ad placement on RTD themed projects (`#8823 <https://github.com/readthedocs/readthedocs.org/pull/8823>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Quiet the Unresolver logging (`#8822 <https://github.com/readthedocs/readthedocs.org/pull/8822>`__)
* `@stsewd <https://github.com/stsewd>`__: Workaround for HttpExchange queries casting IDs as uuid/int wrongly (`#8821 <https://github.com/readthedocs/readthedocs.org/pull/8821>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix queryset for generic models (`#8820 <https://github.com/readthedocs/readthedocs.org/pull/8820>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 7.0.0 (`#8818 <https://github.com/readthedocs/readthedocs.org/pull/8818>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 03 (`#8817 <https://github.com/readthedocs/readthedocs.org/pull/8817>`__)
* `@stsewd <https://github.com/stsewd>`__: Subscriptions: move views  (`#8816 <https://github.com/readthedocs/readthedocs.org/pull/8816>`__)

Version 7.0.0
-------------

This is our 7th major version! This is because we are upgrading to **Django 3.2 LTS**.

:Date: January 17, 2022

* `@stsewd <https://github.com/stsewd>`__: Subscriptions: move views  (`#8816 <https://github.com/readthedocs/readthedocs.org/pull/8816>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix docs (`#8808 <https://github.com/readthedocs/readthedocs.org/pull/8808>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Release 6.3.3 (`#8806 <https://github.com/readthedocs/readthedocs.org/pull/8806>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Fix linting issue on project private view (`#8805 <https://github.com/readthedocs/readthedocs.org/pull/8805>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 02 (`#8804 <https://github.com/readthedocs/readthedocs.org/pull/8804>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Remove explicit username from tutorial (`#8803 <https://github.com/readthedocs/readthedocs.org/pull/8803>`__)
* `@humitos <https://github.com/humitos>`__: Bitbucket: update to match latest API changes (`#8801 <https://github.com/readthedocs/readthedocs.org/pull/8801>`__)
* `@humitos <https://github.com/humitos>`__: Cleanup: remove old/outdated code (`#8793 <https://github.com/readthedocs/readthedocs.org/pull/8793>`__)
* `@stsewd <https://github.com/stsewd>`__: API v3: check if the name generates a valid slug (`#8791 <https://github.com/readthedocs/readthedocs.org/pull/8791>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Make commercial docs more visible (`#8780 <https://github.com/readthedocs/readthedocs.org/pull/8780>`__)
* `@stsewd <https://github.com/stsewd>`__: API v3: less overrides (`#8770 <https://github.com/readthedocs/readthedocs.org/pull/8770>`__)
* `@stsewd <https://github.com/stsewd>`__: Move subscription models (`#8746 <https://github.com/readthedocs/readthedocs.org/pull/8746>`__)
* `@humitos <https://github.com/humitos>`__: Django3: minimal upgrade to Django3 (`#8717 <https://github.com/readthedocs/readthedocs.org/pull/8717>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Make the analytics cookie a session cookie (`#8694 <https://github.com/readthedocs/readthedocs.org/pull/8694>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add ability to rebuild a specific build (`#6995 <https://github.com/readthedocs/readthedocs.org/pull/6995>`__)

Version 6.3.3
-------------

:Date: January 10, 2022

* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 02 (`#8804 <https://github.com/readthedocs/readthedocs.org/pull/8804>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Remove explicit username from tutorial (`#8803 <https://github.com/readthedocs/readthedocs.org/pull/8803>`__)
* `@humitos <https://github.com/humitos>`__: Bitbucket: update to match latest API changes (`#8801 <https://github.com/readthedocs/readthedocs.org/pull/8801>`__)
* `@humitos <https://github.com/humitos>`__: Requirements: downgrade celery (`#8796 <https://github.com/readthedocs/readthedocs.org/pull/8796>`__)
* `@humitos <https://github.com/humitos>`__: Requirements: downgrade redis to 3.5.3 (`#8795 <https://github.com/readthedocs/readthedocs.org/pull/8795>`__)
* `@humitos <https://github.com/humitos>`__: Cleanup: remove old/outdated code (`#8793 <https://github.com/readthedocs/readthedocs.org/pull/8793>`__)
* `@humitos <https://github.com/humitos>`__: Spam: deny dashboard on spammy projects (`#8792 <https://github.com/readthedocs/readthedocs.org/pull/8792>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Mention subproject aliases (`#8785 <https://github.com/readthedocs/readthedocs.org/pull/8785>`__)
* `@humitos <https://github.com/humitos>`__: Config file: system_site_packages overwritten from project's setting (`#8783 <https://github.com/readthedocs/readthedocs.org/pull/8783>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Make commercial docs more visible (`#8780 <https://github.com/readthedocs/readthedocs.org/pull/8780>`__)
* `@humitos <https://github.com/humitos>`__: Spam: allow to mark a project as (non)spam manually (`#8779 <https://github.com/readthedocs/readthedocs.org/pull/8779>`__)
* `@stsewd <https://github.com/stsewd>`__: API v3: less overrides (`#8770 <https://github.com/readthedocs/readthedocs.org/pull/8770>`__)
* `@stsewd <https://github.com/stsewd>`__: Move subscription models (`#8746 <https://github.com/readthedocs/readthedocs.org/pull/8746>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Make the analytics cookie a session cookie (`#8694 <https://github.com/readthedocs/readthedocs.org/pull/8694>`__)

Version 6.3.2
-------------

:Date: January 04, 2022

* `@cagatay-y <https://github.com/cagatay-y>`__: Fix broken link in edit-source-links-sphinx.rst (`#8788 <https://github.com/readthedocs/readthedocs.org/pull/8788>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 52 (`#8787 <https://github.com/readthedocs/readthedocs.org/pull/8787>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Cap setuptools even if installed packages are ignored (`#8777 <https://github.com/readthedocs/readthedocs.org/pull/8777>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 51 (`#8776 <https://github.com/readthedocs/readthedocs.org/pull/8776>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Follow up to dev docs split (`#8774 <https://github.com/readthedocs/readthedocs.org/pull/8774>`__)
* `@stsewd <https://github.com/stsewd>`__: API v3: improve message when using the API on the browser (`#8768 <https://github.com/readthedocs/readthedocs.org/pull/8768>`__)
* `@stsewd <https://github.com/stsewd>`__: API v3: don't include subproject_of on subprojects (`#8767 <https://github.com/readthedocs/readthedocs.org/pull/8767>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Use ad client stickybox feature on RTD's own docs (`#8766 <https://github.com/readthedocs/readthedocs.org/pull/8766>`__)
* `@stsewd <https://github.com/stsewd>`__: API v3: explicitly test with RTD_ALLOW_ORGANIZATIONS=False (`#8765 <https://github.com/readthedocs/readthedocs.org/pull/8765>`__)
* `@stsewd <https://github.com/stsewd>`__: Update tasks.py (`#8764 <https://github.com/readthedocs/readthedocs.org/pull/8764>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 6.3.1 (`#8763 <https://github.com/readthedocs/readthedocs.org/pull/8763>`__)
* `@humitos <https://github.com/humitos>`__: Update `common/` to latest version (`#8761 <https://github.com/readthedocs/readthedocs.org/pull/8761>`__)
* `@stsewd <https://github.com/stsewd>`__: Skip slug check when editing an organization (`#8760 <https://github.com/readthedocs/readthedocs.org/pull/8760>`__)
* `@stsewd <https://github.com/stsewd>`__: Explicit settings for some tests (`#8759 <https://github.com/readthedocs/readthedocs.org/pull/8759>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix EA branding in docs (`#8758 <https://github.com/readthedocs/readthedocs.org/pull/8758>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 50 (`#8757 <https://github.com/readthedocs/readthedocs.org/pull/8757>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Add MyST Markdown examples everywhere (`#8752 <https://github.com/readthedocs/readthedocs.org/pull/8752>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: split user and dev docs (`#8751 <https://github.com/readthedocs/readthedocs.org/pull/8751>`__)
* `@humitos <https://github.com/humitos>`__: Logging: tweaks and minor improvements (`#8736 <https://github.com/readthedocs/readthedocs.org/pull/8736>`__)
* `@stsewd <https://github.com/stsewd>`__: Audit: test models (`#8495 <https://github.com/readthedocs/readthedocs.org/pull/8495>`__)

Version 6.3.1
-------------

:Date: December 14, 2021

* `@stsewd <https://github.com/stsewd>`__: Explicit settings for some tests (`#8759 <https://github.com/readthedocs/readthedocs.org/pull/8759>`__)
* `@stsewd <https://github.com/stsewd>`__: Don't run spam rules check after ban action (`#8756 <https://github.com/readthedocs/readthedocs.org/pull/8756>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Add MyST Markdown examples everywhere (`#8752 <https://github.com/readthedocs/readthedocs.org/pull/8752>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Update mambaforge to latest version (`#8749 <https://github.com/readthedocs/readthedocs.org/pull/8749>`__)
* `@stsewd <https://github.com/stsewd>`__: Update django (`#8748 <https://github.com/readthedocs/readthedocs.org/pull/8748>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Remove sphinx-doc.org from external domains (`#8747 <https://github.com/readthedocs/readthedocs.org/pull/8747>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix call to sync_remote_repositories (`#8742 <https://github.com/readthedocs/readthedocs.org/pull/8742>`__)
* `@stsewd <https://github.com/stsewd>`__: Tests: set privacy level explicitly (`#8740 <https://github.com/readthedocs/readthedocs.org/pull/8740>`__)
* `@humitos <https://github.com/humitos>`__: Spam: contact link on template (`#8739 <https://github.com/readthedocs/readthedocs.org/pull/8739>`__)
* `@humitos <https://github.com/humitos>`__: Spam: fix admin filter (`#8738 <https://github.com/readthedocs/readthedocs.org/pull/8738>`__)
* `@stsewd <https://github.com/stsewd>`__: Always clear cache after each test (`#8737 <https://github.com/readthedocs/readthedocs.org/pull/8737>`__)
* `@humitos <https://github.com/humitos>`__: Logging: tweaks and minor improvements (`#8736 <https://github.com/readthedocs/readthedocs.org/pull/8736>`__)
* `@humitos <https://github.com/humitos>`__: Logs: typo on keyname (`#8734 <https://github.com/readthedocs/readthedocs.org/pull/8734>`__)
* `@humitos <https://github.com/humitos>`__: Log: use structlog-sentry to send logs to Sentry (`#8732 <https://github.com/readthedocs/readthedocs.org/pull/8732>`__)
* `@humitos <https://github.com/humitos>`__: docs: use Python 3.8 to build our docs (`#8731 <https://github.com/readthedocs/readthedocs.org/pull/8731>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Release 6.3.0 (`#8730 <https://github.com/readthedocs/readthedocs.org/pull/8730>`__)
* `@stsewd <https://github.com/stsewd>`__: Custom Domain: make cname_target configurable (`#8728 <https://github.com/readthedocs/readthedocs.org/pull/8728>`__)
* `@stsewd <https://github.com/stsewd>`__: Test external serving for projects with `--` in slug (`#8716 <https://github.com/readthedocs/readthedocs.org/pull/8716>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Add guide to migrate from reST to MyST (`#8714 <https://github.com/readthedocs/readthedocs.org/pull/8714>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Avoid future breakage of `setup.py` invokations (`#8711 <https://github.com/readthedocs/readthedocs.org/pull/8711>`__)
* `@humitos <https://github.com/humitos>`__: structlog: migrate application code to better logging (`#8705 <https://github.com/readthedocs/readthedocs.org/pull/8705>`__)
* `@humitos <https://github.com/humitos>`__: EmbedAPI: log success requests (`#8689 <https://github.com/readthedocs/readthedocs.org/pull/8689>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add ability to rebuild a specific build (`#6995 <https://github.com/readthedocs/readthedocs.org/pull/6995>`__)

Version 6.3.0
-------------

:Date: November 29, 2021

* `@humitos <https://github.com/humitos>`__: Tests: run tests with Python3.8 in CircleCI (`#8718 <https://github.com/readthedocs/readthedocs.org/pull/8718>`__)
* `@stsewd <https://github.com/stsewd>`__: Test external serving for projects with `--` in slug (`#8716 <https://github.com/readthedocs/readthedocs.org/pull/8716>`__)
* `@humitos <https://github.com/humitos>`__: requirements: add requests-oauthlib (`#8712 <https://github.com/readthedocs/readthedocs.org/pull/8712>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Avoid future breakage of `setup.py` invokations (`#8711 <https://github.com/readthedocs/readthedocs.org/pull/8711>`__)
* `@humitos <https://github.com/humitos>`__: spam: fix admin filter (`#8707 <https://github.com/readthedocs/readthedocs.org/pull/8707>`__)
* `@humitos <https://github.com/humitos>`__: oauth: sync remote repositories fix (`#8706 <https://github.com/readthedocs/readthedocs.org/pull/8706>`__)
* `@humitos <https://github.com/humitos>`__: structlog: migrate application code to better logging (`#8705 <https://github.com/readthedocs/readthedocs.org/pull/8705>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Add guide on Poetry (`#8702 <https://github.com/readthedocs/readthedocs.org/pull/8702>`__)
* `@humitos <https://github.com/humitos>`__: EmbedAPI: log success requests (`#8689 <https://github.com/readthedocs/readthedocs.org/pull/8689>`__)

Version 6.2.1
-------------

:Date: November 23, 2021

* `@agjohnson <https://github.com/agjohnson>`__: Fix issue with PR build hostname parsing (`#8700 <https://github.com/readthedocs/readthedocs.org/pull/8700>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix sharing titles (`#8695 <https://github.com/readthedocs/readthedocs.org/pull/8695>`__)
* `@stsewd <https://github.com/stsewd>`__: Downgrade celery and friends (`#8693 <https://github.com/readthedocs/readthedocs.org/pull/8693>`__)
* `@stsewd <https://github.com/stsewd>`__: Downgrade pyyaml (`#8691 <https://github.com/readthedocs/readthedocs.org/pull/8691>`__)
* `@stsewd <https://github.com/stsewd>`__: Downgrade redis (`#8690 <https://github.com/readthedocs/readthedocs.org/pull/8690>`__)
* `@humitos <https://github.com/humitos>`__: Spam: make admin filters easier to understand (`#8688 <https://github.com/readthedocs/readthedocs.org/pull/8688>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Clarify how to pin the Sphinx version (`#8687 <https://github.com/readthedocs/readthedocs.org/pull/8687>`__)
* `@stsewd <https://github.com/stsewd>`__: Webhooks: fix link to docs (`#8685 <https://github.com/readthedocs/readthedocs.org/pull/8685>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: update docs about search on subprojects (`#8683 <https://github.com/readthedocs/readthedocs.org/pull/8683>`__)
* `@stsewd <https://github.com/stsewd>`__: Update common (`#8681 <https://github.com/readthedocs/readthedocs.org/pull/8681>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 46 (`#8680 <https://github.com/readthedocs/readthedocs.org/pull/8680>`__)

Version 6.2.0
-------------

:Date: November 16, 2021

* `@rokroskar <https://github.com/rokroskar>`__: docs: update faq to mention apt for dependencies (`#8676 <https://github.com/readthedocs/readthedocs.org/pull/8676>`__)
* `@stsewd <https://github.com/stsewd>`__: UserProfile: add time fields (`#8675 <https://github.com/readthedocs/readthedocs.org/pull/8675>`__)
* `@stsewd <https://github.com/stsewd>`__: Admin: don't use update to ban users (`#8674 <https://github.com/readthedocs/readthedocs.org/pull/8674>`__)
* `@stsewd <https://github.com/stsewd>`__: UserProfile: add historical model (`#8673 <https://github.com/readthedocs/readthedocs.org/pull/8673>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Add entry on Jupyter Book to the FAQ (`#8669 <https://github.com/readthedocs/readthedocs.org/pull/8669>`__)
* `@stsewd <https://github.com/stsewd>`__: Proxito: add CDN-Cache-Control headers (`#8667 <https://github.com/readthedocs/readthedocs.org/pull/8667>`__)
* `@humitos <https://github.com/humitos>`__: Spam: sort admin filters and show threshold (`#8666 <https://github.com/readthedocs/readthedocs.org/pull/8666>`__)
* `@humitos <https://github.com/humitos>`__: Cleanup: remove old code (`#8665 <https://github.com/readthedocs/readthedocs.org/pull/8665>`__)
* `@humitos <https://github.com/humitos>`__: Spam: check for spam rules after user is banned (`#8664 <https://github.com/readthedocs/readthedocs.org/pull/8664>`__)
* `@humitos <https://github.com/humitos>`__: Spam: use 410 - Gone status code when blocked (`#8661 <https://github.com/readthedocs/readthedocs.org/pull/8661>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Upgrade readthedocs-sphinx-search (`#8660 <https://github.com/readthedocs/readthedocs.org/pull/8660>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Release 6.1.2 (`#8657 <https://github.com/readthedocs/readthedocs.org/pull/8657>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Update requirements pinning (`#8655 <https://github.com/readthedocs/readthedocs.org/pull/8655>`__)
* `@stsewd <https://github.com/stsewd>`__: Historical records: set the change reason explicitly on the instance (`#8627 <https://github.com/readthedocs/readthedocs.org/pull/8627>`__)
* `@stsewd <https://github.com/stsewd>`__: Support for generic webhooks (`#8522 <https://github.com/readthedocs/readthedocs.org/pull/8522>`__)

Version 6.1.2
-------------

:Date: November 08, 2021

* `@astrojuanlu <https://github.com/astrojuanlu>`__: Update requirements pinning (`#8655 <https://github.com/readthedocs/readthedocs.org/pull/8655>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix GitHub permissions required (`#8654 <https://github.com/readthedocs/readthedocs.org/pull/8654>`__)
* `@stsewd <https://github.com/stsewd>`__: Organizations: allow to add owners by email (`#8651 <https://github.com/readthedocs/readthedocs.org/pull/8651>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 44 (`#8645 <https://github.com/readthedocs/readthedocs.org/pull/8645>`__)
* `@humitos <https://github.com/humitos>`__: Spam: use thresholds to decide actions (`#8632 <https://github.com/readthedocs/readthedocs.org/pull/8632>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Document generic webhooks (`#8609 <https://github.com/readthedocs/readthedocs.org/pull/8609>`__)
* `@stsewd <https://github.com/stsewd>`__: Organizations: show audit logs (`#8588 <https://github.com/readthedocs/readthedocs.org/pull/8588>`__)

Version 6.1.1
-------------

:Date: November 02, 2021

* `@agjohnson <https://github.com/agjohnson>`__: Drop beta from title of build config option (`#8637 <https://github.com/readthedocs/readthedocs.org/pull/8637>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Remove mentions to old Python version specification (`#8635 <https://github.com/readthedocs/readthedocs.org/pull/8635>`__)
* `@jugmac00 <https://github.com/jugmac00>`__: fix typos (`#8630 <https://github.com/readthedocs/readthedocs.org/pull/8630>`__)
* `@Arthur-Milchior <https://github.com/Arthur-Milchior>`__: Correct an example (`#8628 <https://github.com/readthedocs/readthedocs.org/pull/8628>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Inherit theme template (`#8626 <https://github.com/readthedocs/readthedocs.org/pull/8626>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Clarify duration of extra DNS records (`#8625 <https://github.com/readthedocs/readthedocs.org/pull/8625>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Promote mamba more in the documentation, hide `CONDA_USES_MAMBA` (`#8624 <https://github.com/readthedocs/readthedocs.org/pull/8624>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Floating ad placement for docs.readthedocs.io (`#8621 <https://github.com/readthedocs/readthedocs.org/pull/8621>`__)
* `@stsewd <https://github.com/stsewd>`__: Audit: track downloads separately from page views (`#8619 <https://github.com/readthedocs/readthedocs.org/pull/8619>`__)
* `@humitos <https://github.com/humitos>`__: Celery: quick hotfix to task (`#8617 <https://github.com/readthedocs/readthedocs.org/pull/8617>`__)

Version 6.1.0
-------------

:Date: October 26, 2021

* `@astrojuanlu <https://github.com/astrojuanlu>`__: Clarify docs (`#8608 <https://github.com/readthedocs/readthedocs.org/pull/8608>`__)
* `@stsewd <https://github.com/stsewd>`__: Move more organization tests (`#8606 <https://github.com/readthedocs/readthedocs.org/pull/8606>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: New Read the Docs tutorial, part III (and finale?) (`#8605 <https://github.com/readthedocs/readthedocs.org/pull/8605>`__)
* `@humitos <https://github.com/humitos>`__: SSO: re-sync VCS accounts for SSO organization daily (`#8601 <https://github.com/readthedocs/readthedocs.org/pull/8601>`__)
* `@humitos <https://github.com/humitos>`__: Django Action: re-sync SSO organization's users (`#8600 <https://github.com/readthedocs/readthedocs.org/pull/8600>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 42 (`#8598 <https://github.com/readthedocs/readthedocs.org/pull/8598>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Don't show the rebuild option on closed/merged Pull Request builds (`#8590 <https://github.com/readthedocs/readthedocs.org/pull/8590>`__)
* `@carltongibson <https://github.com/carltongibson>`__: Adjust Django intersphinx link to stable version. (`#8589 <https://github.com/readthedocs/readthedocs.org/pull/8589>`__)
* `@humitos <https://github.com/humitos>`__: Small fixes to asdf image upload script (`#8587 <https://github.com/readthedocs/readthedocs.org/pull/8587>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Documentation names cleanup (`#8586 <https://github.com/readthedocs/readthedocs.org/pull/8586>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix docs (`#8584 <https://github.com/readthedocs/readthedocs.org/pull/8584>`__)
* `@adamtheturtle <https://github.com/adamtheturtle>`__: Fix typo "interpreters" (`#8583 <https://github.com/readthedocs/readthedocs.org/pull/8583>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Small fixes to asdf image upload script (`#8578 <https://github.com/readthedocs/readthedocs.org/pull/8578>`__)
* `@stsewd <https://github.com/stsewd>`__: Move organization views (`#8577 <https://github.com/readthedocs/readthedocs.org/pull/8577>`__)
* `@humitos <https://github.com/humitos>`__: EmbedAPIv3: docs for endpoint and guide updated (`#8566 <https://github.com/readthedocs/readthedocs.org/pull/8566>`__)
* `@stsewd <https://github.com/stsewd>`__: GitLab integration: escape path (`#8525 <https://github.com/readthedocs/readthedocs.org/pull/8525>`__)
* `@stsewd <https://github.com/stsewd>`__: Domain: allow to disable domain creation/update (`#8020 <https://github.com/readthedocs/readthedocs.org/pull/8020>`__)

Version 6.0.0
-------------

:Date: October 13, 2021


This release includes the upgrade of some base dependencies:

- Python version from 3.6 to 3.8
- Ubuntu version from 18.04 LTS to 20.04 LTS

Starting from this release, all the Read the Docs code will be tested and QAed on these versions.

* `@ericholscher <https://github.com/ericholscher>`__: Release 5.25.1 (`#8576 <https://github.com/readthedocs/readthedocs.org/pull/8576>`__)
* `@deepto98 <https://github.com/deepto98>`__: Moved authenticated_classes definitions from API classes to AuthenticatedClassesMixin (`#8562 <https://github.com/readthedocs/readthedocs.org/pull/8562>`__)
* `@humitos <https://github.com/humitos>`__: Upgrade to Ubuntu 20.04 and Python 3.8 (`#7421 <https://github.com/readthedocs/readthedocs.org/pull/7421>`__)

Version 5.25.1
--------------

:Date: October 11, 2021

* `@astrojuanlu <https://github.com/astrojuanlu>`__: Small fixes (`#8564 <https://github.com/readthedocs/readthedocs.org/pull/8564>`__)
* `@deepto98 <https://github.com/deepto98>`__: Moved authenticated_classes definitions from API classes to AuthenticatedClassesMixin (`#8562 <https://github.com/readthedocs/readthedocs.org/pull/8562>`__)
* `@humitos <https://github.com/humitos>`__: Build: update ca-certificates before cloning (`#8559 <https://github.com/readthedocs/readthedocs.org/pull/8559>`__)
* `@humitos <https://github.com/humitos>`__: Build: support Python 3.10.0 stable release (`#8558 <https://github.com/readthedocs/readthedocs.org/pull/8558>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Document new `build` specification (`#8547 <https://github.com/readthedocs/readthedocs.org/pull/8547>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Add checkbox to subscribe new users to newsletter (`#8546 <https://github.com/readthedocs/readthedocs.org/pull/8546>`__)

Version 5.25.0
--------------

:Date: October 05, 2021

* `@humitos <https://github.com/humitos>`__: Docs: comment about how to add a new tool/version for builders (`#8548 <https://github.com/readthedocs/readthedocs.org/pull/8548>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Add checkbox to subscribe new users to newsletter (`#8546 <https://github.com/readthedocs/readthedocs.org/pull/8546>`__)
* `@humitos <https://github.com/humitos>`__: Build: missing updates from review (`#8544 <https://github.com/readthedocs/readthedocs.org/pull/8544>`__)
* `@humitos <https://github.com/humitos>`__: EmbedAPI: allow CORS for `/api/v3/embed/` (`#8543 <https://github.com/readthedocs/readthedocs.org/pull/8543>`__)
* `@humitos <https://github.com/humitos>`__: Script tools cache: fix environment variables (`#8541 <https://github.com/readthedocs/readthedocs.org/pull/8541>`__)
* `@humitos <https://github.com/humitos>`__: EmbedAPIv3: proxy URLs to be available under `/_/` (`#8540 <https://github.com/readthedocs/readthedocs.org/pull/8540>`__)
* `@humitos <https://github.com/humitos>`__: Docker: use the correct image tag (`#8539 <https://github.com/readthedocs/readthedocs.org/pull/8539>`__)
* `@humitos <https://github.com/humitos>`__: Requirement: ping django-redis-cache to git tag (`#8536 <https://github.com/readthedocs/readthedocs.org/pull/8536>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 39 (`#8531 <https://github.com/readthedocs/readthedocs.org/pull/8531>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Promote and restructure guides (`#8528 <https://github.com/readthedocs/readthedocs.org/pull/8528>`__)
* `@stsewd <https://github.com/stsewd>`__: Analytics: allow to download all data (`#8498 <https://github.com/readthedocs/readthedocs.org/pull/8498>`__)
* `@stsewd <https://github.com/stsewd>`__: HistoricalRecords: add additional fields (ip and browser) (`#8490 <https://github.com/readthedocs/readthedocs.org/pull/8490>`__)

Version 5.24.0
--------------

:Date: September 28, 2021

* `@humitos <https://github.com/humitos>`__: EmbedAPIv3: updates after QA with sphinx-hoverxref (`#8521 <https://github.com/readthedocs/readthedocs.org/pull/8521>`__)
* `@stsewd <https://github.com/stsewd>`__: Contact users: show progress (`#8518 <https://github.com/readthedocs/readthedocs.org/pull/8518>`__)
* `@stsewd <https://github.com/stsewd>`__: Rename audit retention days setting (`#8517 <https://github.com/readthedocs/readthedocs.org/pull/8517>`__)
* `@stsewd <https://github.com/stsewd>`__: Contact users: make notification sticky (`#8516 <https://github.com/readthedocs/readthedocs.org/pull/8516>`__)
* `@stsewd <https://github.com/stsewd>`__: Contact users: report usernames instead of PK (`#8515 <https://github.com/readthedocs/readthedocs.org/pull/8515>`__)
* `@stsewd <https://github.com/stsewd>`__: Audit: update admin (`#8514 <https://github.com/readthedocs/readthedocs.org/pull/8514>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 38 (`#8510 <https://github.com/readthedocs/readthedocs.org/pull/8510>`__)
* `@stsewd <https://github.com/stsewd>`__: New config for new docker build images (`#8478 <https://github.com/readthedocs/readthedocs.org/pull/8478>`__)
* `@stsewd <https://github.com/stsewd>`__: Audit: expose user security logs (`#8477 <https://github.com/readthedocs/readthedocs.org/pull/8477>`__)
* `@humitos <https://github.com/humitos>`__: Build: use new Docker images from design document (`#8453 <https://github.com/readthedocs/readthedocs.org/pull/8453>`__)
* `@humitos <https://github.com/humitos>`__: Embed APIv3: initial implementation (`#8319 <https://github.com/readthedocs/readthedocs.org/pull/8319>`__)

Version 5.23.6
--------------

:Date: September 20, 2021

* `@astrojuanlu <https://github.com/astrojuanlu>`__: Change newsletter form (`#8509 <https://github.com/readthedocs/readthedocs.org/pull/8509>`__)
* `@stsewd <https://github.com/stsewd>`__: Contact users: Allow to pass additional context to each email (`#8507 <https://github.com/readthedocs/readthedocs.org/pull/8507>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Update onboarding (`#8504 <https://github.com/readthedocs/readthedocs.org/pull/8504>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: List default installed dependencies (`#8503 <https://github.com/readthedocs/readthedocs.org/pull/8503>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Clarify that the development installation instructions are for Linux (`#8494 <https://github.com/readthedocs/readthedocs.org/pull/8494>`__)
* `@stsewd <https://github.com/stsewd>`__: Audit: attach organization (`#8491 <https://github.com/readthedocs/readthedocs.org/pull/8491>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Add virtual env instructions to local installation (`#8488 <https://github.com/readthedocs/readthedocs.org/pull/8488>`__)
* `@humitos <https://github.com/humitos>`__: Requirement: update orjson (`#8487 <https://github.com/readthedocs/readthedocs.org/pull/8487>`__)
* `@humitos <https://github.com/humitos>`__: Release 5.23.5 (`#8486 <https://github.com/readthedocs/readthedocs.org/pull/8486>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: New Read the Docs tutorial, part II (`#8473 <https://github.com/readthedocs/readthedocs.org/pull/8473>`__)

Version 5.23.5
--------------

:Date: September 14, 2021

* `@humitos <https://github.com/humitos>`__: Organization: only mark artifacts cleaned as False if they are True (`#8481 <https://github.com/readthedocs/readthedocs.org/pull/8481>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Fix link to version states documentation (`#8475 <https://github.com/readthedocs/readthedocs.org/pull/8475>`__)
* `@stsewd <https://github.com/stsewd>`__: OAuth models: increase avatar_url lenght (`#8472 <https://github.com/readthedocs/readthedocs.org/pull/8472>`__)
* `@pzhlkj6612 <https://github.com/pzhlkj6612>`__: Docs: update the links to the dependency management content of setuptools docs (`#8470 <https://github.com/readthedocs/readthedocs.org/pull/8470>`__)
* `@stsewd <https://github.com/stsewd>`__: Permissions: avoid using project.users, use proper permissions instead (`#8458 <https://github.com/readthedocs/readthedocs.org/pull/8458>`__)
* `@humitos <https://github.com/humitos>`__: Docker build images: update design doc (`#8447 <https://github.com/readthedocs/readthedocs.org/pull/8447>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: New Read the Docs tutorial, part I (`#8428 <https://github.com/readthedocs/readthedocs.org/pull/8428>`__)

Version 5.23.4
--------------

:Date: September 07, 2021

* `@pzhlkj6612 <https://github.com/pzhlkj6612>`__: Docs: update the links to the dependency management content of setuptools docs (`#8470 <https://github.com/readthedocs/readthedocs.org/pull/8470>`__)
* `@nienn <https://github.com/nienn>`__: Add custom team img styling (`#8467 <https://github.com/readthedocs/readthedocs.org/pull/8467>`__)
* `@nienn <https://github.com/nienn>`__: Docs: Change "right-click" to "click" (`#8465 <https://github.com/readthedocs/readthedocs.org/pull/8465>`__)
* `@stsewd <https://github.com/stsewd>`__: Permissions: avoid using project.users, use proper permissions instead (`#8458 <https://github.com/readthedocs/readthedocs.org/pull/8458>`__)
* `@stsewd <https://github.com/stsewd>`__: Add templatetag to filter by admin projects (`#8456 <https://github.com/readthedocs/readthedocs.org/pull/8456>`__)
* `@stsewd <https://github.com/stsewd>`__: Support form: don't allow to change the email (`#8455 <https://github.com/readthedocs/readthedocs.org/pull/8455>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: show only results from the current role_name being filtered (`#8454 <https://github.com/readthedocs/readthedocs.org/pull/8454>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 35 (`#8451 <https://github.com/readthedocs/readthedocs.org/pull/8451>`__)
* `@stsewd <https://github.com/stsewd>`__: Update common (`#8449 <https://github.com/readthedocs/readthedocs.org/pull/8449>`__)
* `@stsewd <https://github.com/stsewd>`__: API v3 (subprojects): filter by correct owner/organization (`#8446 <https://github.com/readthedocs/readthedocs.org/pull/8446>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Rework Team page (`#8441 <https://github.com/readthedocs/readthedocs.org/pull/8441>`__)
* `@mforbes <https://github.com/mforbes>`__: Added note about how to use Anaconda Project. (`#8436 <https://github.com/readthedocs/readthedocs.org/pull/8436>`__)
* `@stsewd <https://github.com/stsewd>`__: Contact users: pass user and domain in the context (`#8430 <https://github.com/readthedocs/readthedocs.org/pull/8430>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: New Read the Docs tutorial, part I (`#8428 <https://github.com/readthedocs/readthedocs.org/pull/8428>`__)
* `@stsewd <https://github.com/stsewd>`__: Footer: remove auth block (`#8397 <https://github.com/readthedocs/readthedocs.org/pull/8397>`__)
* `@stsewd <https://github.com/stsewd>`__: API: fix subprojects creation when organizaions are enabled (`#8393 <https://github.com/readthedocs/readthedocs.org/pull/8393>`__)
* `@stsewd <https://github.com/stsewd>`__: QuerySets: remove unused overrides (`#8299 <https://github.com/readthedocs/readthedocs.org/pull/8299>`__)
* `@stsewd <https://github.com/stsewd>`__: QuerySets: filter permissions by organizations (`#8298 <https://github.com/readthedocs/readthedocs.org/pull/8298>`__)

Version 5.23.3
--------------

:Date: August 30, 2021

* `@stsewd <https://github.com/stsewd>`__: Update common (`#8449 <https://github.com/readthedocs/readthedocs.org/pull/8449>`__)
* `@stsewd <https://github.com/stsewd>`__: Upgrade ES to 7.14.0 (`#8448 <https://github.com/readthedocs/readthedocs.org/pull/8448>`__)
* `@humitos <https://github.com/humitos>`__: Docs: typo in tutorial (`#8442 <https://github.com/readthedocs/readthedocs.org/pull/8442>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Docs miscellaneous enhancements (`#8440 <https://github.com/readthedocs/readthedocs.org/pull/8440>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: New Read the Docs tutorial, part I (`#8428 <https://github.com/readthedocs/readthedocs.org/pull/8428>`__)
* `@humitos <https://github.com/humitos>`__: Track organization artifacts cleanup (`#8418 <https://github.com/readthedocs/readthedocs.org/pull/8418>`__)

Version 5.23.2
--------------

:Date: August 24, 2021

* `@astrojuanlu <https://github.com/astrojuanlu>`__: Add MyST (Markdown) examples to "cross referencing with Sphinx" guide (`#8437 <https://github.com/readthedocs/readthedocs.org/pull/8437>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Added Search and Filters for `RemoteRepository` and `RemoteOrganization` admin list page (`#8431 <https://github.com/readthedocs/readthedocs.org/pull/8431>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Try out codeowners (`#8429 <https://github.com/readthedocs/readthedocs.org/pull/8429>`__)
* `@humitos <https://github.com/humitos>`__: Proxito: do not log response header for each custom domain request (`#8427 <https://github.com/readthedocs/readthedocs.org/pull/8427>`__)
* `@cclauss <https://github.com/cclauss>`__: Fix undefined names (`#8425 <https://github.com/readthedocs/readthedocs.org/pull/8425>`__)
* `@stsewd <https://github.com/stsewd>`__: Allow cookies from cross site requests to avoid problems with iframes (`#8422 <https://github.com/readthedocs/readthedocs.org/pull/8422>`__)
* `@cclauss <https://github.com/cclauss>`__: Finish codespell -- Concludes #8409 (`#8421 <https://github.com/readthedocs/readthedocs.org/pull/8421>`__)
* `@cclauss <https://github.com/cclauss>`__: codespell CHANGELOG.rst (`#8420 <https://github.com/readthedocs/readthedocs.org/pull/8420>`__)
* `@cclauss <https://github.com/cclauss>`__: codespell part 2 - Continues #8409 (`#8419 <https://github.com/readthedocs/readthedocs.org/pull/8419>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Don't filter on large items in the auditing sidebar. (`#8417 <https://github.com/readthedocs/readthedocs.org/pull/8417>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Fix YAML extension (`#8416 <https://github.com/readthedocs/readthedocs.org/pull/8416>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 5.23.1 (`#8415 <https://github.com/readthedocs/readthedocs.org/pull/8415>`__)
* `@stsewd <https://github.com/stsewd>`__: Audit: attach project from the request if available (`#8414 <https://github.com/readthedocs/readthedocs.org/pull/8414>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: update logout button image (`#8413 <https://github.com/readthedocs/readthedocs.org/pull/8413>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 33 (`#8411 <https://github.com/readthedocs/readthedocs.org/pull/8411>`__)
* `@cclauss <https://github.com/cclauss>`__: Fix typos discovered by codespell in /docs (`#8409 <https://github.com/readthedocs/readthedocs.org/pull/8409>`__)
* `@stsewd <https://github.com/stsewd>`__: Support: update contact information via Front webhook (`#8406 <https://github.com/readthedocs/readthedocs.org/pull/8406>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: environment variables (`#8390 <https://github.com/readthedocs/readthedocs.org/pull/8390>`__)
* `@stsewd <https://github.com/stsewd>`__: Allow users to remove themselves from a project (`#8384 <https://github.com/readthedocs/readthedocs.org/pull/8384>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: document how to terminate a session (`#8286 <https://github.com/readthedocs/readthedocs.org/pull/8286>`__)

Version 5.23.1
--------------

:Date: August 16, 2021

* `@cclauss <https://github.com/cclauss>`__: Fix typos discovered by codespell in /docs (`#8409 <https://github.com/readthedocs/readthedocs.org/pull/8409>`__)
* `@stsewd <https://github.com/stsewd>`__: Audit: use analytics' get_client_ip (`#8404 <https://github.com/readthedocs/readthedocs.org/pull/8404>`__)
* `@steko <https://github.com/steko>`__: Add documentation about webhooks for Gitea (`#8402 <https://github.com/readthedocs/readthedocs.org/pull/8402>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add CSP header to the domain options (`#8388 <https://github.com/readthedocs/readthedocs.org/pull/8388>`__)
* `@stsewd <https://github.com/stsewd>`__: Cookies: set samesite: `Lax` by default (`#8304 <https://github.com/readthedocs/readthedocs.org/pull/8304>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: document how to terminate a session (`#8286 <https://github.com/readthedocs/readthedocs.org/pull/8286>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: update sharing (`#8239 <https://github.com/readthedocs/readthedocs.org/pull/8239>`__)

Version 5.23.0
--------------

:Date: August 09, 2021

* `@ericholscher <https://github.com/ericholscher>`__: Only call analytics tracking of flyout when analytics are enabled (`#8398 <https://github.com/readthedocs/readthedocs.org/pull/8398>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 31 (`#8385 <https://github.com/readthedocs/readthedocs.org/pull/8385>`__)
* `@stsewd <https://github.com/stsewd>`__: Audit: track user events (`#8379 <https://github.com/readthedocs/readthedocs.org/pull/8379>`__)
* `@stsewd <https://github.com/stsewd>`__: Cookies: set samesite: `Lax` by default (`#8304 <https://github.com/readthedocs/readthedocs.org/pull/8304>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: update sharing (`#8239 <https://github.com/readthedocs/readthedocs.org/pull/8239>`__)
* `@DetectedStorm <https://github.com/DetectedStorm>`__: Update LICENSE (`#5125 <https://github.com/readthedocs/readthedocs.org/pull/5125>`__)

Version 5.22.0
--------------

:Date: August 02, 2021

* `@pzhlkj6612 <https://github.com/pzhlkj6612>`__: Docs: fix typo in versions.rst: -> need (`#8383 <https://github.com/readthedocs/readthedocs.org/pull/8383>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Remove clickjacking middleware for proxito (`#8378 <https://github.com/readthedocs/readthedocs.org/pull/8378>`__)
* `@stsewd <https://github.com/stsewd>`__: Config file: use string for python.version (`#8372 <https://github.com/readthedocs/readthedocs.org/pull/8372>`__)
* `@humitos <https://github.com/humitos>`__: Add support for Python3.10 on `testing` Docker image (`#8328 <https://github.com/readthedocs/readthedocs.org/pull/8328>`__)
* `@stsewd <https://github.com/stsewd>`__: Analytics: don't fail if the page was created in another request (`#8310 <https://github.com/readthedocs/readthedocs.org/pull/8310>`__)

Version 5.21.0
--------------

:Date: July 27, 2021

* `@stsewd <https://github.com/stsewd>`__: Fix migrations (`#8373 <https://github.com/readthedocs/readthedocs.org/pull/8373>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Build out the MyST section of the getting started (`#8371 <https://github.com/readthedocs/readthedocs.org/pull/8371>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix tasks (`#8370 <https://github.com/readthedocs/readthedocs.org/pull/8370>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Update common (`#8368 <https://github.com/readthedocs/readthedocs.org/pull/8368>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Redirect users to appropriate support channels using template chooser (`#8366 <https://github.com/readthedocs/readthedocs.org/pull/8366>`__)
* `@humitos <https://github.com/humitos>`__: Proxito: return user-defined HTTP headers on custom domains (`#8360 <https://github.com/readthedocs/readthedocs.org/pull/8360>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 5.20.3 (`#8356 <https://github.com/readthedocs/readthedocs.org/pull/8356>`__)
* `@stsewd <https://github.com/stsewd>`__: Track model changes with django-simple-history (`#8355 <https://github.com/readthedocs/readthedocs.org/pull/8355>`__)
* `@stsewd <https://github.com/stsewd>`__: SSO: move models (`#8330 <https://github.com/readthedocs/readthedocs.org/pull/8330>`__)

Version 5.20.3
--------------

:Date: July 19, 2021

* `@Nkarnaud <https://github.com/Nkarnaud>`__: change vieweable to viewable on  home page: issue#8346 (`#8351 <https://github.com/readthedocs/readthedocs.org/pull/8351>`__)
* `@stsewd <https://github.com/stsewd>`__: Builds: don't record git rev-parse command (`#8348 <https://github.com/readthedocs/readthedocs.org/pull/8348>`__)
* `@stsewd <https://github.com/stsewd>`__: UI: allow to close notifications (`#8345 <https://github.com/readthedocs/readthedocs.org/pull/8345>`__)
* `@stsewd <https://github.com/stsewd>`__: Use email from DEFAULT_FROM_EMAIL to contact users (`#8344 <https://github.com/readthedocs/readthedocs.org/pull/8344>`__)
* `@stsewd <https://github.com/stsewd>`__: Downgrade taggit (`#8342 <https://github.com/readthedocs/readthedocs.org/pull/8342>`__)
* `@stsewd <https://github.com/stsewd>`__: Dont mutate env vars outside the BuildEnv classes (`#8340 <https://github.com/readthedocs/readthedocs.org/pull/8340>`__)
* `@stsewd <https://github.com/stsewd>`__: Guides: how to import a private project using an ssh key (`#8336 <https://github.com/readthedocs/readthedocs.org/pull/8336>`__)

Version 5.20.2
--------------

:Date: July 13, 2021

* `@humitos <https://github.com/humitos>`__: psycopg2: pin to a compatible version with Django 2.2 (`#8335 <https://github.com/readthedocs/readthedocs.org/pull/8335>`__)
* `@stsewd <https://github.com/stsewd>`__: Contact owners: use correct organization to filter (`#8325 <https://github.com/readthedocs/readthedocs.org/pull/8325>`__)
* `@humitos <https://github.com/humitos>`__: Design doc: fix render api endpoints (`#8320 <https://github.com/readthedocs/readthedocs.org/pull/8320>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 27 (`#8317 <https://github.com/readthedocs/readthedocs.org/pull/8317>`__)
* `@mongolsteppe <https://github.com/mongolsteppe>`__: Fixing minor error (`#8313 <https://github.com/readthedocs/readthedocs.org/pull/8313>`__)
* `@stsewd <https://github.com/stsewd>`__: Build: remove after_vcs signal (`#8311 <https://github.com/readthedocs/readthedocs.org/pull/8311>`__)
* `@The-Compiler <https://github.com/The-Compiler>`__: Add link to redirect docs (`#8308 <https://github.com/readthedocs/readthedocs.org/pull/8308>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add docs about setting up permissions for GH apps & orgs (`#8305 <https://github.com/readthedocs/readthedocs.org/pull/8305>`__)
* `@stsewd <https://github.com/stsewd>`__: Schema: fix version type (`#8303 <https://github.com/readthedocs/readthedocs.org/pull/8303>`__)
* `@stsewd <https://github.com/stsewd>`__: Slugify: don't generate slugs with trailing `-` (`#8302 <https://github.com/readthedocs/readthedocs.org/pull/8302>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Increase guide depth (`#8300 <https://github.com/readthedocs/readthedocs.org/pull/8300>`__)
* `@humitos <https://github.com/humitos>`__: autoscaling: remove app autoscaling tasks (`#8297 <https://github.com/readthedocs/readthedocs.org/pull/8297>`__)
* `@humitos <https://github.com/humitos>`__: PR build status: re-try up to 3 times if it fails for some reason (`#8296 <https://github.com/readthedocs/readthedocs.org/pull/8296>`__)
* `@SethFalco <https://github.com/SethFalco>`__: feat: add json schema (`#8294 <https://github.com/readthedocs/readthedocs.org/pull/8294>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 26 (`#8293 <https://github.com/readthedocs/readthedocs.org/pull/8293>`__)
* `@stsewd <https://github.com/stsewd>`__: Organizations: validate that a correct slug is generated (`#8292 <https://github.com/readthedocs/readthedocs.org/pull/8292>`__)
* `@stsewd <https://github.com/stsewd>`__: Footer: remove unused context vars (`#8285 <https://github.com/readthedocs/readthedocs.org/pull/8285>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Add new guide about Jupyter in Sphinx (`#8283 <https://github.com/readthedocs/readthedocs.org/pull/8283>`__)
* `@humitos <https://github.com/humitos>`__: oauth webhook: check the `Project` has a `RemoteRepository` (`#8282 <https://github.com/readthedocs/readthedocs.org/pull/8282>`__)
* `@stsewd <https://github.com/stsewd>`__: Allow to email users from a management command (`#8243 <https://github.com/readthedocs/readthedocs.org/pull/8243>`__)
* `@humitos <https://github.com/humitos>`__: Design doc: Embed APIv3 (`#8222 <https://github.com/readthedocs/readthedocs.org/pull/8222>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Add proposal for new Sphinx and RTD tutorials (`#8106 <https://github.com/readthedocs/readthedocs.org/pull/8106>`__)
* `@stsewd <https://github.com/stsewd>`__: Allow to change the privacy level of external versions (`#7825 <https://github.com/readthedocs/readthedocs.org/pull/7825>`__)
* `@stsewd <https://github.com/stsewd>`__: Add tests for remove index files (`#6381 <https://github.com/readthedocs/readthedocs.org/pull/6381>`__)

Version 5.20.1
--------------

:Date: June 28, 2021

* `@stsewd <https://github.com/stsewd>`__: Organizations: validate that a correct slug is generated (`#8292 <https://github.com/readthedocs/readthedocs.org/pull/8292>`__)
* `@stsewd <https://github.com/stsewd>`__: Footer: remove unused context vars (`#8285 <https://github.com/readthedocs/readthedocs.org/pull/8285>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: remove additional fields (`#8284 <https://github.com/readthedocs/readthedocs.org/pull/8284>`__)
* `@humitos <https://github.com/humitos>`__: oauth webhook: check the `Project` has a `RemoteRepository` (`#8282 <https://github.com/readthedocs/readthedocs.org/pull/8282>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: small improvements (`#8276 <https://github.com/readthedocs/readthedocs.org/pull/8276>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: ask for confirmation when running reindex_elasticsearch (`#8275 <https://github.com/readthedocs/readthedocs.org/pull/8275>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Hit Elasticsearch only once for each search query through the APIv2 (`#8228 <https://github.com/readthedocs/readthedocs.org/pull/8228>`__)
* `@humitos <https://github.com/humitos>`__: Design doc: Embed APIv3 (`#8222 <https://github.com/readthedocs/readthedocs.org/pull/8222>`__)
* `@stsewd <https://github.com/stsewd>`__: QuerySets: remove include_all (`#8212 <https://github.com/readthedocs/readthedocs.org/pull/8212>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Add proposal for new Sphinx and RTD tutorials (`#8106 <https://github.com/readthedocs/readthedocs.org/pull/8106>`__)
* `@stsewd <https://github.com/stsewd>`__: Add tests for remove index files (`#6381 <https://github.com/readthedocs/readthedocs.org/pull/6381>`__)

Version 5.20.0
--------------

:Date: June 22, 2021

* `@humitos <https://github.com/humitos>`__: Migration: fix RemoteRepository - Project data migration (`#8271 <https://github.com/readthedocs/readthedocs.org/pull/8271>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 5.19.0 (`#8266 <https://github.com/readthedocs/readthedocs.org/pull/8266>`__)
* `@humitos <https://github.com/humitos>`__: Sync RemoteRepository for external collaborators (`#8265 <https://github.com/readthedocs/readthedocs.org/pull/8265>`__)
* `@stsewd <https://github.com/stsewd>`__: Git: don't expand envvars in Gitpython (`#8263 <https://github.com/readthedocs/readthedocs.org/pull/8263>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 24 (`#8262 <https://github.com/readthedocs/readthedocs.org/pull/8262>`__)
* `@stsewd <https://github.com/stsewd>`__: Builds: check for nonexistent object (`#8261 <https://github.com/readthedocs/readthedocs.org/pull/8261>`__)
* `@humitos <https://github.com/humitos>`__: Make `Project -> ForeignKey -> RemoteRepository` (`#8259 <https://github.com/readthedocs/readthedocs.org/pull/8259>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Add basic security policy (`#8254 <https://github.com/readthedocs/readthedocs.org/pull/8254>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: remove workaround for subprojects (`#8211 <https://github.com/readthedocs/readthedocs.org/pull/8211>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: allow to filter by project slugs (`#8149 <https://github.com/readthedocs/readthedocs.org/pull/8149>`__)

Version 5.19.0
--------------

.. warning:: This release contains a security fix to our CSRF settings: https://github.com/readthedocs/readthedocs.org/security/advisories/GHSA-3v5m-qmm9-3c6c

:Date: June 15, 2021

* `@stsewd <https://github.com/stsewd>`__: Builds: check for nonexistent object (`#8261 <https://github.com/readthedocs/readthedocs.org/pull/8261>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Remove video from our Sphinx quickstart. (`#8246 <https://github.com/readthedocs/readthedocs.org/pull/8246>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Remove "Markdown" from Mkdocs title (`#8245 <https://github.com/readthedocs/readthedocs.org/pull/8245>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Make sustainability page more visible (`#8244 <https://github.com/readthedocs/readthedocs.org/pull/8244>`__)
* `@stsewd <https://github.com/stsewd>`__: Builds: move send_build_status to builds/tasks.py (`#8241 <https://github.com/readthedocs/readthedocs.org/pull/8241>`__)
* `@humitos <https://github.com/humitos>`__: Add ability to rebuild a specific build (`#8227 <https://github.com/readthedocs/readthedocs.org/pull/8227>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Don't do any CORS checking on Embed API requests (`#8226 <https://github.com/readthedocs/readthedocs.org/pull/8226>`__)
* `@stsewd <https://github.com/stsewd>`__: Footer: return well formed html (`#8202 <https://github.com/readthedocs/readthedocs.org/pull/8202>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Add project/build filters (`#8142 <https://github.com/readthedocs/readthedocs.org/pull/8142>`__)
* `@humitos <https://github.com/humitos>`__: Sign Up: limit the providers allowed to sign up (`#8062 <https://github.com/readthedocs/readthedocs.org/pull/8062>`__)
* `@stsewd <https://github.com/stsewd>`__:  Search: use multi-fields for Wildcard queries  (`#7613 <https://github.com/readthedocs/readthedocs.org/pull/7613>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add ability to rebuild a specific build (`#6995 <https://github.com/readthedocs/readthedocs.org/pull/6995>`__)

Version 5.18.0
--------------

:Date: June 08, 2021

* `@stsewd <https://github.com/stsewd>`__: Fix tests (`#8240 <https://github.com/readthedocs/readthedocs.org/pull/8240>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Backport manual indexes (`#8235 <https://github.com/readthedocs/readthedocs.org/pull/8235>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Clean up SSO docs (`#8233 <https://github.com/readthedocs/readthedocs.org/pull/8233>`__)
* `@stsewd <https://github.com/stsewd>`__: Cache get_project (`#8231 <https://github.com/readthedocs/readthedocs.org/pull/8231>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Don't do any CORS checking on Embed API requests (`#8226 <https://github.com/readthedocs/readthedocs.org/pull/8226>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Optimize Index time database query (`#8224 <https://github.com/readthedocs/readthedocs.org/pull/8224>`__)
* `@stsewd <https://github.com/stsewd>`__: Proxito: check if attribute exists (`#8220 <https://github.com/readthedocs/readthedocs.org/pull/8220>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Update gitter channel name (`#8217 <https://github.com/readthedocs/readthedocs.org/pull/8217>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Remove IRC from our docs (`#8216 <https://github.com/readthedocs/readthedocs.org/pull/8216>`__)
* `@stsewd <https://github.com/stsewd>`__: QuerySets: filter by admin/team (`#8214 <https://github.com/readthedocs/readthedocs.org/pull/8214>`__)
* `@stsewd <https://github.com/stsewd>`__: QuerySets: remove unused `detail` parameter (`#8213 <https://github.com/readthedocs/readthedocs.org/pull/8213>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 21 (`#8206 <https://github.com/readthedocs/readthedocs.org/pull/8206>`__)
* `@stsewd <https://github.com/stsewd>`__: QuerySets: refactor _add_user_repos (`#8182 <https://github.com/readthedocs/readthedocs.org/pull/8182>`__)
* `@stsewd <https://github.com/stsewd>`__: Organizations: simplify querysets/managers (`#8180 <https://github.com/readthedocs/readthedocs.org/pull/8180>`__)
* `@akien-mga <https://github.com/akien-mga>`__: Docs: Add section about deleting downloadable content (`#8162 <https://github.com/readthedocs/readthedocs.org/pull/8162>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: refactor views (`#8157 <https://github.com/readthedocs/readthedocs.org/pull/8157>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: little optimization when saving search queries (`#8132 <https://github.com/readthedocs/readthedocs.org/pull/8132>`__)
* `@akien-mga <https://github.com/akien-mga>`__: Docs: Add some details to the User Defined Redirects (`#7894 <https://github.com/readthedocs/readthedocs.org/pull/7894>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Add APIv3 version edit URL (`#7594 <https://github.com/readthedocs/readthedocs.org/pull/7594>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Add List API Endpoint for `RemoteRepository` and `RemoteOrganization` (`#7510 <https://github.com/readthedocs/readthedocs.org/pull/7510>`__)

Version 5.17.0
--------------

:Date: May 24, 2021

* `@stsewd <https://github.com/stsewd>`__: Proxito: don't require the middleware for proxied apis (`#8203 <https://github.com/readthedocs/readthedocs.org/pull/8203>`__)
* `@stsewd <https://github.com/stsewd>`__: Builds: prevent code injection in cwd (`#8198 <https://github.com/readthedocs/readthedocs.org/pull/8198>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Remove specific name from security page at user request (`#8195 <https://github.com/readthedocs/readthedocs.org/pull/8195>`__)
* `@humitos <https://github.com/humitos>`__: Docker: remove `volumes=` argument when creating the container (`#8194 <https://github.com/readthedocs/readthedocs.org/pull/8194>`__)
* `@stsewd <https://github.com/stsewd>`__: Proxito: fix https and canonical redirects (`#8193 <https://github.com/readthedocs/readthedocs.org/pull/8193>`__)
* `@stsewd <https://github.com/stsewd>`__: API v2: allow listing when using private repos (`#8192 <https://github.com/readthedocs/readthedocs.org/pull/8192>`__)
* `@stsewd <https://github.com/stsewd>`__: Docker: set cwd explicitly (`#8191 <https://github.com/readthedocs/readthedocs.org/pull/8191>`__)
* `@stsewd <https://github.com/stsewd>`__: API v2: allow to filter more endpoints (`#8189 <https://github.com/readthedocs/readthedocs.org/pull/8189>`__)
* `@stsewd <https://github.com/stsewd>`__: Proxito: redirect to main project from subprojects (`#8187 <https://github.com/readthedocs/readthedocs.org/pull/8187>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 20 (`#8186 <https://github.com/readthedocs/readthedocs.org/pull/8186>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Add DPA to legal docs in documentation (`#8130 <https://github.com/readthedocs/readthedocs.org/pull/8130>`__)

Version 5.16.0
--------------

:Date: May 18, 2021

* `@stsewd <https://github.com/stsewd>`__: QuerySets: check for .is_superuser instead of has_perm (`#8181 <https://github.com/readthedocs/readthedocs.org/pull/8181>`__)
* `@humitos <https://github.com/humitos>`__: Build: use `is_active` method to know if the build should be skipped (`#8179 <https://github.com/readthedocs/readthedocs.org/pull/8179>`__)
* `@humitos <https://github.com/humitos>`__: APIv2: disable listing endpoints (`#8178 <https://github.com/readthedocs/readthedocs.org/pull/8178>`__)
* `@stsewd <https://github.com/stsewd>`__: Project: use IntegerField for `remote_repository` from project form. (`#8176 <https://github.com/readthedocs/readthedocs.org/pull/8176>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: remove some lies from cross referencing guide (`#8173 <https://github.com/readthedocs/readthedocs.org/pull/8173>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: add space to bash code (`#8171 <https://github.com/readthedocs/readthedocs.org/pull/8171>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 19 (`#8170 <https://github.com/readthedocs/readthedocs.org/pull/8170>`__)
* `@stsewd <https://github.com/stsewd>`__: Querysets: include organizations in is_active check (`#8163 <https://github.com/readthedocs/readthedocs.org/pull/8163>`__)
* `@stsewd <https://github.com/stsewd>`__: Querysets: remove private and for_project (`#8158 <https://github.com/readthedocs/readthedocs.org/pull/8158>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Disable FLOC by introducing permissions policy header (`#8145 <https://github.com/readthedocs/readthedocs.org/pull/8145>`__)
* `@stsewd <https://github.com/stsewd>`__: Build: allow to install packages with apt (`#8065 <https://github.com/readthedocs/readthedocs.org/pull/8065>`__)

Version 5.15.0
--------------

:Date: May 10, 2021

* `@stsewd <https://github.com/stsewd>`__: Ads: don't load script if a project is marked as ad_free (`#8164 <https://github.com/readthedocs/readthedocs.org/pull/8164>`__)
* `@stsewd <https://github.com/stsewd>`__: Querysets: include organizations in is_active check (`#8163 <https://github.com/readthedocs/readthedocs.org/pull/8163>`__)
* `@stsewd <https://github.com/stsewd>`__: Querysets: simplify project querysets (`#8154 <https://github.com/readthedocs/readthedocs.org/pull/8154>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 18 (`#8153 <https://github.com/readthedocs/readthedocs.org/pull/8153>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: default to search on default version of subprojects (`#8148 <https://github.com/readthedocs/readthedocs.org/pull/8148>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove protected privacy level (`#8146 <https://github.com/readthedocs/readthedocs.org/pull/8146>`__)
* `@stsewd <https://github.com/stsewd>`__: Embed: fix paths that start with `/` (`#8139 <https://github.com/readthedocs/readthedocs.org/pull/8139>`__)
* `@humitos <https://github.com/humitos>`__: Metrics: run metrics task every 30 minutes (`#8138 <https://github.com/readthedocs/readthedocs.org/pull/8138>`__)
* `@humitos <https://github.com/humitos>`__: web-celery: add logging for OOM debug on suspicious tasks (`#8131 <https://github.com/readthedocs/readthedocs.org/pull/8131>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Fix a few style and grammar issues with SSO docs (`#8109 <https://github.com/readthedocs/readthedocs.org/pull/8109>`__)
* `@stsewd <https://github.com/stsewd>`__: Embed: don't fail while querying sections with bad id (`#8084 <https://github.com/readthedocs/readthedocs.org/pull/8084>`__)
* `@stsewd <https://github.com/stsewd>`__: Design doc: allow to install packages using apt (`#8060 <https://github.com/readthedocs/readthedocs.org/pull/8060>`__)

Version 5.14.3
--------------

:Date: April 26, 2021

* `@humitos <https://github.com/humitos>`__: Metrics: run metrics task every 30 minutes (`#8138 <https://github.com/readthedocs/readthedocs.org/pull/8138>`__)
* `@humitos <https://github.com/humitos>`__: web-celery: add logging for OOM debug on suspicious tasks (`#8131 <https://github.com/readthedocs/readthedocs.org/pull/8131>`__)
* `@stsewd <https://github.com/stsewd>`__: Celery router: check all `n` last builds for Conda (`#8129 <https://github.com/readthedocs/readthedocs.org/pull/8129>`__)
* `@jonels-msft <https://github.com/jonels-msft>`__: Include aria-label in flyout search box (`#8127 <https://github.com/readthedocs/readthedocs.org/pull/8127>`__)
* `@humitos <https://github.com/humitos>`__: Logging: use %s to format the variable (`#8125 <https://github.com/readthedocs/readthedocs.org/pull/8125>`__)
* `@stsewd <https://github.com/stsewd>`__: Build: improve list_packages_installed (`#8122 <https://github.com/readthedocs/readthedocs.org/pull/8122>`__)
* `@stsewd <https://github.com/stsewd>`__: BuildCommand: don't leak stacktrace to the user (`#8121 <https://github.com/readthedocs/readthedocs.org/pull/8121>`__)
* `@stsewd <https://github.com/stsewd>`__: API (v2): use empty list in serializer's exclude (`#8120 <https://github.com/readthedocs/readthedocs.org/pull/8120>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Miscellaneous doc improvements (`#8118 <https://github.com/readthedocs/readthedocs.org/pull/8118>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 16 (`#8117 <https://github.com/readthedocs/readthedocs.org/pull/8117>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Fix a few style and grammar issues with SSO docs (`#8109 <https://github.com/readthedocs/readthedocs.org/pull/8109>`__)

Version 5.14.2
--------------

:Date: April 20, 2021

* `@stsewd <https://github.com/stsewd>`__: OAuth: check if user exists (`#8115 <https://github.com/readthedocs/readthedocs.org/pull/8115>`__)
* `@stsewd <https://github.com/stsewd>`__: Sync versions: don't fetch/return all versions (`#8114 <https://github.com/readthedocs/readthedocs.org/pull/8114>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Improve contributing docs, take 2 (`#8113 <https://github.com/readthedocs/readthedocs.org/pull/8113>`__)
* `@stsewd <https://github.com/stsewd>`__: ImportedFile: remove md5 field (`#8111 <https://github.com/readthedocs/readthedocs.org/pull/8111>`__)
* `@stsewd <https://github.com/stsewd>`__: Config file: improve docs and help text (`#8110 <https://github.com/readthedocs/readthedocs.org/pull/8110>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: add warning about design docs (`#8104 <https://github.com/readthedocs/readthedocs.org/pull/8104>`__)
* `@Harmon758 <https://github.com/Harmon758>`__: Docs: fix typo in config-file/v2.rst (`#8102 <https://github.com/readthedocs/readthedocs.org/pull/8102>`__)
* `@cocobennett <https://github.com/cocobennett>`__: Improve documentation on contributing to documentation (`#8082 <https://github.com/readthedocs/readthedocs.org/pull/8082>`__)

Version 5.14.1
--------------

:Date: April 13, 2021

* `@stsewd <https://github.com/stsewd>`__: OAuth: protection against deleted objects (`#8081 <https://github.com/readthedocs/readthedocs.org/pull/8081>`__)
* `@cocobennett <https://github.com/cocobennett>`__: Add page and page_size to server side api documentation (`#8080 <https://github.com/readthedocs/readthedocs.org/pull/8080>`__)
* `@stsewd <https://github.com/stsewd>`__: Version warning banner: inject on role="main" or main tag (`#8079 <https://github.com/readthedocs/readthedocs.org/pull/8079>`__)
* `@stsewd <https://github.com/stsewd>`__: OAuth: avoid undefined var (`#8078 <https://github.com/readthedocs/readthedocs.org/pull/8078>`__)
* `@stsewd <https://github.com/stsewd>`__: Conda: protect against None when appending core requirements (`#8077 <https://github.com/readthedocs/readthedocs.org/pull/8077>`__)
* `@humitos <https://github.com/humitos>`__: SSO: add small paragraph mentioning how to enable it on commercial (`#8063 <https://github.com/readthedocs/readthedocs.org/pull/8063>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Add separate version create view and create view URL (`#7595 <https://github.com/readthedocs/readthedocs.org/pull/7595>`__)

Version 5.14.0
--------------

:Date: April 06, 2021

This release includes a security update which was done in a private branch PR.
See our `security changelog <https://docs.readthedocs.io/en/latest/security.html#version-5-14-0>`__ for more details.

* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 14 (`#8071 <https://github.com/readthedocs/readthedocs.org/pull/8071>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Clarify ad-free conditions (`#8064 <https://github.com/readthedocs/readthedocs.org/pull/8064>`__)
* `@humitos <https://github.com/humitos>`__: SSO: add small paragraph mentioning how to enable it on commercial (`#8063 <https://github.com/readthedocs/readthedocs.org/pull/8063>`__)
* `@stsewd <https://github.com/stsewd>`__: Build environment: allow to run commands with a custom user (`#8058 <https://github.com/readthedocs/readthedocs.org/pull/8058>`__)
* `@humitos <https://github.com/humitos>`__: Design document for new Docker images structure (`#7566 <https://github.com/readthedocs/readthedocs.org/pull/7566>`__)

Version 5.13.0
--------------

:Date: March 30, 2021

* `@stsewd <https://github.com/stsewd>`__: Test proxied embed API (`#8051 <https://github.com/readthedocs/readthedocs.org/pull/8051>`__)
* `@stsewd <https://github.com/stsewd>`__: Feature flag: remove EXTERNAL_BUILD (`#8050 <https://github.com/readthedocs/readthedocs.org/pull/8050>`__)
* `@stsewd <https://github.com/stsewd>`__: Sync versions: always use a task (`#8049 <https://github.com/readthedocs/readthedocs.org/pull/8049>`__)
* `@stsewd <https://github.com/stsewd>`__: Versions: don't create versions in bulk (`#8046 <https://github.com/readthedocs/readthedocs.org/pull/8046>`__)
* `@stsewd <https://github.com/stsewd>`__: Embed: add cache tags (`#8045 <https://github.com/readthedocs/readthedocs.org/pull/8045>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix proxito slash redirect for leading slash (`#8044 <https://github.com/readthedocs/readthedocs.org/pull/8044>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 12 (`#8038 <https://github.com/readthedocs/readthedocs.org/pull/8038>`__)
* `@humitos <https://github.com/humitos>`__: Docs: cleanup of old/deprecated documents (`#7994 <https://github.com/readthedocs/readthedocs.org/pull/7994>`__)
* `@flying-sheep <https://github.com/flying-sheep>`__: Add publicly visible env vars (`#7891 <https://github.com/readthedocs/readthedocs.org/pull/7891>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove broadcast function (`#7044 <https://github.com/readthedocs/readthedocs.org/pull/7044>`__)

Version 5.12.2
--------------

:Date: March 23, 2021

* `@humitos <https://github.com/humitos>`__: AWS homepage link (`#8037 <https://github.com/readthedocs/readthedocs.org/pull/8037>`__)
* `@hukkinj1 <https://github.com/hukkinj1>`__: Fix a typo in the docs (`#8035 <https://github.com/readthedocs/readthedocs.org/pull/8035>`__)
* `@stsewd <https://github.com/stsewd>`__: Clean some feature flags (`#8034 <https://github.com/readthedocs/readthedocs.org/pull/8034>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Standardize footerjs code (`#8032 <https://github.com/readthedocs/readthedocs.org/pull/8032>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: remove pdf format in MkdDocs example (`#8030 <https://github.com/readthedocs/readthedocs.org/pull/8030>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: don't leak data for projects with this feature disabled (`#8029 <https://github.com/readthedocs/readthedocs.org/pull/8029>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Canonicalize all proxito slashes (`#8028 <https://github.com/readthedocs/readthedocs.org/pull/8028>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Make pageviews analytics show top 25 pages (`#8027 <https://github.com/readthedocs/readthedocs.org/pull/8027>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add CSV header data for search analytics  (`#8026 <https://github.com/readthedocs/readthedocs.org/pull/8026>`__)
* `@stsewd <https://github.com/stsewd>`__: HTMLFile: make md5 field nullable (`#8025 <https://github.com/readthedocs/readthedocs.org/pull/8025>`__)
* `@humitos <https://github.com/humitos>`__: Use `RemoteRepository` relation to match already imported projects (`#8024 <https://github.com/readthedocs/readthedocs.org/pull/8024>`__)
* `@stsewd <https://github.com/stsewd>`__: Badge: exclude duplicated builds (`#8023 <https://github.com/readthedocs/readthedocs.org/pull/8023>`__)
* `@stsewd <https://github.com/stsewd>`__: Intersphinx: declare user agent (`#8022 <https://github.com/readthedocs/readthedocs.org/pull/8022>`__)
* `@stsewd <https://github.com/stsewd>`__: Builds: restart build commands before a new build (`#7999 <https://github.com/readthedocs/readthedocs.org/pull/7999>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Remote Repository and  Remote Organization Normalization (`#7949 <https://github.com/readthedocs/readthedocs.org/pull/7949>`__)
* `@stsewd <https://github.com/stsewd>`__: Build: don't track changed files (`#7874 <https://github.com/readthedocs/readthedocs.org/pull/7874>`__)

Version 5.12.1
--------------

:Date: March 16, 2021

* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 11 (`#8019 <https://github.com/readthedocs/readthedocs.org/pull/8019>`__)
* `@stsewd <https://github.com/stsewd>`__: Embed: Allow to override embed view for proxied use (`#8018 <https://github.com/readthedocs/readthedocs.org/pull/8018>`__)
* `@humitos <https://github.com/humitos>`__: RemoteRepository: Improvements to `sync_vcs_data.py` script (`#8017 <https://github.com/readthedocs/readthedocs.org/pull/8017>`__)
* `@humitos <https://github.com/humitos>`__: Stripe checkout: handle events (`#8016 <https://github.com/readthedocs/readthedocs.org/pull/8016>`__)
* `@humitos <https://github.com/humitos>`__: Remove `contrib/` directory (`#8014 <https://github.com/readthedocs/readthedocs.org/pull/8014>`__)
* `@stsewd <https://github.com/stsewd>`__: Dockerfile: install lsb_release (`#8010 <https://github.com/readthedocs/readthedocs.org/pull/8010>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Fix AWS image so it looks sharp (`#8009 <https://github.com/readthedocs/readthedocs.org/pull/8009>`__)
* `@stsewd <https://github.com/stsewd>`__: Update common (`#8008 <https://github.com/readthedocs/readthedocs.org/pull/8008>`__)
* `@stsewd <https://github.com/stsewd>`__: Update Sphinx (`#8007 <https://github.com/readthedocs/readthedocs.org/pull/8007>`__)
* `@2Fake <https://github.com/2Fake>`__: fix small typo (`#8005 <https://github.com/readthedocs/readthedocs.org/pull/8005>`__)
* `@stsewd <https://github.com/stsewd>`__: Embed: validate query arguments (`#8003 <https://github.com/readthedocs/readthedocs.org/pull/8003>`__)
* `@humitos <https://github.com/humitos>`__: Stripe Checkout: handle duplicated wehbook (`#8002 <https://github.com/readthedocs/readthedocs.org/pull/8002>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Add __str__ to RemoteRepositoryRelation and RemoteOrganizationRelation and Use raw_id_fields in Admin (`#8001 <https://github.com/readthedocs/readthedocs.org/pull/8001>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Remove duplicate results from RemoteOrganization API (`#8000 <https://github.com/readthedocs/readthedocs.org/pull/8000>`__)
* `@humitos <https://github.com/humitos>`__: Typo fixed on `checkout.js` (`#7998 <https://github.com/readthedocs/readthedocs.org/pull/7998>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Make SupportView login_required (`#7997 <https://github.com/readthedocs/readthedocs.org/pull/7997>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 5.12.0 (`#7996 <https://github.com/readthedocs/readthedocs.org/pull/7996>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 10 (`#7995 <https://github.com/readthedocs/readthedocs.org/pull/7995>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Remove json field from RemoteRepositoryRelation and RemoteOrganizationRelation model (`#7993 <https://github.com/readthedocs/readthedocs.org/pull/7993>`__)
* `@humitos <https://github.com/humitos>`__: Use independent Docker image to build assets (`#7992 <https://github.com/readthedocs/readthedocs.org/pull/7992>`__)
* `@Pradhvan <https://github.com/Pradhvan>`__: Fixes typo in getting-started-with-sphinx: (`#7991 <https://github.com/readthedocs/readthedocs.org/pull/7991>`__)
* `@humitos <https://github.com/humitos>`__: Allow `donate` app to use Stripe Checkout for one-time donations (`#7983 <https://github.com/readthedocs/readthedocs.org/pull/7983>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add proxito healthcheck (`#7948 <https://github.com/readthedocs/readthedocs.org/pull/7948>`__)
* `@Pradhvan <https://github.com/Pradhvan>`__: Docs: Adds Myst to the getting started with sphinx (`#7938 <https://github.com/readthedocs/readthedocs.org/pull/7938>`__)
* `@humitos <https://github.com/humitos>`__: Use Stripe Checkout for Gold Users (`#7889 <https://github.com/readthedocs/readthedocs.org/pull/7889>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: guide about reproducible builds (`#7888 <https://github.com/readthedocs/readthedocs.org/pull/7888>`__)

Version 5.12.0
--------------

:Date: March 08, 2021

* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 10 (`#7995 <https://github.com/readthedocs/readthedocs.org/pull/7995>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Remove json field from RemoteRepositoryRelation and RemoteOrganizationRelation model (`#7993 <https://github.com/readthedocs/readthedocs.org/pull/7993>`__)
* `@humitos <https://github.com/humitos>`__: Use independent Docker image to build assets (`#7992 <https://github.com/readthedocs/readthedocs.org/pull/7992>`__)
* `@Pradhvan <https://github.com/Pradhvan>`__: Fixes typo in getting-started-with-sphinx: (`#7991 <https://github.com/readthedocs/readthedocs.org/pull/7991>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: use doctype from indexed pages instead of the db (`#7984 <https://github.com/readthedocs/readthedocs.org/pull/7984>`__)
* `@humitos <https://github.com/humitos>`__: Allow `donate` app to use Stripe Checkout for one-time donations (`#7983 <https://github.com/readthedocs/readthedocs.org/pull/7983>`__)
* `@humitos <https://github.com/humitos>`__: Update development/standards guide (`#7981 <https://github.com/readthedocs/readthedocs.org/pull/7981>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: update expand_tabs to work with the latest version of sphinx-tabs (`#7979 <https://github.com/readthedocs/readthedocs.org/pull/7979>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix build routing (`#7978 <https://github.com/readthedocs/readthedocs.org/pull/7978>`__)
* `@stsewd <https://github.com/stsewd>`__: Builds: register tasks to delete inactive external versions (`#7975 <https://github.com/readthedocs/readthedocs.org/pull/7975>`__)
* `@stsewd <https://github.com/stsewd>`__: Embed: fix join (`#7974 <https://github.com/readthedocs/readthedocs.org/pull/7974>`__)
* `@stsewd <https://github.com/stsewd>`__: Embed: change proxied urls (`#7973 <https://github.com/readthedocs/readthedocs.org/pull/7973>`__)
* `@ericholscher <https://github.com/ericholscher>`__: refactor footer, add jobs & status page (`#7970 <https://github.com/readthedocs/readthedocs.org/pull/7970>`__)
* `@stsewd <https://github.com/stsewd>`__: Sphinx domain: remove API (`#7969 <https://github.com/readthedocs/readthedocs.org/pull/7969>`__)
* `@humitos <https://github.com/humitos>`__: Upgrade `postgres-client` to v12 in Docker image (`#7967 <https://github.com/readthedocs/readthedocs.org/pull/7967>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Add management command to Load Project and RemoteRepository Relationship from JSON file (`#7966 <https://github.com/readthedocs/readthedocs.org/pull/7966>`__)
* `@astrojuanlu <https://github.com/astrojuanlu>`__: Update guide on conda support (`#7965 <https://github.com/readthedocs/readthedocs.org/pull/7965>`__)
* `@stsewd <https://github.com/stsewd>`__: Embed: add more tests (`#7962 <https://github.com/readthedocs/readthedocs.org/pull/7962>`__)
* `@humitos <https://github.com/humitos>`__: Lower rank of development/install.html (`#7960 <https://github.com/readthedocs/readthedocs.org/pull/7960>`__)
* `@stsewd <https://github.com/stsewd>`__: Embed: refactor view (`#7955 <https://github.com/readthedocs/readthedocs.org/pull/7955>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: make --queue required for management command (`#7952 <https://github.com/readthedocs/readthedocs.org/pull/7952>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add proxito healthcheck (`#7948 <https://github.com/readthedocs/readthedocs.org/pull/7948>`__)
* `@Pradhvan <https://github.com/Pradhvan>`__: Docs: Adds Myst to the getting started with sphinx (`#7938 <https://github.com/readthedocs/readthedocs.org/pull/7938>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add a support form to the website (`#7929 <https://github.com/readthedocs/readthedocs.org/pull/7929>`__)
* `@humitos <https://github.com/humitos>`__: Use Stripe Checkout for Gold Users (`#7889 <https://github.com/readthedocs/readthedocs.org/pull/7889>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: guide about reproducible builds (`#7888 <https://github.com/readthedocs/readthedocs.org/pull/7888>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: update links from build images (`#7886 <https://github.com/readthedocs/readthedocs.org/pull/7886>`__)
* `@stsewd <https://github.com/stsewd>`__: Install latest mkdocs by default as we do with sphinx (`#7869 <https://github.com/readthedocs/readthedocs.org/pull/7869>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: document analytics (`#7857 <https://github.com/readthedocs/readthedocs.org/pull/7857>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove some feature flags (`#7846 <https://github.com/readthedocs/readthedocs.org/pull/7846>`__)
* `@stsewd <https://github.com/stsewd>`__: Update requirements/deploy.txt (`#7843 <https://github.com/readthedocs/readthedocs.org/pull/7843>`__)
* `@humitos <https://github.com/humitos>`__: Implementation of APIv3 (`#4863 <https://github.com/readthedocs/readthedocs.org/pull/4863>`__)

Version 5.11.0
--------------

:Date: March 02, 2021

* `@saadmk11 <https://github.com/saadmk11>`__: Add management command to Load Project and RemoteRepository Relationship from JSON file (`#7966 <https://github.com/readthedocs/readthedocs.org/pull/7966>`__)
* `@humitos <https://github.com/humitos>`__: Lower rank of development/install.html (`#7960 <https://github.com/readthedocs/readthedocs.org/pull/7960>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Add Management Command to Dump Project and RemoteRepository Relationship in JSON format (`#7957 <https://github.com/readthedocs/readthedocs.org/pull/7957>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Enable the cached template loader (`#7953 <https://github.com/readthedocs/readthedocs.org/pull/7953>`__)
* `@stsewd <https://github.com/stsewd>`__: Update common to master (`#7951 <https://github.com/readthedocs/readthedocs.org/pull/7951>`__)
* `@stsewd <https://github.com/stsewd>`__: Embed: refactor tests (`#7947 <https://github.com/readthedocs/readthedocs.org/pull/7947>`__)
* `@stsewd <https://github.com/stsewd>`__: Downgrade jedi (`#7946 <https://github.com/readthedocs/readthedocs.org/pull/7946>`__)
* `@FatGrizzly <https://github.com/FatGrizzly>`__: Added warnings for previous gitbook users (`#7945 <https://github.com/readthedocs/readthedocs.org/pull/7945>`__)
* `@stsewd <https://github.com/stsewd>`__: Move embed app (`#7943 <https://github.com/readthedocs/readthedocs.org/pull/7943>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Change our sponsored hosting from Azure -> AWS. (`#7940 <https://github.com/readthedocs/readthedocs.org/pull/7940>`__)
* `@Pradhvan <https://github.com/Pradhvan>`__: Docs: Adds Myst to the getting started with sphinx (`#7938 <https://github.com/readthedocs/readthedocs.org/pull/7938>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add a support form to the website (`#7929 <https://github.com/readthedocs/readthedocs.org/pull/7929>`__)
* `@stsewd <https://github.com/stsewd>`__: Drop six (`#7890 <https://github.com/readthedocs/readthedocs.org/pull/7890>`__)
* `@fabianmp <https://github.com/fabianmp>`__: Allow to use a different url for intersphinx object file download (`#7807 <https://github.com/readthedocs/readthedocs.org/pull/7807>`__)

Version 5.10.0
--------------

:Date: February 23, 2021

* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 08 (`#7941 <https://github.com/readthedocs/readthedocs.org/pull/7941>`__)
* `@PawelBorkar <https://github.com/PawelBorkar>`__: Update license (`#7934 <https://github.com/readthedocs/readthedocs.org/pull/7934>`__)
* `@humitos <https://github.com/humitos>`__: Route external versions to the queue were default version was built (`#7933 <https://github.com/readthedocs/readthedocs.org/pull/7933>`__)
* `@humitos <https://github.com/humitos>`__: Pin jedi dependency to avoid breaking ipython (`#7932 <https://github.com/readthedocs/readthedocs.org/pull/7932>`__)
* `@humitos <https://github.com/humitos>`__: Use `admin` user for SLUMBER API on local environment (`#7925 <https://github.com/readthedocs/readthedocs.org/pull/7925>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: add cache tags (`#7922 <https://github.com/readthedocs/readthedocs.org/pull/7922>`__)
* `@humitos <https://github.com/humitos>`__: Use S3 from community (`#7920 <https://github.com/readthedocs/readthedocs.org/pull/7920>`__)
* `@stsewd <https://github.com/stsewd>`__: Use only one variant of the config file (`#7918 <https://github.com/readthedocs/readthedocs.org/pull/7918>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 07 (`#7913 <https://github.com/readthedocs/readthedocs.org/pull/7913>`__)
* `@humitos <https://github.com/humitos>`__: Router PRs builds to last queue where a build was executed (`#7912 <https://github.com/readthedocs/readthedocs.org/pull/7912>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: improve re-index management command (`#7904 <https://github.com/readthedocs/readthedocs.org/pull/7904>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: link to main project in subproject results (`#7880 <https://github.com/readthedocs/readthedocs.org/pull/7880>`__)
* `@humitos <https://github.com/humitos>`__: Upgrade Celery and friends to latest versions (`#7786 <https://github.com/readthedocs/readthedocs.org/pull/7786>`__)

Version 5.9.0
-------------

:Date: February 16, 2021

Last Friday we migrated our site from Azure to AWS (`read the blog post <https://blog.readthedocs.com/aws-migration/>`_).
This is the first release into our new AWS infra.

* `@humitos <https://github.com/humitos>`__: Router PRs builds to last queue where a build was executed (`#7912 <https://github.com/readthedocs/readthedocs.org/pull/7912>`__)
* `@humitos <https://github.com/humitos>`__: Update common/ submodule (`#7910 <https://github.com/readthedocs/readthedocs.org/pull/7910>`__)
* `@humitos <https://github.com/humitos>`__: Upgrade Redis version to match production (`#7909 <https://github.com/readthedocs/readthedocs.org/pull/7909>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Make storage classes into module level vars (`#7908 <https://github.com/readthedocs/readthedocs.org/pull/7908>`__)
* `@csdev <https://github.com/csdev>`__: fix typo (`#7902 <https://github.com/readthedocs/readthedocs.org/pull/7902>`__)
* `@humitos <https://github.com/humitos>`__: Match Redis version from AWS producion (`#7897 <https://github.com/readthedocs/readthedocs.org/pull/7897>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 06 (`#7896 <https://github.com/readthedocs/readthedocs.org/pull/7896>`__)
* `@nedbat <https://github.com/nedbat>`__: Doc fix: two endpoints had 'pip' for the project_slug (`#7895 <https://github.com/readthedocs/readthedocs.org/pull/7895>`__)
* `@stsewd <https://github.com/stsewd>`__: Set storage for BuildCommand and BuildEnvironment as private (`#7893 <https://github.com/readthedocs/readthedocs.org/pull/7893>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 05 (`#7887 <https://github.com/readthedocs/readthedocs.org/pull/7887>`__)
* `@humitos <https://github.com/humitos>`__: Add support for Python 3.9 on "testing" Docker image (`#7885 <https://github.com/readthedocs/readthedocs.org/pull/7885>`__)
* `@stsewd <https://github.com/stsewd>`__: Add version_changed signal (`#7878 <https://github.com/readthedocs/readthedocs.org/pull/7878>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: don't index permalinks (`#7876 <https://github.com/readthedocs/readthedocs.org/pull/7876>`__)
* `@stsewd <https://github.com/stsewd>`__: Update common (`#7873 <https://github.com/readthedocs/readthedocs.org/pull/7873>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 04 (`#7867 <https://github.com/readthedocs/readthedocs.org/pull/7867>`__)
* `@humitos <https://github.com/humitos>`__: Log Stripe errors when trying to delete customer/subscription (`#7853 <https://github.com/readthedocs/readthedocs.org/pull/7853>`__)
* `@humitos <https://github.com/humitos>`__: Save builder when the build is concurrency limited (`#7851 <https://github.com/readthedocs/readthedocs.org/pull/7851>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove some feature flags (`#7846 <https://github.com/readthedocs/readthedocs.org/pull/7846>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix conf.py for external versions (`#7845 <https://github.com/readthedocs/readthedocs.org/pull/7845>`__)
* `@humitos <https://github.com/humitos>`__: Metric tasks for community (`#7841 <https://github.com/readthedocs/readthedocs.org/pull/7841>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 03 (`#7840 <https://github.com/readthedocs/readthedocs.org/pull/7840>`__)
* `@humitos <https://github.com/humitos>`__: Speed up concurrent builds by limited to 5 hours ago (`#7839 <https://github.com/readthedocs/readthedocs.org/pull/7839>`__)
* `@humitos <https://github.com/humitos>`__: Match Redis version with production (`#7838 <https://github.com/readthedocs/readthedocs.org/pull/7838>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Add Option to Enable External Builds Through Project Update API (`#7834 <https://github.com/readthedocs/readthedocs.org/pull/7834>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: mention the version warning is for sphinx only (`#7832 <https://github.com/readthedocs/readthedocs.org/pull/7832>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Hide design docs from documentation (`#7826 <https://github.com/readthedocs/readthedocs.org/pull/7826>`__)
* `@stsewd <https://github.com/stsewd>`__: Update docs about preview from pull/merge requests (`#7823 <https://github.com/readthedocs/readthedocs.org/pull/7823>`__)
* `@humitos <https://github.com/humitos>`__: Register MetricsTask to send metrics to AWS CloudWatch (`#7817 <https://github.com/readthedocs/readthedocs.org/pull/7817>`__)
* `@humitos <https://github.com/humitos>`__: Use S3 (MinIO emulator) as storage backend (`#7812 <https://github.com/readthedocs/readthedocs.org/pull/7812>`__)
* `@zachdeibert <https://github.com/zachdeibert>`__: Cloudflare to Cloudflare CNAME Records (`#7801 <https://github.com/readthedocs/readthedocs.org/pull/7801>`__)
* `@humitos <https://github.com/humitos>`__: Documentation for `/organizations/` endpoint in commercial (`#7800 <https://github.com/readthedocs/readthedocs.org/pull/7800>`__)
* `@stsewd <https://github.com/stsewd>`__: Privacy Levels: migrate protected projects to private (`#7608 <https://github.com/readthedocs/readthedocs.org/pull/7608>`__)
* `@pawamoy <https://github.com/pawamoy>`__: Don't lose python/name tags values in mkdocs.yml (`#7507 <https://github.com/readthedocs/readthedocs.org/pull/7507>`__)
* `@stsewd <https://github.com/stsewd>`__: Install latest version of setuptools (`#7290 <https://github.com/readthedocs/readthedocs.org/pull/7290>`__)
* `@humitos <https://github.com/humitos>`__: Implementation of APIv3 (`#4863 <https://github.com/readthedocs/readthedocs.org/pull/4863>`__)

Version 5.8.5
-------------

:Date: January 18, 2021

* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 03 (`#7840 <https://github.com/readthedocs/readthedocs.org/pull/7840>`__)
* `@humitos <https://github.com/humitos>`__: Speed up concurrent builds by limited to 5 hours ago (`#7839 <https://github.com/readthedocs/readthedocs.org/pull/7839>`__)
* `@humitos <https://github.com/humitos>`__: Match Redis version with production (`#7838 <https://github.com/readthedocs/readthedocs.org/pull/7838>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Add Option to Enable External Builds Through Project Update API (`#7834 <https://github.com/readthedocs/readthedocs.org/pull/7834>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: mention the version warning is for sphinx only (`#7832 <https://github.com/readthedocs/readthedocs.org/pull/7832>`__)
* `@stsewd <https://github.com/stsewd>`__: Tests: make PRODUCTION_DOMAIN explicit (`#7831 <https://github.com/readthedocs/readthedocs.org/pull/7831>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: make it easy to copy/pasta examples (`#7829 <https://github.com/readthedocs/readthedocs.org/pull/7829>`__)
* `@stsewd <https://github.com/stsewd>`__: PR preview: pass PR and build urls to sphinx context (`#7828 <https://github.com/readthedocs/readthedocs.org/pull/7828>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Hide design docs from documentation (`#7826 <https://github.com/readthedocs/readthedocs.org/pull/7826>`__)
* `@stsewd <https://github.com/stsewd>`__: Footer: add cache tags (`#7821 <https://github.com/readthedocs/readthedocs.org/pull/7821>`__)
* `@humitos <https://github.com/humitos>`__: Log Stripe Resource fallback creation in Sentry (`#7820 <https://github.com/readthedocs/readthedocs.org/pull/7820>`__)
* `@humitos <https://github.com/humitos>`__: Register MetricsTask to send metrics to AWS CloudWatch (`#7817 <https://github.com/readthedocs/readthedocs.org/pull/7817>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Add management command to Sync RemoteRepositories and RemoteOrganizations (`#7803 <https://github.com/readthedocs/readthedocs.org/pull/7803>`__)
* `@stsewd <https://github.com/stsewd>`__: Mkdocs: default to "docs" for docs_dir (`#7766 <https://github.com/readthedocs/readthedocs.org/pull/7766>`__)

Version 5.8.4
-------------

:Date: January 12, 2021

* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 02 (`#7818 <https://github.com/readthedocs/readthedocs.org/pull/7818>`__)
* `@stsewd <https://github.com/stsewd>`__: List SYNC_VERSIONS_USING_A_TASK flag in the admin (`#7802 <https://github.com/readthedocs/readthedocs.org/pull/7802>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Update build concurrency numbers for Business (`#7794 <https://github.com/readthedocs/readthedocs.org/pull/7794>`__)
* `@stsewd <https://github.com/stsewd>`__: Sphinx: use html_baseurl for setting the canonical URL (`#7540 <https://github.com/readthedocs/readthedocs.org/pull/7540>`__)

Version 5.8.3
-------------

:Date: January 05, 2021

* `@humitos <https://github.com/humitos>`__: Change query on `send_build_status` task for compatibility with .com (`#7797 <https://github.com/readthedocs/readthedocs.org/pull/7797>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Update build concurrency numbers for Business (`#7794 <https://github.com/readthedocs/readthedocs.org/pull/7794>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 01 (`#7793 <https://github.com/readthedocs/readthedocs.org/pull/7793>`__)
* `@timgates42 <https://github.com/timgates42>`__: docs: fix simple typo, -> translations (`#7781 <https://github.com/readthedocs/readthedocs.org/pull/7781>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 5.8.2 (`#7776 <https://github.com/readthedocs/readthedocs.org/pull/7776>`__)
* `@humitos <https://github.com/humitos>`__: Use Python3.7 on conda base environment when using mamba (`#7773 <https://github.com/readthedocs/readthedocs.org/pull/7773>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove domain verify signal and task (`#7763 <https://github.com/readthedocs/readthedocs.org/pull/7763>`__)
* `@stsewd <https://github.com/stsewd>`__: Import page: fix wizard form (`#7702 <https://github.com/readthedocs/readthedocs.org/pull/7702>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Migrate sync_versions from an API call to a task (`#7548 <https://github.com/readthedocs/readthedocs.org/pull/7548>`__)
* `@humitos <https://github.com/humitos>`__: Design document for RemoteRepository DB normalization (`#7169 <https://github.com/readthedocs/readthedocs.org/pull/7169>`__)

Version 5.8.2
-------------

:Date: December 21, 2020

* `@humitos <https://github.com/humitos>`__: Use Python3.7 on conda base environment when using mamba (`#7773 <https://github.com/readthedocs/readthedocs.org/pull/7773>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove domain verify signal and task (`#7763 <https://github.com/readthedocs/readthedocs.org/pull/7763>`__)
* `@humitos <https://github.com/humitos>`__: Register StopBuilder task to be executed by builders (`#7759 <https://github.com/readthedocs/readthedocs.org/pull/7759>`__)
* `@stsewd <https://github.com/stsewd>`__: Footer: remove absolute_uri (`#7758 <https://github.com/readthedocs/readthedocs.org/pull/7758>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: use alias to link to search results of subprojects (`#7757 <https://github.com/readthedocs/readthedocs.org/pull/7757>`__)
* `@stsewd <https://github.com/stsewd>`__: Footer: remove jsonp call (`#7756 <https://github.com/readthedocs/readthedocs.org/pull/7756>`__)
* `@humitos <https://github.com/humitos>`__: Register AutoscaleBuildersTask (`#7755 <https://github.com/readthedocs/readthedocs.org/pull/7755>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Set The Right Permissions on GitLab OAuth RemoteRepository (`#7753 <https://github.com/readthedocs/readthedocs.org/pull/7753>`__)
* `@stsewd <https://github.com/stsewd>`__: Use lru_cache for caching methods (`#7751 <https://github.com/readthedocs/readthedocs.org/pull/7751>`__)
* `@fabianmp <https://github.com/fabianmp>`__: Allow to add additional binds to Docker build container (`#7684 <https://github.com/readthedocs/readthedocs.org/pull/7684>`__)

Version 5.8.1
-------------

:Date: December 14, 2020

* `@humitos <https://github.com/humitos>`__: Register ShutdownBuilder task (`#7749 <https://github.com/readthedocs/readthedocs.org/pull/7749>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Use "path_with_namespace" for GitLab RemoteRepository full_name Field (`#7746 <https://github.com/readthedocs/readthedocs.org/pull/7746>`__)
* `@stsewd <https://github.com/stsewd>`__: Features: remove USE_NEW_PIP_RESOLVER (`#7745 <https://github.com/readthedocs/readthedocs.org/pull/7745>`__)
* `@stsewd <https://github.com/stsewd>`__: Version sync: exclude external versions when deleting (`#7742 <https://github.com/readthedocs/readthedocs.org/pull/7742>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: limit number of sections and domains to 10K (`#7741 <https://github.com/readthedocs/readthedocs.org/pull/7741>`__)
* `@stsewd <https://github.com/stsewd>`__: Traffic analytics: don't pass context if the feature isn't enabled (`#7740 <https://github.com/readthedocs/readthedocs.org/pull/7740>`__)
* `@stsewd <https://github.com/stsewd>`__: Analytics: move page views to its own endpoint (`#7739 <https://github.com/readthedocs/readthedocs.org/pull/7739>`__)
* `@stsewd <https://github.com/stsewd>`__: FeatureQuerySet: make check for date inclusive (`#7737 <https://github.com/readthedocs/readthedocs.org/pull/7737>`__)
* `@stsewd <https://github.com/stsewd>`__: Typo: date -> data (`#7736 <https://github.com/readthedocs/readthedocs.org/pull/7736>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Use remote_id and vcs_provider Instead of full_name to Get RemoteRepository (`#7734 <https://github.com/readthedocs/readthedocs.org/pull/7734>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 49 (`#7730 <https://github.com/readthedocs/readthedocs.org/pull/7730>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Update parts of code that were using the old RemoteRepository model fields (`#7728 <https://github.com/readthedocs/readthedocs.org/pull/7728>`__)
* `@stsewd <https://github.com/stsewd>`__: Builds: don't delete them when a version is deleted (`#7679 <https://github.com/readthedocs/readthedocs.org/pull/7679>`__)
* `@stsewd <https://github.com/stsewd>`__: Sync versions: create new versions in bulk (`#7382 <https://github.com/readthedocs/readthedocs.org/pull/7382>`__)
* `@humitos <https://github.com/humitos>`__: Use `mamba` under a feature flag to create conda environments (`#6815 <https://github.com/readthedocs/readthedocs.org/pull/6815>`__)

Version 5.8.0
-------------

:Date: December 08, 2020

* `@stsewd <https://github.com/stsewd>`__: Update common (`#7731 <https://github.com/readthedocs/readthedocs.org/pull/7731>`__)
* `@stsewd <https://github.com/stsewd>`__: Bitbucket: mainbranch can be None (`#7725 <https://github.com/readthedocs/readthedocs.org/pull/7725>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: use with_positions_offsets term vector for some fields (`#7724 <https://github.com/readthedocs/readthedocs.org/pull/7724>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: filter only active and built versions from subprojects (`#7723 <https://github.com/readthedocs/readthedocs.org/pull/7723>`__)
* `@stsewd <https://github.com/stsewd>`__: Extra features: allow to display them conditionally (`#7715 <https://github.com/readthedocs/readthedocs.org/pull/7715>`__)
* `@humitos <https://github.com/humitos>`__: Define `pre/post_collectstatic` signals and send them (`#7701 <https://github.com/readthedocs/readthedocs.org/pull/7701>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Support the new Google analytics gtag.js (`#7691 <https://github.com/readthedocs/readthedocs.org/pull/7691>`__)
* `@stsewd <https://github.com/stsewd>`__: HTMLFile: remove slug field (`#7680 <https://github.com/readthedocs/readthedocs.org/pull/7680>`__)
* `@stsewd <https://github.com/stsewd>`__: External versions: delete after 3 months of being merged/closed (`#7678 <https://github.com/readthedocs/readthedocs.org/pull/7678>`__)
* `@stsewd <https://github.com/stsewd>`__: Automation Rules: keep history of recent matches (`#7658 <https://github.com/readthedocs/readthedocs.org/pull/7658>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: update to ES 7.x (`#7582 <https://github.com/readthedocs/readthedocs.org/pull/7582>`__)

Version 5.7.0
-------------

:Date: December 01, 2020

* `@davidfischer <https://github.com/davidfischer>`__: Ensure there is space for sidebar ads (`#7716 <https://github.com/readthedocs/readthedocs.org/pull/7716>`__)
* `@humitos <https://github.com/humitos>`__: Install six as core requirement for builds (`#7710 <https://github.com/readthedocs/readthedocs.org/pull/7710>`__)
* `@stsewd <https://github.com/stsewd>`__: Features: increase feature_id max_length (`#7698 <https://github.com/readthedocs/readthedocs.org/pull/7698>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 5.6.1 (`#7695 <https://github.com/readthedocs/readthedocs.org/pull/7695>`__)
* `@stsewd <https://github.com/stsewd>`__: Tests: mock trigger_build (`#7681 <https://github.com/readthedocs/readthedocs.org/pull/7681>`__)
* `@stsewd <https://github.com/stsewd>`__: Sync versions: use stable version instead of querying all versions (`#7380 <https://github.com/readthedocs/readthedocs.org/pull/7380>`__)

Version 5.6.5
-------------

:Date: November 23, 2020

* `@stsewd <https://github.com/stsewd>`__: Tests: mock trigger_build (`#7681 <https://github.com/readthedocs/readthedocs.org/pull/7681>`__)
* `@stsewd <https://github.com/stsewd>`__: Tests: mock update_docs_task to speed up tests (`#7677 <https://github.com/readthedocs/readthedocs.org/pull/7677>`__)
* `@stsewd <https://github.com/stsewd>`__: Versions: add timestamp fields (`#7676 <https://github.com/readthedocs/readthedocs.org/pull/7676>`__)
* `@stsewd <https://github.com/stsewd>`__: Tests: create an organization when running in .com (`#7673 <https://github.com/readthedocs/readthedocs.org/pull/7673>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Speed up the tag index page (`#7671 <https://github.com/readthedocs/readthedocs.org/pull/7671>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Fix for out of order script loading (`#7670 <https://github.com/readthedocs/readthedocs.org/pull/7670>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Set ad configuration values if using explicit placement (`#7669 <https://github.com/readthedocs/readthedocs.org/pull/7669>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 46 (`#7668 <https://github.com/readthedocs/readthedocs.org/pull/7668>`__)
* `@stsewd <https://github.com/stsewd>`__: Tests: mock trigger build to speed up tests (`#7661 <https://github.com/readthedocs/readthedocs.org/pull/7661>`__)
* `@stsewd <https://github.com/stsewd>`__: Remote repository: save and set default_branch (`#7646 <https://github.com/readthedocs/readthedocs.org/pull/7646>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: exclude some fields from source results (`#7640 <https://github.com/readthedocs/readthedocs.org/pull/7640>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: allow to search on different versions of subprojects (`#7634 <https://github.com/readthedocs/readthedocs.org/pull/7634>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: refactor api view (`#7633 <https://github.com/readthedocs/readthedocs.org/pull/7633>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Add Initial Modeling with Through Model and Data Migration for RemoteRepository Model (`#7536 <https://github.com/readthedocs/readthedocs.org/pull/7536>`__)
* `@stsewd <https://github.com/stsewd>`__: ImportedFile: remove slug 1/2 (`#7228 <https://github.com/readthedocs/readthedocs.org/pull/7228>`__)
* `@humitos <https://github.com/humitos>`__: Changes required for APIv3 in corporate (`#6489 <https://github.com/readthedocs/readthedocs.org/pull/6489>`__)

Version 5.6.4
-------------

:Date: November 16, 2020

* `@davidfischer <https://github.com/davidfischer>`__: Fix for out of order script loading (`#7670 <https://github.com/readthedocs/readthedocs.org/pull/7670>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Set ad configuration values if using explicit placement (`#7669 <https://github.com/readthedocs/readthedocs.org/pull/7669>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 46 (`#7668 <https://github.com/readthedocs/readthedocs.org/pull/7668>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 45 (`#7655 <https://github.com/readthedocs/readthedocs.org/pull/7655>`__)
* `@stsewd <https://github.com/stsewd>`__: Automation rules: add delete version action (`#7644 <https://github.com/readthedocs/readthedocs.org/pull/7644>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: exclude some fields from source results (`#7640 <https://github.com/readthedocs/readthedocs.org/pull/7640>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Add Initial Modeling with Through Model and Data Migration for RemoteRepository Model (`#7536 <https://github.com/readthedocs/readthedocs.org/pull/7536>`__)
* `@humitos <https://github.com/humitos>`__: Changes required for APIv3 in corporate (`#6489 <https://github.com/readthedocs/readthedocs.org/pull/6489>`__)

Version 5.6.3
-------------

:Date: November 10, 2020

* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 43 (`#7602 <https://github.com/readthedocs/readthedocs.org/pull/7602>`__)

Version 5.6.2
-------------

:Date: November 03, 2020

* `@humitos <https://github.com/humitos>`__: Check only for override settings (part 2) (`#7630 <https://github.com/readthedocs/readthedocs.org/pull/7630>`__)
* `@humitos <https://github.com/humitos>`__: Check only override settings (`#7628 <https://github.com/readthedocs/readthedocs.org/pull/7628>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Display sidebar ad when scrolled (`#7621 <https://github.com/readthedocs/readthedocs.org/pull/7621>`__)
* `@humitos <https://github.com/humitos>`__: Reserve 1Gb for Application Memory (`#7618 <https://github.com/readthedocs/readthedocs.org/pull/7618>`__)
* `@humitos <https://github.com/humitos>`__: Catch `requests.exceptions.ReadTimeout` when removing container (`#7617 <https://github.com/readthedocs/readthedocs.org/pull/7617>`__)
* `@humitos <https://github.com/humitos>`__: Allow search and filter in Django Admin for Message model (`#7615 <https://github.com/readthedocs/readthedocs.org/pull/7615>`__)
* `@stsewd <https://github.com/stsewd>`__: CI: use badge from circleci (`#7614 <https://github.com/readthedocs/readthedocs.org/pull/7614>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: respect feature flag in dashboard search (`#7611 <https://github.com/readthedocs/readthedocs.org/pull/7611>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 5.6.1 (`#7604 <https://github.com/readthedocs/readthedocs.org/pull/7604>`__)
* `@stsewd <https://github.com/stsewd>`__: CI: use circleci (`#7603 <https://github.com/readthedocs/readthedocs.org/pull/7603>`__)


Version 5.6.1
-------------

:Date: October 26, 2020

* `@agjohnson <https://github.com/agjohnson>`__: Bump common to include docker task changes (`#7597 <https://github.com/readthedocs/readthedocs.org/pull/7597>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Default to sphinx theme 0.5.0 when defaulting to latest sphinx (`#7596 <https://github.com/readthedocs/readthedocs.org/pull/7596>`__)
* `@humitos <https://github.com/humitos>`__: Use correct Cache-Tag (CDN) and X-RTD-Project header on subprojects (`#7593 <https://github.com/readthedocs/readthedocs.org/pull/7593>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Ads JS hotfix (`#7586 <https://github.com/readthedocs/readthedocs.org/pull/7586>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Add remoterepo query param (`#7580 <https://github.com/readthedocs/readthedocs.org/pull/7580>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Undeprecate APIv2 in docs (`#7579 <https://github.com/readthedocs/readthedocs.org/pull/7579>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Add settings and docker configuration for working with new theme (`#7578 <https://github.com/readthedocs/readthedocs.org/pull/7578>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: exclude chagelog from results (`#7570 <https://github.com/readthedocs/readthedocs.org/pull/7570>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: better results for single terms (`#7569 <https://github.com/readthedocs/readthedocs.org/pull/7569>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: refactor query objects (`#7568 <https://github.com/readthedocs/readthedocs.org/pull/7568>`__)
* `@humitos <https://github.com/humitos>`__: Add our `readthedocs_processor` data to our notifications (`#7565 <https://github.com/readthedocs/readthedocs.org/pull/7565>`__)
* `@stsewd <https://github.com/stsewd>`__: Update ES to 6.8.12 (`#7559 <https://github.com/readthedocs/readthedocs.org/pull/7559>`__)
* `@stsewd <https://github.com/stsewd>`__: Builds: always install latest version of our sphinx extension (`#7542 <https://github.com/readthedocs/readthedocs.org/pull/7542>`__)
* `@stsewd <https://github.com/stsewd>`__: Bring back project privacy level (`#7525 <https://github.com/readthedocs/readthedocs.org/pull/7525>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add future default true to Feature flags (`#7524 <https://github.com/readthedocs/readthedocs.org/pull/7524>`__)
* `@stsewd <https://github.com/stsewd>`__: Add feature flag to not install the latest version of pip (`#7522 <https://github.com/readthedocs/readthedocs.org/pull/7522>`__)
* `@davidfischer <https://github.com/davidfischer>`__: No longer proxy RTD ads through RTD servers (`#7506 <https://github.com/readthedocs/readthedocs.org/pull/7506>`__)
* `@stsewd <https://github.com/stsewd>`__: Subprojects: fix form (`#7491 <https://github.com/readthedocs/readthedocs.org/pull/7491>`__)
* `@AvdN <https://github.com/AvdN>`__: correct inconsistent indentation of YAML (`#7459 <https://github.com/readthedocs/readthedocs.org/pull/7459>`__)

Version 5.6.0
-------------

:Date: October 19, 2020

* `@stsewd <https://github.com/stsewd>`__: Search: exclude chagelog from results (`#7570 <https://github.com/readthedocs/readthedocs.org/pull/7570>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: show example of a requirements.txt file (`#7563 <https://github.com/readthedocs/readthedocs.org/pull/7563>`__)
* `@stsewd <https://github.com/stsewd>`__: Update ES to 6.8.12 (`#7559 <https://github.com/readthedocs/readthedocs.org/pull/7559>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 40 (`#7537 <https://github.com/readthedocs/readthedocs.org/pull/7537>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add future default true to Feature flags (`#7524 <https://github.com/readthedocs/readthedocs.org/pull/7524>`__)
* `@davidfischer <https://github.com/davidfischer>`__: No longer proxy RTD ads through RTD servers (`#7506 <https://github.com/readthedocs/readthedocs.org/pull/7506>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Allow projects to opt-out of analytics (`#7175 <https://github.com/readthedocs/readthedocs.org/pull/7175>`__)

Version 5.5.3
-------------

:Date: October 13, 2020

* `@ericholscher <https://github.com/ericholscher>`__: Add a reference to the Import guide at the start of Getting started (`#7547 <https://github.com/readthedocs/readthedocs.org/pull/7547>`__)
* `@kuzmoyev <https://github.com/kuzmoyev>`__: Include month-ago day to traffic data (`#7545 <https://github.com/readthedocs/readthedocs.org/pull/7545>`__)
* `@stsewd <https://github.com/stsewd>`__: Downloads: fix translation of a subproject (`#7541 <https://github.com/readthedocs/readthedocs.org/pull/7541>`__)
* `@stsewd <https://github.com/stsewd>`__: Domains: more robust form (`#7523 <https://github.com/readthedocs/readthedocs.org/pull/7523>`__)
* `@stsewd <https://github.com/stsewd>`__: Revert "Revert ES: update dependencies" (`#7439 <https://github.com/readthedocs/readthedocs.org/pull/7439>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: remove old endpoint (`#7414 <https://github.com/readthedocs/readthedocs.org/pull/7414>`__)

Version 5.5.2
-------------

:Date: October 06, 2020

* `@stsewd <https://github.com/stsewd>`__: Domain: show created/modified date in admin (`#7517 <https://github.com/readthedocs/readthedocs.org/pull/7517>`__)
* `@stsewd <https://github.com/stsewd>`__: Tests: fix eslint (`#7516 <https://github.com/readthedocs/readthedocs.org/pull/7516>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Revert "New docker image for builders: 8.0" (`#7514 <https://github.com/readthedocs/readthedocs.org/pull/7514>`__)
* `@srijan-deepsource <https://github.com/srijan-deepsource>`__: Fix some code quality issues (`#7494 <https://github.com/readthedocs/readthedocs.org/pull/7494>`__)

Version 5.5.1
-------------

:Date: September 28, 2020

* `@stsewd <https://github.com/stsewd>`__: Domain: fix form (`#7502 <https://github.com/readthedocs/readthedocs.org/pull/7502>`__)
* `@stsewd <https://github.com/stsewd>`__: Builders: little refactor (`#7500 <https://github.com/readthedocs/readthedocs.org/pull/7500>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add proper div names on our ad placements (`#7493 <https://github.com/readthedocs/readthedocs.org/pull/7493>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: APIv3 Version list slug filter added (`#7372 <https://github.com/readthedocs/readthedocs.org/pull/7372>`__)
* `@humitos <https://github.com/humitos>`__: Use "-j auto" on sphinx-build command to build in parallel (`#7128 <https://github.com/readthedocs/readthedocs.org/pull/7128>`__)

Version 5.5.0
-------------

:Date: September 22, 2020

* `@stsewd <https://github.com/stsewd>`__: Don't install pygments (`#7490 <https://github.com/readthedocs/readthedocs.org/pull/7490>`__)
* `@humitos <https://github.com/humitos>`__: Limit concurrency per-organization (`#7489 <https://github.com/readthedocs/readthedocs.org/pull/7489>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 37 (`#7482 <https://github.com/readthedocs/readthedocs.org/pull/7482>`__)
* `@humitos <https://github.com/humitos>`__: Use `permissions` (project and group) for `RemoteRepository.admin` on GitLab (`#7479 <https://github.com/readthedocs/readthedocs.org/pull/7479>`__)

Version 5.4.3
-------------

:Date: September 15, 2020

* `@stsewd <https://github.com/stsewd>`__: Domain: inherit from TimeStampedModel (`#7476 <https://github.com/readthedocs/readthedocs.org/pull/7476>`__)
* `@stsewd <https://github.com/stsewd>`__: Truncate output at the start for large commands (`#7473 <https://github.com/readthedocs/readthedocs.org/pull/7473>`__)
* `@stsewd <https://github.com/stsewd>`__: Add dependency explicitly (dateutil) (`#7415 <https://github.com/readthedocs/readthedocs.org/pull/7415>`__)
* `@stsewd <https://github.com/stsewd>`__: Domains: add ssl_status field (`#7398 <https://github.com/readthedocs/readthedocs.org/pull/7398>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: allow ignoring files from indexing (`#7308 <https://github.com/readthedocs/readthedocs.org/pull/7308>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: SSS integration guide (`#7232 <https://github.com/readthedocs/readthedocs.org/pull/7232>`__)

Version 5.4.2
-------------

:Date: September 09, 2020

* `@humitos <https://github.com/humitos>`__: Show "Connected Services" form errors to the user (`#7469 <https://github.com/readthedocs/readthedocs.org/pull/7469>`__)
* `@humitos <https://github.com/humitos>`__: Allow to extend OrganizationTeamBasicForm from -corporate (`#7467 <https://github.com/readthedocs/readthedocs.org/pull/7467>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 36 (`#7465 <https://github.com/readthedocs/readthedocs.org/pull/7465>`__)
* `@AvdN <https://github.com/AvdN>`__: correct invalid YAML (`#7458 <https://github.com/readthedocs/readthedocs.org/pull/7458>`__)
* `@stsewd <https://github.com/stsewd>`__: Remote repository: filter by account before deleting (`#7454 <https://github.com/readthedocs/readthedocs.org/pull/7454>`__)
* `@humitos <https://github.com/humitos>`__: Truncate the beginning of the commands' output (`#7449 <https://github.com/readthedocs/readthedocs.org/pull/7449>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Update links to advertising (`#7443 <https://github.com/readthedocs/readthedocs.org/pull/7443>`__)
* `@stsewd <https://github.com/stsewd>`__: Revert "Don't retry on POST" (`#7442 <https://github.com/readthedocs/readthedocs.org/pull/7442>`__)
* `@stsewd <https://github.com/stsewd>`__: Organizations: move signals (`#7441 <https://github.com/readthedocs/readthedocs.org/pull/7441>`__)
* `@stsewd <https://github.com/stsewd>`__: Organizations: move forms (`#7438 <https://github.com/readthedocs/readthedocs.org/pull/7438>`__)
* `@humitos <https://github.com/humitos>`__: Grab the correct name of RemoteOrganization to use in the query (`#7430 <https://github.com/readthedocs/readthedocs.org/pull/7430>`__)
* `@stsewd <https://github.com/stsewd>`__: Revert "ES: update dependencies" (`#7429 <https://github.com/readthedocs/readthedocs.org/pull/7429>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 35 (`#7423 <https://github.com/readthedocs/readthedocs.org/pull/7423>`__)
* `@humitos <https://github.com/humitos>`__: Mark a build as DUPLICATED (same version) only it's close in time (`#7420 <https://github.com/readthedocs/readthedocs.org/pull/7420>`__)

Version 5.4.1
-------------

:Date: September 01, 2020

* `@stsewd <https://github.com/stsewd>`__: Docs: update readthedcos-sphinx-search ext (`#7427 <https://github.com/readthedocs/readthedocs.org/pull/7427>`__)
* `@humitos <https://github.com/humitos>`__: Upgrade Django to 2.2.16 (`#7426 <https://github.com/readthedocs/readthedocs.org/pull/7426>`__)
* `@bmorrison4 <https://github.com/bmorrison4>`__: Fix typo in docs/guides/adding-custom-css.rst (`#7424 <https://github.com/readthedocs/readthedocs.org/pull/7424>`__)
* `@stsewd <https://github.com/stsewd>`__: Test: set privacy level explicitly (`#7422 <https://github.com/readthedocs/readthedocs.org/pull/7422>`__)
* `@stsewd <https://github.com/stsewd>`__: Pip: test new resolver (`#7412 <https://github.com/readthedocs/readthedocs.org/pull/7412>`__)
* `@stsewd <https://github.com/stsewd>`__: Update common (`#7411 <https://github.com/readthedocs/readthedocs.org/pull/7411>`__)
* `@stsewd <https://github.com/stsewd>`__: Release 5.4.0 (`#7410 <https://github.com/readthedocs/readthedocs.org/pull/7410>`__)
* `@stsewd <https://github.com/stsewd>`__: Docker: install requirements from local changes (`#7409 <https://github.com/readthedocs/readthedocs.org/pull/7409>`__)
* `@stsewd <https://github.com/stsewd>`__: ES: update dependencies (`#7408 <https://github.com/readthedocs/readthedocs.org/pull/7408>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 34 (`#7406 <https://github.com/readthedocs/readthedocs.org/pull/7406>`__)
* `@stsewd <https://github.com/stsewd>`__: API client: don't retry on POST (`#7383 <https://github.com/readthedocs/readthedocs.org/pull/7383>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: build_url added to all API v3 build endpoints (`#7373 <https://github.com/readthedocs/readthedocs.org/pull/7373>`__)
* `@stsewd <https://github.com/stsewd>`__: Guide: deprecating content (`#7333 <https://github.com/readthedocs/readthedocs.org/pull/7333>`__)
* `@humitos <https://github.com/humitos>`__: Auto-join email users field for Team model (`#7328 <https://github.com/readthedocs/readthedocs.org/pull/7328>`__)
* `@stsewd <https://github.com/stsewd>`__: Guide: Cross-referencing with Sphinx (`#7326 <https://github.com/readthedocs/readthedocs.org/pull/7326>`__)
* `@humitos <https://github.com/humitos>`__: Sync RemoteRepository and RemoteOrganization in all VCS providers (`#7310 <https://github.com/readthedocs/readthedocs.org/pull/7310>`__)
* `@stsewd <https://github.com/stsewd>`__: Page views: use origin URL instead of page name (`#7293 <https://github.com/readthedocs/readthedocs.org/pull/7293>`__)

Version 5.4.0
-------------

:Date: August 25, 2020

* `@stsewd <https://github.com/stsewd>`__: ES: match version used in production (`#7407 <https://github.com/readthedocs/readthedocs.org/pull/7407>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Advertising docs tweaks (`#7400 <https://github.com/readthedocs/readthedocs.org/pull/7400>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: update readthedocs-sphinx-search (`#7399 <https://github.com/readthedocs/readthedocs.org/pull/7399>`__)
* `@keewis <https://github.com/keewis>`__: document installing into a environment with pinned dependencies (`#7397 <https://github.com/readthedocs/readthedocs.org/pull/7397>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 32 (`#7377 <https://github.com/readthedocs/readthedocs.org/pull/7377>`__)
* `@stsewd <https://github.com/stsewd>`__: Builds: store build commands in storage (`#7356 <https://github.com/readthedocs/readthedocs.org/pull/7356>`__)
* `@stsewd <https://github.com/stsewd>`__: Guide: Cross-referencing with Sphinx (`#7326 <https://github.com/readthedocs/readthedocs.org/pull/7326>`__)

Version 5.3.0
-------------

:Date: August 18, 2020

* `@humitos <https://github.com/humitos>`__: Remove the comma added in logs that breaks grep parsing (`#7393 <https://github.com/readthedocs/readthedocs.org/pull/7393>`__)
* `@stsewd <https://github.com/stsewd>`__: GitLab webhook: don't fail on invalid payload (`#7391 <https://github.com/readthedocs/readthedocs.org/pull/7391>`__)
* `@stsewd <https://github.com/stsewd>`__: Task router: improve logging (`#7389 <https://github.com/readthedocs/readthedocs.org/pull/7389>`__)
* `@stsewd <https://github.com/stsewd>`__: External providers: better logging for GitLab (`#7385 <https://github.com/readthedocs/readthedocs.org/pull/7385>`__)
* `@stsewd <https://github.com/stsewd>`__: Task router: small changes (`#7379 <https://github.com/readthedocs/readthedocs.org/pull/7379>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: return relatives URLS (`#7376 <https://github.com/readthedocs/readthedocs.org/pull/7376>`__)
* `@stsewd <https://github.com/stsewd>`__: Sync versions: little optimization when deleting versions (`#7367 <https://github.com/readthedocs/readthedocs.org/pull/7367>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Add feature flag to just skip the sync version task entirely (`#7366 <https://github.com/readthedocs/readthedocs.org/pull/7366>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Convert zip to list for templates (`#7359 <https://github.com/readthedocs/readthedocs.org/pull/7359>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: implement stable API (`#7255 <https://github.com/readthedocs/readthedocs.org/pull/7255>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: improve parser (`#7233 <https://github.com/readthedocs/readthedocs.org/pull/7233>`__)

Version 5.2.3
-------------

:Date: August 04, 2020

* `@davidfischer <https://github.com/davidfischer>`__: Add a middleware for referrer policy (`#7346 <https://github.com/readthedocs/readthedocs.org/pull/7346>`__)
* `@stsewd <https://github.com/stsewd>`__: Footer: don't show the version warning for external version (`#7340 <https://github.com/readthedocs/readthedocs.org/pull/7340>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Lower rank for custom install docs. (`#7339 <https://github.com/readthedocs/readthedocs.org/pull/7339>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Argument list for "python -m virtualenv" without empty strings (`#7330 <https://github.com/readthedocs/readthedocs.org/pull/7330>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: fix some links (`#7317 <https://github.com/readthedocs/readthedocs.org/pull/7317>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: little improvements on getting start docs (`#7316 <https://github.com/readthedocs/readthedocs.org/pull/7316>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: migrate null ranks to zero (`#7274 <https://github.com/readthedocs/readthedocs.org/pull/7274>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: make it more clear search on subprojects (`#7272 <https://github.com/readthedocs/readthedocs.org/pull/7272>`__)

Version 5.2.2
-------------

:Date: July 29, 2020

* `@agjohnson <https://github.com/agjohnson>`__: Reduce robots.txt cache TTL (`#7334 <https://github.com/readthedocs/readthedocs.org/pull/7334>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Use the privacy embed for YouTube (`#7320 <https://github.com/readthedocs/readthedocs.org/pull/7320>`__)
* `@DougCal <https://github.com/DougCal>`__: re-worded text on top of "Import a Repository" (`#7318 <https://github.com/readthedocs/readthedocs.org/pull/7318>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: make it clear the config file options are per version (`#7314 <https://github.com/readthedocs/readthedocs.org/pull/7314>`__)
* `@humitos <https://github.com/humitos>`__: Feature to disable auto-generated index.md/README.rst files (`#7305 <https://github.com/readthedocs/readthedocs.org/pull/7305>`__)
* `@stsewd <https://github.com/stsewd>`__: Sphinx: always exclude the build directory (`#7303 <https://github.com/readthedocs/readthedocs.org/pull/7303>`__)
* `@humitos <https://github.com/humitos>`__: Enable SessionAuthentication on APIv3 endpoints (`#7295 <https://github.com/readthedocs/readthedocs.org/pull/7295>`__)
* `@humitos <https://github.com/humitos>`__: Allow to extend TeamManager (`#7294 <https://github.com/readthedocs/readthedocs.org/pull/7294>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 28 (`#7287 <https://github.com/readthedocs/readthedocs.org/pull/7287>`__)
* `@humitos <https://github.com/humitos>`__: Make "homepage" optional when updating a project (`#7286 <https://github.com/readthedocs/readthedocs.org/pull/7286>`__)
* `@humitos <https://github.com/humitos>`__: Allow users to set hidden on versions via APIv3 (`#7285 <https://github.com/readthedocs/readthedocs.org/pull/7285>`__)
* `@humitos <https://github.com/humitos>`__: DONT_INSTALL_DOCUTILS feature flag (`#7276 <https://github.com/readthedocs/readthedocs.org/pull/7276>`__)
* `@humitos <https://github.com/humitos>`__: Documentation for Single Sign-On feature on commercial (`#7212 <https://github.com/readthedocs/readthedocs.org/pull/7212>`__)

Version 5.2.1
-------------

:Date: July 14, 2020

* `@davidfischer <https://github.com/davidfischer>`__: Fix a case where "tags" is interpreted as a project slug (`#7284 <https://github.com/readthedocs/readthedocs.org/pull/7284>`__)
* `@stsewd <https://github.com/stsewd>`__: Dashboard: little optimization (`#7281 <https://github.com/readthedocs/readthedocs.org/pull/7281>`__)
* `@stsewd <https://github.com/stsewd>`__: Automation rules: privacy levels (`#7278 <https://github.com/readthedocs/readthedocs.org/pull/7278>`__)
* `@stsewd <https://github.com/stsewd>`__: Templates: optimize permissions check (`#7277 <https://github.com/readthedocs/readthedocs.org/pull/7277>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Fix versions (`#7271 <https://github.com/readthedocs/readthedocs.org/pull/7271>`__)
* `@stsewd <https://github.com/stsewd>`__: Tweak priority a little more (`#7270 <https://github.com/readthedocs/readthedocs.org/pull/7270>`__)
* `@stsewd <https://github.com/stsewd>`__: Don't default on the migration (`#7269 <https://github.com/readthedocs/readthedocs.org/pull/7269>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Automation rule to make versions hidden added (`#7265 <https://github.com/readthedocs/readthedocs.org/pull/7265>`__)
* `@humitos <https://github.com/humitos>`__: Add `is_member` template filter (`#7264 <https://github.com/readthedocs/readthedocs.org/pull/7264>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: set ranking for some pages (`#7257 <https://github.com/readthedocs/readthedocs.org/pull/7257>`__)
* `@stsewd <https://github.com/stsewd>`__: Sphinx: add --keep-going when fail_on_warning is true (`#7251 <https://github.com/readthedocs/readthedocs.org/pull/7251>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Don't allow Domain name matching production domain to be created (`#7244 <https://github.com/readthedocs/readthedocs.org/pull/7244>`__)
* `@humitos <https://github.com/humitos>`__: Documentation for Single Sign-On feature on commercial (`#7212 <https://github.com/readthedocs/readthedocs.org/pull/7212>`__)

Version 5.2.0
-------------

:Date: July 07, 2020

* `@saadmk11 <https://github.com/saadmk11>`__: Version docs Typo fix (`#7266 <https://github.com/readthedocs/readthedocs.org/pull/7266>`__)
* `@stsewd <https://github.com/stsewd>`__: CI: fix linter (`#7261 <https://github.com/readthedocs/readthedocs.org/pull/7261>`__)
* `@GioviQ <https://github.com/GioviQ>`__: Update manage-translations.rst (`#7260 <https://github.com/readthedocs/readthedocs.org/pull/7260>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add additional logging for sync_repository task (`#7254 <https://github.com/readthedocs/readthedocs.org/pull/7254>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: custom search page ranking (`#7237 <https://github.com/readthedocs/readthedocs.org/pull/7237>`__)

Version 5.1.5
-------------

:Date: July 01, 2020

* `@choldgraf <https://github.com/choldgraf>`__: cross-linking build limitations for pr builds (`#7248 <https://github.com/readthedocs/readthedocs.org/pull/7248>`__)
* `@humitos <https://github.com/humitos>`__: Allow to extend Import Project page from corporate (`#7234 <https://github.com/readthedocs/readthedocs.org/pull/7234>`__)
* `@humitos <https://github.com/humitos>`__: Make RemoteRepository.full_name db_index=True (`#7231 <https://github.com/readthedocs/readthedocs.org/pull/7231>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: tweak fuzziness (`#7225 <https://github.com/readthedocs/readthedocs.org/pull/7225>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Re-add the rst filter that got removed (`#7223 <https://github.com/readthedocs/readthedocs.org/pull/7223>`__)

Version 5.1.4
-------------

:Date: June 23, 2020

* `@stsewd <https://github.com/stsewd>`__: Search: index from html files for mkdocs projects (`#7208 <https://github.com/readthedocs/readthedocs.org/pull/7208>`__)
* `@stsewd <https://github.com/stsewd>`__:  Search: recursively parse sections (`#7207 <https://github.com/readthedocs/readthedocs.org/pull/7207>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: more general parser for html (`#7204 <https://github.com/readthedocs/readthedocs.org/pull/7204>`__)
* `@humitos <https://github.com/humitos>`__: Use total_memory to calculate "time" Docker limit (`#7203 <https://github.com/readthedocs/readthedocs.org/pull/7203>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Feature flag for using latest Sphinx (`#7201 <https://github.com/readthedocs/readthedocs.org/pull/7201>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Mention that we don't index search in PR builds (`#7199 <https://github.com/readthedocs/readthedocs.org/pull/7199>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Add a feature flag to use latest RTD Sphinx ext (`#7198 <https://github.com/readthedocs/readthedocs.org/pull/7198>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 5.1.3 (`#7197 <https://github.com/readthedocs/readthedocs.org/pull/7197>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: improve results for simple queries (`#7194 <https://github.com/readthedocs/readthedocs.org/pull/7194>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: refactor json parser (`#7184 <https://github.com/readthedocs/readthedocs.org/pull/7184>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove unused dep (`#7147 <https://github.com/readthedocs/readthedocs.org/pull/7147>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Use theme release 0.5.0rc1 for docs (`#7037 <https://github.com/readthedocs/readthedocs.org/pull/7037>`__)
* `@humitos <https://github.com/humitos>`__: Skip promoting new stable if current stable is not `machine=True` (`#6695 <https://github.com/readthedocs/readthedocs.org/pull/6695>`__)

Version 5.1.3
-------------

:Date: June 16, 2020

* `@davidfischer <https://github.com/davidfischer>`__: Fix the project migration conflict (`#7196 <https://github.com/readthedocs/readthedocs.org/pull/7196>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: fix pagination (`#7195 <https://github.com/readthedocs/readthedocs.org/pull/7195>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Document the fact that PR builds are now enabled on .org (`#7187 <https://github.com/readthedocs/readthedocs.org/pull/7187>`__)
* `@stsewd <https://github.com/stsewd>`__: Project: make description shorter (`#7186 <https://github.com/readthedocs/readthedocs.org/pull/7186>`__)
* `@stsewd <https://github.com/stsewd>`__: Migrate private versions (`#7181 <https://github.com/readthedocs/readthedocs.org/pull/7181>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Update sharing examples (`#7179 <https://github.com/readthedocs/readthedocs.org/pull/7179>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Allow projects to opt-out of analytics (`#7175 <https://github.com/readthedocs/readthedocs.org/pull/7175>`__)
* `@stsewd <https://github.com/stsewd>`__: Docs: install readthedocs-sphinx-search from pypi (`#7174 <https://github.com/readthedocs/readthedocs.org/pull/7174>`__)
* `@humitos <https://github.com/humitos>`__: Rename API endpoint call (`#7173 <https://github.com/readthedocs/readthedocs.org/pull/7173>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Reduce logging in proxito middleware so it isn't in Sentry (`#7172 <https://github.com/readthedocs/readthedocs.org/pull/7172>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 5.1.2 (`#7171 <https://github.com/readthedocs/readthedocs.org/pull/7171>`__)
* `@humitos <https://github.com/humitos>`__: Use `CharField.choices` for `Build.status_code` (`#7166 <https://github.com/readthedocs/readthedocs.org/pull/7166>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Store pageviews via signals, not tasks (`#7106 <https://github.com/readthedocs/readthedocs.org/pull/7106>`__)
* `@stsewd <https://github.com/stsewd>`__: Move organizations models (`#6776 <https://github.com/readthedocs/readthedocs.org/pull/6776>`__)

Version 5.1.2
-------------

:Date: June 09, 2020

* `@humitos <https://github.com/humitos>`__: Use `CharField.choices` for `Build.status_code` (`#7166 <https://github.com/readthedocs/readthedocs.org/pull/7166>`__)
* `@humitos <https://github.com/humitos>`__: Install `argh` for Docker environment (`#7164 <https://github.com/readthedocs/readthedocs.org/pull/7164>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Reindex search on the `reindex` queue (`#7161 <https://github.com/readthedocs/readthedocs.org/pull/7161>`__)
* `@stsewd <https://github.com/stsewd>`__: Project search: Show original description when there isn't highlight (`#7160 <https://github.com/readthedocs/readthedocs.org/pull/7160>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: highlight results from projects (`#7158 <https://github.com/readthedocs/readthedocs.org/pull/7158>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix custom URLConf redirects (`#7155 <https://github.com/readthedocs/readthedocs.org/pull/7155>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Allow `blank=True` for URLConf (`#7153 <https://github.com/readthedocs/readthedocs.org/pull/7153>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix flaky test (`#7148 <https://github.com/readthedocs/readthedocs.org/pull/7148>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: Make total_results not null (`#7145 <https://github.com/readthedocs/readthedocs.org/pull/7145>`__)
* `@stsewd <https://github.com/stsewd>`__: Project: make external_builds_enabled not null (`#7144 <https://github.com/readthedocs/readthedocs.org/pull/7144>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Do not Pre-populate username field for account delete (`#7143 <https://github.com/readthedocs/readthedocs.org/pull/7143>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Add feature flag to use the stock Sphinx builders (`#7141 <https://github.com/readthedocs/readthedocs.org/pull/7141>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Move changes_files to before search indexing (`#7138 <https://github.com/readthedocs/readthedocs.org/pull/7138>`__)
* `@stsewd <https://github.com/stsewd>`__: Proxito middleware: reset to original urlconf after request (`#7137 <https://github.com/readthedocs/readthedocs.org/pull/7137>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: don't index permalinks (`#7134 <https://github.com/readthedocs/readthedocs.org/pull/7134>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Revert "Merge pull request #7101 from readthedocs/show-last-total" (`#7133 <https://github.com/readthedocs/readthedocs.org/pull/7133>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 5.1.1 (`#7129 <https://github.com/readthedocs/readthedocs.org/pull/7129>`__)
* `@humitos <https://github.com/humitos>`__: Use "-j auto" on sphinx-build command to build in parallel (`#7128 <https://github.com/readthedocs/readthedocs.org/pull/7128>`__)
* `@humitos <https://github.com/humitos>`__: De-duplicate builds (`#7123 <https://github.com/readthedocs/readthedocs.org/pull/7123>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: refactor API to not emulate a Django queryset (`#7114 <https://github.com/readthedocs/readthedocs.org/pull/7114>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Store pageviews via signals, not tasks (`#7106 <https://github.com/readthedocs/readthedocs.org/pull/7106>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: don't index line numbers from code blocks (`#7104 <https://github.com/readthedocs/readthedocs.org/pull/7104>`__)
* `@humitos <https://github.com/humitos>`__: Document Embed APIv2 endpoint (`#7095 <https://github.com/readthedocs/readthedocs.org/pull/7095>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add a project-level configuration for PR builds (`#7090 <https://github.com/readthedocs/readthedocs.org/pull/7090>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove usage of project.privacy_level (`#7013 <https://github.com/readthedocs/readthedocs.org/pull/7013>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 18 (`#7012 <https://github.com/readthedocs/readthedocs.org/pull/7012>`__)
* `@stsewd <https://github.com/stsewd>`__: Allow to enable server side search for MkDocs (`#6986 <https://github.com/readthedocs/readthedocs.org/pull/6986>`__)
* `@stsewd <https://github.com/stsewd>`__: Pass the NO_COLOR env var to builder (`#6981 <https://github.com/readthedocs/readthedocs.org/pull/6981>`__)
* `@humitos <https://github.com/humitos>`__: Limit concurrency in translations (`#6969 <https://github.com/readthedocs/readthedocs.org/pull/6969>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add ability for users to set their own URLConf (`#6963 <https://github.com/readthedocs/readthedocs.org/pull/6963>`__)

Version 5.1.1
-------------

:Date: May 26, 2020

* `@stsewd <https://github.com/stsewd>`__: Search: show total_results from last query (`#7101 <https://github.com/readthedocs/readthedocs.org/pull/7101>`__)
* `@humitos <https://github.com/humitos>`__: Add a tip in EmbedAPI to use Sphinx reference in section (`#7099 <https://github.com/readthedocs/readthedocs.org/pull/7099>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 5.1.0 (`#7098 <https://github.com/readthedocs/readthedocs.org/pull/7098>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add a setting for storing pageviews (`#7097 <https://github.com/readthedocs/readthedocs.org/pull/7097>`__)
* `@humitos <https://github.com/humitos>`__: Document Embed APIv2 endpoint (`#7095 <https://github.com/readthedocs/readthedocs.org/pull/7095>`__)
* `@stsewd <https://github.com/stsewd>`__: Footer: Check for mkdocs doctype too (`#7094 <https://github.com/readthedocs/readthedocs.org/pull/7094>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix the unresolver not working properly with root paths (`#7093 <https://github.com/readthedocs/readthedocs.org/pull/7093>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add a project-level configuration for PR builds (`#7090 <https://github.com/readthedocs/readthedocs.org/pull/7090>`__)
* `@santos22 <https://github.com/santos22>`__: Fix tests ahead of django-dynamic-fixture update (`#7073 <https://github.com/readthedocs/readthedocs.org/pull/7073>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add ability for users to set their own URLConf (`#6963 <https://github.com/readthedocs/readthedocs.org/pull/6963>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Store Pageviews in DB (`#6121 <https://github.com/readthedocs/readthedocs.org/pull/6121>`__)
* `@humitos <https://github.com/humitos>`__: GitLab Integration (`#3327 <https://github.com/readthedocs/readthedocs.org/pull/3327>`__)

Version 5.1.0
-------------

:Date: May 19, 2020

This release includes one major new feature which is Pageview Analytics.
This allows projects to see the pages in their docs that have been viewed in the past 30 days,
giving them an idea of what pages to focus on when updating them.

This release also has a few small search improvements, doc updates, and other bugfixes as well.

* `@ericholscher <https://github.com/ericholscher>`__: Add a setting for storing pageviews (`#7097 <https://github.com/readthedocs/readthedocs.org/pull/7097>`__)
* `@stsewd <https://github.com/stsewd>`__: Footer: Check for mkdocs doctype too (`#7094 <https://github.com/readthedocs/readthedocs.org/pull/7094>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix the unresolver not working properly with root paths (`#7093 <https://github.com/readthedocs/readthedocs.org/pull/7093>`__)
* `@stsewd <https://github.com/stsewd>`__: Privacy levels: migrate protected versions (`#7092 <https://github.com/readthedocs/readthedocs.org/pull/7092>`__)
* `@humitos <https://github.com/humitos>`__: Guide for Embed API (`#7089 <https://github.com/readthedocs/readthedocs.org/pull/7089>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Document HSTS support (`#7083 <https://github.com/readthedocs/readthedocs.org/pull/7083>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: record queries with 0 results (`#7081 <https://github.com/readthedocs/readthedocs.org/pull/7081>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: track total results (`#7080 <https://github.com/readthedocs/readthedocs.org/pull/7080>`__)
* `@humitos <https://github.com/humitos>`__: Proxy embed URL (`#7079 <https://github.com/readthedocs/readthedocs.org/pull/7079>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: Little refactor (`#7076 <https://github.com/readthedocs/readthedocs.org/pull/7076>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Canonical/HTTPS redirect fix (`#7075 <https://github.com/readthedocs/readthedocs.org/pull/7075>`__)
* `@santos22 <https://github.com/santos22>`__: Fix tests ahead of django-dynamic-fixture update (`#7073 <https://github.com/readthedocs/readthedocs.org/pull/7073>`__)
* `@stsewd <https://github.com/stsewd>`__: Sphinx Search: don't skip indexing if one file fails (`#7071 <https://github.com/readthedocs/readthedocs.org/pull/7071>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: generate full link from the server side (`#7070 <https://github.com/readthedocs/readthedocs.org/pull/7070>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix PR builds being marked built (`#7069 <https://github.com/readthedocs/readthedocs.org/pull/7069>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add a page about choosing between .com/.org (`#7068 <https://github.com/readthedocs/readthedocs.org/pull/7068>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 5.0.0 (`#7064 <https://github.com/readthedocs/readthedocs.org/pull/7064>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: Index more content from sphinx (`#7063 <https://github.com/readthedocs/readthedocs.org/pull/7063>`__)
* `@santos22 <https://github.com/santos22>`__: Hide unbuilt versions in footer flyout (`#7056 <https://github.com/readthedocs/readthedocs.org/pull/7056>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Docs: Refactor and simplify our docs (`#7052 <https://github.com/readthedocs/readthedocs.org/pull/7052>`__)
* `@stsewd <https://github.com/stsewd>`__: Search Document: remove unused class methods (`#7035 <https://github.com/readthedocs/readthedocs.org/pull/7035>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: iterate over valid facets only (`#7034 <https://github.com/readthedocs/readthedocs.org/pull/7034>`__)
* `@stsewd <https://github.com/stsewd>`__: RTDFacetedSearch: pass filters in one way only (`#7032 <https://github.com/readthedocs/readthedocs.org/pull/7032>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Store Pageviews in DB (`#6121 <https://github.com/readthedocs/readthedocs.org/pull/6121>`__)

Version 5.0.0
-------------

:Date: May 12, 2020

This release includes two large changes, one that is breaking and requires a major version upgrade:

* We have removed our deprecated doc serving code that used ``core/views``, ``core/symlinks``, and ``builds/syncers`` (`#6535 <https://github.com/readthedocs/readthedocs.org/pull/6535>`__). All doc serving should now be done via ``proxito``. In production this has been the case for over a month, we have now removed the deprecated code from the codebase.
* We did a large documentation refactor that should make things nicer to read and highlights more of our existing features. This is the first of a series of new documentation additions we have planned


* `@ericholscher <https://github.com/ericholscher>`__: Fix the caching of featured projects (`#7054 <https://github.com/readthedocs/readthedocs.org/pull/7054>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Docs: Refactor and simplify our docs (`#7052 <https://github.com/readthedocs/readthedocs.org/pull/7052>`__)
* `@stsewd <https://github.com/stsewd>`__: Mention using ssh URLs when using private submodules (`#7046 <https://github.com/readthedocs/readthedocs.org/pull/7046>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Show project slug in Version admin (`#7042 <https://github.com/readthedocs/readthedocs.org/pull/7042>`__)
* `@stsewd <https://github.com/stsewd>`__: List apiv3 first (`#7041 <https://github.com/readthedocs/readthedocs.org/pull/7041>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove CELERY_ROUTER flag (`#7040 <https://github.com/readthedocs/readthedocs.org/pull/7040>`__)
* `@stsewd <https://github.com/stsewd>`__: Search: remove unused taxonomy field (`#7033 <https://github.com/readthedocs/readthedocs.org/pull/7033>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Use a high time limit for celery build task (`#7029 <https://github.com/readthedocs/readthedocs.org/pull/7029>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Clean up build admin to make list display match search (`#7028 <https://github.com/readthedocs/readthedocs.org/pull/7028>`__)
* `@stsewd <https://github.com/stsewd>`__: Task Router: check for None (`#7027 <https://github.com/readthedocs/readthedocs.org/pull/7027>`__)
* `@stsewd <https://github.com/stsewd>`__: Implement repo_exists for all VCS backends (`#7025 <https://github.com/readthedocs/readthedocs.org/pull/7025>`__)
* `@stsewd <https://github.com/stsewd>`__: Mkdocs: Index pages without anchors (`#7024 <https://github.com/readthedocs/readthedocs.org/pull/7024>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Move docker limits back to setting (`#7023 <https://github.com/readthedocs/readthedocs.org/pull/7023>`__)
* `@humitos <https://github.com/humitos>`__: Fix typo (`#7022 <https://github.com/readthedocs/readthedocs.org/pull/7022>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix linter (`#7021 <https://github.com/readthedocs/readthedocs.org/pull/7021>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 4.1.8 (`#7020 <https://github.com/readthedocs/readthedocs.org/pull/7020>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Cleanup unresolver logging (`#7019 <https://github.com/readthedocs/readthedocs.org/pull/7019>`__)
* `@stsewd <https://github.com/stsewd>`__: Document about next when using a secret link (`#7015 <https://github.com/readthedocs/readthedocs.org/pull/7015>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove unused field project.version_privacy_level (`#7011 <https://github.com/readthedocs/readthedocs.org/pull/7011>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add proxito headers to redirect responses (`#7007 <https://github.com/readthedocs/readthedocs.org/pull/7007>`__)
* `@stsewd <https://github.com/stsewd>`__: Make hidden field not null (`#6996 <https://github.com/readthedocs/readthedocs.org/pull/6996>`__)
* `@humitos <https://github.com/humitos>`__: Show a list of packages installed on environment (`#6992 <https://github.com/readthedocs/readthedocs.org/pull/6992>`__)
* `@eric-wieser <https://github.com/eric-wieser>`__: Ensure invoked Sphinx matches importable one (`#6965 <https://github.com/readthedocs/readthedocs.org/pull/6965>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add an unresolver similar to our resolver (`#6944 <https://github.com/readthedocs/readthedocs.org/pull/6944>`__)
* `@KengoTODA <https://github.com/KengoTODA>`__: Replace "PROJECT" with project object (`#6878 <https://github.com/readthedocs/readthedocs.org/pull/6878>`__)
* `@humitos <https://github.com/humitos>`__: Remove code replaced by El Proxito and stateless servers (`#6535 <https://github.com/readthedocs/readthedocs.org/pull/6535>`__)

Version 4.1.8
-------------

:Date: May 05, 2020

This release adds a few new features and bugfixes.
The largest change is the addition of ``hidden`` versions,
which allows docs to be built but not shown to users on the site.
This will keep old links from breaking but not direct new users there.

We've also expanded the CDN support to make sure we're passing headers on 3xx and 4xx responses.
This will allow us to expand the timeout on our CDN.

We've also updated and added a good amount of documentation in this release,
and we're starting a larger refactor of our docs to help users understand the platform better.

* `@ericholscher <https://github.com/ericholscher>`__: Cleanup unresolver logging (`#7019 <https://github.com/readthedocs/readthedocs.org/pull/7019>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add CDN to the installed apps (`#7014 <https://github.com/readthedocs/readthedocs.org/pull/7014>`__)
* `@eric-wieser <https://github.com/eric-wieser>`__: Emit a better error if no feature flag is found (`#7009 <https://github.com/readthedocs/readthedocs.org/pull/7009>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add proxito headers to redirect responses (`#7007 <https://github.com/readthedocs/readthedocs.org/pull/7007>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add Priority 0 to Celery (`#7006 <https://github.com/readthedocs/readthedocs.org/pull/7006>`__)
* `@stsewd <https://github.com/stsewd>`__: Update conftest (`#7002 <https://github.com/readthedocs/readthedocs.org/pull/7002>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Start storing JSON data for PR builds (`#7001 <https://github.com/readthedocs/readthedocs.org/pull/7001>`__)
* `@yarikoptic <https://github.com/yarikoptic>`__: Add a note if build status is not being reported (`#6999 <https://github.com/readthedocs/readthedocs.org/pull/6999>`__)
* `@stsewd <https://github.com/stsewd>`__: Update common (`#6997 <https://github.com/readthedocs/readthedocs.org/pull/6997>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Exclusively handle proxito HSTS from the backend (`#6994 <https://github.com/readthedocs/readthedocs.org/pull/6994>`__)
* `@humitos <https://github.com/humitos>`__: Mention concurrent builds limitation in "Build Process" (`#6993 <https://github.com/readthedocs/readthedocs.org/pull/6993>`__)
* `@humitos <https://github.com/humitos>`__: Show a list of packages installed on environment (`#6992 <https://github.com/readthedocs/readthedocs.org/pull/6992>`__)
* `@humitos <https://github.com/humitos>`__: Document SHARE_SPHINX_DOCTREE flag (`#6991 <https://github.com/readthedocs/readthedocs.org/pull/6991>`__)
* `@humitos <https://github.com/humitos>`__: Contact us via email for Feature Flags (`#6990 <https://github.com/readthedocs/readthedocs.org/pull/6990>`__)
* `@santos22 <https://github.com/santos22>`__: Alter field url on webhook (`#6988 <https://github.com/readthedocs/readthedocs.org/pull/6988>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Log sync_repository_task when we run it (`#6987 <https://github.com/readthedocs/readthedocs.org/pull/6987>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Remove old SSL cert warning, since they now work. (`#6985 <https://github.com/readthedocs/readthedocs.org/pull/6985>`__)
* `@agjohnson <https://github.com/agjohnson>`__: More fixes for automatic Docker limits (`#6982 <https://github.com/readthedocs/readthedocs.org/pull/6982>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Add details to our changelog for 4.1.7 (`#6978 <https://github.com/readthedocs/readthedocs.org/pull/6978>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 4.1.7 (`#6976 <https://github.com/readthedocs/readthedocs.org/pull/6976>`__)
* `@humitos <https://github.com/humitos>`__: Remove DOCKER_LIMITS (`#6975 <https://github.com/readthedocs/readthedocs.org/pull/6975>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Catch infinite canonical redirects (`#6973 <https://github.com/readthedocs/readthedocs.org/pull/6973>`__)
* `@eric-wieser <https://github.com/eric-wieser>`__: Ensure invoked Sphinx matches importable one (`#6965 <https://github.com/readthedocs/readthedocs.org/pull/6965>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add an unresolver similar to our resolver (`#6944 <https://github.com/readthedocs/readthedocs.org/pull/6944>`__)
* `@stsewd <https://github.com/stsewd>`__: Add support for Mkdocs search (`#6937 <https://github.com/readthedocs/readthedocs.org/pull/6937>`__)
* `@humitos <https://github.com/humitos>`__: Optimization on `sync_versions` to use ls-remote on Git VCS (`#6930 <https://github.com/readthedocs/readthedocs.org/pull/6930>`__)
* `@humitos <https://github.com/humitos>`__: Split X-RTD-Version-Method header into two HTTP headers. (`#6907 <https://github.com/readthedocs/readthedocs.org/pull/6907>`__)
* `@stsewd <https://github.com/stsewd>`__: Allow to override sign in and sign out views (`#6901 <https://github.com/readthedocs/readthedocs.org/pull/6901>`__)
* `@stsewd <https://github.com/stsewd>`__: Hide version privacy (`#6808 <https://github.com/readthedocs/readthedocs.org/pull/6808>`__)
* `@stsewd <https://github.com/stsewd>`__: Implement hidden state for versions (`#6792 <https://github.com/readthedocs/readthedocs.org/pull/6792>`__)
* `@stsewd <https://github.com/stsewd>`__: Design doc for privacy levels (`#6194 <https://github.com/readthedocs/readthedocs.org/pull/6194>`__)

Version 4.1.7
-------------

:Date: April 28, 2020

As of this release, most documentation on Read the Docs Community is now behind Cloudflare's CDN.
It should be much faster for people further from US East.
Please report any issues you experience with stale cached documentation (especially CSS/JS).

Another change in this release related to how custom domains are handled.
Custom domains will now redirect HTTP -> HTTPS if the Domain's "HTTPS" flag is set.
Also, the subdomain URL (eg. ``<project>.readthedocs.io/...``) should redirect to the custom domain
if the Domain's "canonical" flag is set.
These flags are configurable in your project dashboard under :guilabel:`Admin` > :guilabel:`Domains`.

Many of the other changes related to improvements for our infrastructure
to allow us to have autoscaling build and web servers.
There were bug fixes for projects using versions tied to annotated git tags
and custom user redirects will now send query parameters.

* `@ericholscher <https://github.com/ericholscher>`__: Reduce proxito logging (`#6970 <https://github.com/readthedocs/readthedocs.org/pull/6970>`__)
* `@humitos <https://github.com/humitos>`__: Log build/sync tasks when triggered (`#6967 <https://github.com/readthedocs/readthedocs.org/pull/6967>`__)
* `@humitos <https://github.com/humitos>`__: Stop builders gracefully on SIGTERM (`#6960 <https://github.com/readthedocs/readthedocs.org/pull/6960>`__)
* `@stsewd <https://github.com/stsewd>`__: Try to fix annotated tags (`#6959 <https://github.com/readthedocs/readthedocs.org/pull/6959>`__)
* `@stsewd <https://github.com/stsewd>`__: Include query params in 404 redirects (`#6957 <https://github.com/readthedocs/readthedocs.org/pull/6957>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix the trailing slash in our repo regexs (`#6956 <https://github.com/readthedocs/readthedocs.org/pull/6956>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Add canonical to the Domain listview in the admin (`#6954 <https://github.com/readthedocs/readthedocs.org/pull/6954>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Allow setting HSTS on a per domain basis (`#6953 <https://github.com/readthedocs/readthedocs.org/pull/6953>`__)
* `@humitos <https://github.com/humitos>`__: Refactor how we handle GitHub webhook events (`#6949 <https://github.com/readthedocs/readthedocs.org/pull/6949>`__)
* `@humitos <https://github.com/humitos>`__: Return 400 when importing an already existing project (`#6948 <https://github.com/readthedocs/readthedocs.org/pull/6948>`__)
* `@humitos <https://github.com/humitos>`__: Return max_concurrent_builds in ProjectAdminSerializer (`#6946 <https://github.com/readthedocs/readthedocs.org/pull/6946>`__)
* `@tom-doerr <https://github.com/tom-doerr>`__: Update year (`#6945 <https://github.com/readthedocs/readthedocs.org/pull/6945>`__)
* `@humitos <https://github.com/humitos>`__: Revert "Use requests.head to query storage.exists" (`#6941 <https://github.com/readthedocs/readthedocs.org/pull/6941>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 4.1.6 (`#6940 <https://github.com/readthedocs/readthedocs.org/pull/6940>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove note about search analytics being beta (`#6939 <https://github.com/readthedocs/readthedocs.org/pull/6939>`__)
* `@stsewd <https://github.com/stsewd>`__: Add troubleshooting section for dev search docs (`#6933 <https://github.com/readthedocs/readthedocs.org/pull/6933>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Index date and ID together on builds (`#6926 <https://github.com/readthedocs/readthedocs.org/pull/6926>`__)
* `@davidfischer <https://github.com/davidfischer>`__: CAA records are not only for users of Cloudflare DNS (`#6925 <https://github.com/readthedocs/readthedocs.org/pull/6925>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Docs on supporting root domains (`#6923 <https://github.com/readthedocs/readthedocs.org/pull/6923>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add basic support for lower priority PR builds (`#6921 <https://github.com/readthedocs/readthedocs.org/pull/6921>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Change the dashboard search to default to searching files (`#6920 <https://github.com/readthedocs/readthedocs.org/pull/6920>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Canonicalize domains and redirect in proxito (`#6905 <https://github.com/readthedocs/readthedocs.org/pull/6905>`__)
* `@zdover23 <https://github.com/zdover23>`__: Made syntactical improvements and fixed some vocabulary issues. (`#6825 <https://github.com/readthedocs/readthedocs.org/pull/6825>`__)

Version 4.1.6
-------------

:Date: April 21, 2020

* `@stsewd <https://github.com/stsewd>`__: Revert usage of watchman (`#6934 <https://github.com/readthedocs/readthedocs.org/pull/6934>`__)
* `@Mariatta <https://github.com/Mariatta>`__: Fix typo: you -> your (`#6931 <https://github.com/readthedocs/readthedocs.org/pull/6931>`__)
* `@humitos <https://github.com/humitos>`__: Do not override the domain of Azure Storage (`#6928 <https://github.com/readthedocs/readthedocs.org/pull/6928>`__)
* `@humitos <https://github.com/humitos>`__: Per-project concurrency and check before triggering the build (`#6927 <https://github.com/readthedocs/readthedocs.org/pull/6927>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Remove note about underscore in domain (`#6924 <https://github.com/readthedocs/readthedocs.org/pull/6924>`__)
* `@stsewd <https://github.com/stsewd>`__: Pass INIT to azurite (`#6918 <https://github.com/readthedocs/readthedocs.org/pull/6918>`__)
* `@humitos <https://github.com/humitos>`__: Use requests.head to query storage.exists (`#6917 <https://github.com/readthedocs/readthedocs.org/pull/6917>`__)
* `@stsewd <https://github.com/stsewd>`__: Bring back search highlight (`#6914 <https://github.com/readthedocs/readthedocs.org/pull/6914>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Improve logging around status setting on PR builds (`#6912 <https://github.com/readthedocs/readthedocs.org/pull/6912>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add hoverxref to our docs (`#6911 <https://github.com/readthedocs/readthedocs.org/pull/6911>`__)
* `@stsewd <https://github.com/stsewd>`__: Safely join storage paths (`#6910 <https://github.com/readthedocs/readthedocs.org/pull/6910>`__)
* `@humitos <https://github.com/humitos>`__: Release 4.1.5 (`#6909 <https://github.com/readthedocs/readthedocs.org/pull/6909>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix Cache-Tag header name (`#6908 <https://github.com/readthedocs/readthedocs.org/pull/6908>`__)
* `@stsewd <https://github.com/stsewd>`__: Handle paths with trailing `/` (`#6906 <https://github.com/readthedocs/readthedocs.org/pull/6906>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Include the project slug in the PR context (`#6904 <https://github.com/readthedocs/readthedocs.org/pull/6904>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix single version infinite redirect (`#6900 <https://github.com/readthedocs/readthedocs.org/pull/6900>`__)
* `@humitos <https://github.com/humitos>`__: Load YAML files safely (`#6897 <https://github.com/readthedocs/readthedocs.org/pull/6897>`__)
* `@humitos <https://github.com/humitos>`__: Use a custom Task Router to route tasks dynamically (`#6849 <https://github.com/readthedocs/readthedocs.org/pull/6849>`__)
* `@zdover23 <https://github.com/zdover23>`__: Made syntactical improvements and fixed some vocabulary issues. (`#6825 <https://github.com/readthedocs/readthedocs.org/pull/6825>`__)
* `@humitos <https://github.com/humitos>`__: Add CORS headers to Azurite (`#6784 <https://github.com/readthedocs/readthedocs.org/pull/6784>`__)
* `@stsewd <https://github.com/stsewd>`__: Force to use proxied API for footer and search (`#6768 <https://github.com/readthedocs/readthedocs.org/pull/6768>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Only output debug logging from RTD app (`#6717 <https://github.com/readthedocs/readthedocs.org/pull/6717>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add ability to sort dashboard by modified date (`#6680 <https://github.com/readthedocs/readthedocs.org/pull/6680>`__)
* `@stsewd <https://github.com/stsewd>`__: Protection against None when sending notifications (`#6610 <https://github.com/readthedocs/readthedocs.org/pull/6610>`__)
* `@stsewd <https://github.com/stsewd>`__: Guide: private python packages in .com (`#6530 <https://github.com/readthedocs/readthedocs.org/pull/6530>`__)

Version 4.1.5
-------------

:Date: April 15, 2020

* `@ericholscher <https://github.com/ericholscher>`__: Fix Cache-Tag header name (`#6908 <https://github.com/readthedocs/readthedocs.org/pull/6908>`__)
* `@stsewd <https://github.com/stsewd>`__: Handle paths with trailing `/` (`#6906 <https://github.com/readthedocs/readthedocs.org/pull/6906>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix single version infinite redirect (`#6900 <https://github.com/readthedocs/readthedocs.org/pull/6900>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 4.1.4 (`#6899 <https://github.com/readthedocs/readthedocs.org/pull/6899>`__)
* `@humitos <https://github.com/humitos>`__: On Azure .exists blob timeout, log the exception and return False (`#6895 <https://github.com/readthedocs/readthedocs.org/pull/6895>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix URLs like `/projects/subproject` from 404ing when they don't end with a slash (`#6888 <https://github.com/readthedocs/readthedocs.org/pull/6888>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Allocate docker limits based on server size. (`#6879 <https://github.com/readthedocs/readthedocs.org/pull/6879>`__)

Version 4.1.4
-------------

:Date: April 14, 2020

* `@humitos <https://github.com/humitos>`__: On Azure .exists blob timeout, log the exception and return False (`#6895 <https://github.com/readthedocs/readthedocs.org/pull/6895>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix URLs like `/projects/subproject` from 404ing when they don't end with a slash (`#6888 <https://github.com/readthedocs/readthedocs.org/pull/6888>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add CloudFlare Cache tags support (`#6887 <https://github.com/readthedocs/readthedocs.org/pull/6887>`__)
* `@stsewd <https://github.com/stsewd>`__: Update requirements (`#6885 <https://github.com/readthedocs/readthedocs.org/pull/6885>`__)
* `@stsewd <https://github.com/stsewd>`__: Be explicit with PUBLIC_DOMAIN setting (`#6881 <https://github.com/readthedocs/readthedocs.org/pull/6881>`__)
* `@stsewd <https://github.com/stsewd>`__: Allow to override project detail view (`#6880 <https://github.com/readthedocs/readthedocs.org/pull/6880>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Allocate docker limits based on server size. (`#6879 <https://github.com/readthedocs/readthedocs.org/pull/6879>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Make the status name in CI configurable via setting (`#6877 <https://github.com/readthedocs/readthedocs.org/pull/6877>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add 12 hour caching to our robots.txt serving (`#6876 <https://github.com/readthedocs/readthedocs.org/pull/6876>`__)
* `@humitos <https://github.com/humitos>`__: Filter triggered builds when checking concurrency (`#6875 <https://github.com/readthedocs/readthedocs.org/pull/6875>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix issue with sphinx domain types with `:` in them: (`#6874 <https://github.com/readthedocs/readthedocs.org/pull/6874>`__)
* `@stsewd <https://github.com/stsewd>`__: Make dashboard faster for projects with a lot of subprojects (`#6873 <https://github.com/readthedocs/readthedocs.org/pull/6873>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 4.1.3 (`#6872 <https://github.com/readthedocs/readthedocs.org/pull/6872>`__)
* `@stsewd <https://github.com/stsewd>`__: Don't do unnecessary queries when listing subprojects (`#6869 <https://github.com/readthedocs/readthedocs.org/pull/6869>`__)
* `@stsewd <https://github.com/stsewd>`__: Optimize resolve_path (`#6867 <https://github.com/readthedocs/readthedocs.org/pull/6867>`__)
* `@stsewd <https://github.com/stsewd>`__: Don't do extra query if the project is a translation (`#6865 <https://github.com/readthedocs/readthedocs.org/pull/6865>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove private argument from resolver (`#6864 <https://github.com/readthedocs/readthedocs.org/pull/6864>`__)
* `@stsewd <https://github.com/stsewd>`__: Support mkdocs html pages as doctype (`#6846 <https://github.com/readthedocs/readthedocs.org/pull/6846>`__)
* `@stsewd <https://github.com/stsewd>`__: Reduce queries to storage to serve 404 pages (`#6845 <https://github.com/readthedocs/readthedocs.org/pull/6845>`__)
* `@stsewd <https://github.com/stsewd>`__: Rework custom domains docs (`#6844 <https://github.com/readthedocs/readthedocs.org/pull/6844>`__)
* `@stsewd <https://github.com/stsewd>`__: Add checking the github oauth app in the troubleshooting page (`#6827 <https://github.com/readthedocs/readthedocs.org/pull/6827>`__)
* `@humitos <https://github.com/humitos>`__: Return full path URL (including `.html`) on `/api/v2/docurl/` endpoint (`#6082 <https://github.com/readthedocs/readthedocs.org/pull/6082>`__)

Version 4.1.3
-------------

:Date: April 07, 2020

* `@stsewd <https://github.com/stsewd>`__: Don't do unnecessary queries when listing subprojects (`#6869 <https://github.com/readthedocs/readthedocs.org/pull/6869>`__)
* `@stsewd <https://github.com/stsewd>`__: Don't do extra query if the project is a translation (`#6865 <https://github.com/readthedocs/readthedocs.org/pull/6865>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove private argument from resolver (`#6864 <https://github.com/readthedocs/readthedocs.org/pull/6864>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Make development docs a bit easier to find (`#6861 <https://github.com/readthedocs/readthedocs.org/pull/6861>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Add an advertising API timeout (`#6856 <https://github.com/readthedocs/readthedocs.org/pull/6856>`__)
* `@humitos <https://github.com/humitos>`__: Add more exceptions as WARNING log level (`#6851 <https://github.com/readthedocs/readthedocs.org/pull/6851>`__)
* `@humitos <https://github.com/humitos>`__: Limit concurrent builds (`#6847 <https://github.com/readthedocs/readthedocs.org/pull/6847>`__)
* `@humitos <https://github.com/humitos>`__: Release 4.1.2 (`#6840 <https://github.com/readthedocs/readthedocs.org/pull/6840>`__)
* `@humitos <https://github.com/humitos>`__: Report build status in a smarter way (`#6839 <https://github.com/readthedocs/readthedocs.org/pull/6839>`__)
* `@stsewd <https://github.com/stsewd>`__: Update messages-extends to latest version (`#6838 <https://github.com/readthedocs/readthedocs.org/pull/6838>`__)
* `@humitos <https://github.com/humitos>`__: Do not save pip cache when using CACHED_ENVIRONMENT (`#6820 <https://github.com/readthedocs/readthedocs.org/pull/6820>`__)
* `@stsewd <https://github.com/stsewd>`__: Force to reinstall package (`#6817 <https://github.com/readthedocs/readthedocs.org/pull/6817>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Denormalize from_url_without_rest onto the redirects model (`#6780 <https://github.com/readthedocs/readthedocs.org/pull/6780>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Developer docs emphasize the Docker setup (`#6682 <https://github.com/readthedocs/readthedocs.org/pull/6682>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Document setting up connected accounts in dev (`#6681 <https://github.com/readthedocs/readthedocs.org/pull/6681>`__)
* `@humitos <https://github.com/humitos>`__: Return full path URL (including `.html`) on `/api/v2/docurl/` endpoint (`#6082 <https://github.com/readthedocs/readthedocs.org/pull/6082>`__)

Version 4.1.2
-------------

:Date: March 31, 2020

* `@humitos <https://github.com/humitos>`__: Report build status in a smarter way (`#6839 <https://github.com/readthedocs/readthedocs.org/pull/6839>`__)
* `@stsewd <https://github.com/stsewd>`__: Update messages-extends to latest version (`#6838 <https://github.com/readthedocs/readthedocs.org/pull/6838>`__)
* `@humitos <https://github.com/humitos>`__: Allow receiving `None` for `template_html` when sending emails (`#6834 <https://github.com/readthedocs/readthedocs.org/pull/6834>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix silly issue with sync_callback (`#6830 <https://github.com/readthedocs/readthedocs.org/pull/6830>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Show the builder in the Build admin (`#6826 <https://github.com/readthedocs/readthedocs.org/pull/6826>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Properly call sync_callback when there aren't any MULTIPLE_APP_SERVERS settings (`#6823 <https://github.com/readthedocs/readthedocs.org/pull/6823>`__)
* `@stsewd <https://github.com/stsewd>`__: Allow to override app from where to read templates (`#6821 <https://github.com/readthedocs/readthedocs.org/pull/6821>`__)
* `@humitos <https://github.com/humitos>`__: Do not save pip cache when using CACHED_ENVIRONMENT (`#6820 <https://github.com/readthedocs/readthedocs.org/pull/6820>`__)
* `@stsewd <https://github.com/stsewd>`__: Allow to override ProfileDetail view (`#6819 <https://github.com/readthedocs/readthedocs.org/pull/6819>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 4.1.1 (`#6818 <https://github.com/readthedocs/readthedocs.org/pull/6818>`__)
* `@stsewd <https://github.com/stsewd>`__: Force to reinstall package (`#6817 <https://github.com/readthedocs/readthedocs.org/pull/6817>`__)
* `@humitos <https://github.com/humitos>`__: Show uploading state (`#6816 <https://github.com/readthedocs/readthedocs.org/pull/6816>`__)
* `@humitos <https://github.com/humitos>`__: Use watchman when calling `runserver` in local development (`#6813 <https://github.com/readthedocs/readthedocs.org/pull/6813>`__)
* `@humitos <https://github.com/humitos>`__: Call proper handler (`#6811 <https://github.com/readthedocs/readthedocs.org/pull/6811>`__)
* `@humitos <https://github.com/humitos>`__: Show "Uploading" build state when uploading artifacts into storage (`#6810 <https://github.com/readthedocs/readthedocs.org/pull/6810>`__)
* `@stsewd <https://github.com/stsewd>`__: Make search compatible with sphinx 2.2.1 (`#6804 <https://github.com/readthedocs/readthedocs.org/pull/6804>`__)
* `@stsewd <https://github.com/stsewd>`__: Changes on 404, robots, and sitemap (`#6798 <https://github.com/readthedocs/readthedocs.org/pull/6798>`__)
* `@humitos <https://github.com/humitos>`__: Update guide about building consuming too much resources (`#6778 <https://github.com/readthedocs/readthedocs.org/pull/6778>`__)

Version 4.1.1
-------------

:Date: March 24, 2020

* `@stsewd <https://github.com/stsewd>`__: Force to reinstall package (`#6817 <https://github.com/readthedocs/readthedocs.org/pull/6817>`__)
* `@humitos <https://github.com/humitos>`__: Show uploading state (`#6816 <https://github.com/readthedocs/readthedocs.org/pull/6816>`__)
* `@stsewd <https://github.com/stsewd>`__: Respect order when serving 404 (version -> default_version) (`#6805 <https://github.com/readthedocs/readthedocs.org/pull/6805>`__)
* `@humitos <https://github.com/humitos>`__: Use storage.open API correctly for tar files (build cached envs) (`#6799 <https://github.com/readthedocs/readthedocs.org/pull/6799>`__)
* `@humitos <https://github.com/humitos>`__: Check 404 page once when slug and default_version is the same (`#6796 <https://github.com/readthedocs/readthedocs.org/pull/6796>`__)
* `@humitos <https://github.com/humitos>`__: Do not reset the build start time when running build env (`#6794 <https://github.com/readthedocs/readthedocs.org/pull/6794>`__)
* `@humitos <https://github.com/humitos>`__: Skip .cache directory for cached builds if it does not exist (`#6791 <https://github.com/readthedocs/readthedocs.org/pull/6791>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Remove GET args from the path passed via proxito header (`#6790 <https://github.com/readthedocs/readthedocs.org/pull/6790>`__)
* `@stsewd <https://github.com/stsewd>`__: Check for /index on pages' slug (`#6789 <https://github.com/readthedocs/readthedocs.org/pull/6789>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 4.1.0 (`#6788 <https://github.com/readthedocs/readthedocs.org/pull/6788>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Revert "Add feature flag to just completely skip sync and symlink operations (#6689)" (`#6781 <https://github.com/readthedocs/readthedocs.org/pull/6781>`__)

Version 4.1.0
-------------

:Date: March 17, 2020

* `@ericholscher <https://github.com/ericholscher>`__: Properly proxy the Proxito headers via nginx/sendfile (`#6782 <https://github.com/readthedocs/readthedocs.org/pull/6782>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Revert "Add feature flag to just completely skip sync and symlink operations (#6689)" (`#6781 <https://github.com/readthedocs/readthedocs.org/pull/6781>`__)
* `@humitos <https://github.com/humitos>`__: Upgrade django-storages to support URLs with more http methods (`#6771 <https://github.com/readthedocs/readthedocs.org/pull/6771>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Use the hotfixed version of django-messages-extends (`#6767 <https://github.com/readthedocs/readthedocs.org/pull/6767>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 4.0.3 (`#6766 <https://github.com/readthedocs/readthedocs.org/pull/6766>`__)
* `@stsewd <https://github.com/stsewd>`__: Document usage or pytest marks (`#6764 <https://github.com/readthedocs/readthedocs.org/pull/6764>`__)
* `@humitos <https://github.com/humitos>`__: Pull/Push cached environment using storage (`#6763 <https://github.com/readthedocs/readthedocs.org/pull/6763>`__)
* `@stsewd <https://github.com/stsewd>`__: Refactor search view to make use of permission_classes (`#6761 <https://github.com/readthedocs/readthedocs.org/pull/6761>`__)
* `@stsewd <https://github.com/stsewd>`__: Run proxito tests with proxito (`#6714 <https://github.com/readthedocs/readthedocs.org/pull/6714>`__)
* `@stsewd <https://github.com/stsewd>`__: Proxy footer api on docs' domains (`#6630 <https://github.com/readthedocs/readthedocs.org/pull/6630>`__)

Version 4.0.3
-------------

:Date: March 10, 2020

* `@stsewd <https://github.com/stsewd>`__: Document usage or pytest marks (`#6764 <https://github.com/readthedocs/readthedocs.org/pull/6764>`__)
* `@stsewd <https://github.com/stsewd>`__: Update some dependencies (`#6762 <https://github.com/readthedocs/readthedocs.org/pull/6762>`__)
* `@stsewd <https://github.com/stsewd>`__: Refactor search view to make use of permission_classes (`#6761 <https://github.com/readthedocs/readthedocs.org/pull/6761>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Revert "Merge pull request #6739 from readthedocs/agj/docs-tos-pdf" (`#6760 <https://github.com/readthedocs/readthedocs.org/pull/6760>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Expand the logic in our proxito mixin. (`#6759 <https://github.com/readthedocs/readthedocs.org/pull/6759>`__)
* `@comradekingu <https://github.com/comradekingu>`__: Spelling: "Set up your environment" (`#6752 <https://github.com/readthedocs/readthedocs.org/pull/6752>`__)
* `@humitos <https://github.com/humitos>`__: Use `storage.exists` on HEAD method (`#6751 <https://github.com/readthedocs/readthedocs.org/pull/6751>`__)
* `@humitos <https://github.com/humitos>`__: Pull only latest image for development (`#6750 <https://github.com/readthedocs/readthedocs.org/pull/6750>`__)
* `@humitos <https://github.com/humitos>`__: Update common submodule (`#6749 <https://github.com/readthedocs/readthedocs.org/pull/6749>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 4.0.2 (`#6741 <https://github.com/readthedocs/readthedocs.org/pull/6741>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Add TOS PDF output (`#6739 <https://github.com/readthedocs/readthedocs.org/pull/6739>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Don't call virtualenv with `--no-site-packages` (`#6738 <https://github.com/readthedocs/readthedocs.org/pull/6738>`__)
* `@GallowayJ <https://github.com/GallowayJ>`__: Drop mock dependency (`#6723 <https://github.com/readthedocs/readthedocs.org/pull/6723>`__)
* `@stsewd <https://github.com/stsewd>`__: Run proxito tests with proxito (`#6714 <https://github.com/readthedocs/readthedocs.org/pull/6714>`__)
* `@humitos <https://github.com/humitos>`__: New block on footer template to override from corporate (`#6702 <https://github.com/readthedocs/readthedocs.org/pull/6702>`__)
* `@humitos <https://github.com/humitos>`__: Point users to support email instead asking to open an issue (`#6650 <https://github.com/readthedocs/readthedocs.org/pull/6650>`__)
* `@stsewd <https://github.com/stsewd>`__: Proxy footer api on docs' domains (`#6630 <https://github.com/readthedocs/readthedocs.org/pull/6630>`__)

Version 4.0.2
-------------

:Date: March 04, 2020

* `@ericholscher <https://github.com/ericholscher>`__: Don't call virtualenv with `--no-site-packages` (`#6738 <https://github.com/readthedocs/readthedocs.org/pull/6738>`__)
* `@stsewd <https://github.com/stsewd>`__: Catch ConnectionError from request on api timing out (`#6735 <https://github.com/readthedocs/readthedocs.org/pull/6735>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 4.0.1 (`#6733 <https://github.com/readthedocs/readthedocs.org/pull/6733>`__)
* `@humitos <https://github.com/humitos>`__: Improve Proxito 404 handler to render user-facing Maze when needed (`#6726 <https://github.com/readthedocs/readthedocs.org/pull/6726>`__)

Version 4.0.1
-------------

:Date: March 03, 2020

* `@ericholscher <https://github.com/ericholscher>`__: Add feature flag for branch & tag syncing to API. (`#6729 <https://github.com/readthedocs/readthedocs.org/pull/6729>`__)
* `@stsewd <https://github.com/stsewd>`__: Don't fail a build on api timing out (`#6719 <https://github.com/readthedocs/readthedocs.org/pull/6719>`__)
* `@stsewd <https://github.com/stsewd>`__: Be explicit on privacy level for search tests (`#6713 <https://github.com/readthedocs/readthedocs.org/pull/6713>`__)
* `@stsewd <https://github.com/stsewd>`__: Make easy to run search tests in docker compose (`#6711 <https://github.com/readthedocs/readthedocs.org/pull/6711>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Docker settings improvements (`#6709 <https://github.com/readthedocs/readthedocs.org/pull/6709>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Workaround SameSite cookies (`#6708 <https://github.com/readthedocs/readthedocs.org/pull/6708>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Figure out the host IP when using Docker (`#6707 <https://github.com/readthedocs/readthedocs.org/pull/6707>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Pin the version of Azurite for docker-compose development (`#6706 <https://github.com/readthedocs/readthedocs.org/pull/6706>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 4.0.0 (`#6704 <https://github.com/readthedocs/readthedocs.org/pull/6704>`__)
* `@humitos <https://github.com/humitos>`__: Rename docker settings to fix local environment (`#6703 <https://github.com/readthedocs/readthedocs.org/pull/6703>`__)
* `@sduthil <https://github.com/sduthil>`__: API v3 doc: fix typos in URL for PATCH /versions/slug/ (`#6698 <https://github.com/readthedocs/readthedocs.org/pull/6698>`__)
* `@humitos <https://github.com/humitos>`__: Sort versions in-place to help performance (`#6696 <https://github.com/readthedocs/readthedocs.org/pull/6696>`__)
* `@humitos <https://github.com/humitos>`__: Use .iterator when sorting versions (`#6694 <https://github.com/readthedocs/readthedocs.org/pull/6694>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Add feature flag to just completely skip sync and symlink operations (`#6689 <https://github.com/readthedocs/readthedocs.org/pull/6689>`__)
* `@humitos <https://github.com/humitos>`__: Disable more loggings in development environment (`#6683 <https://github.com/readthedocs/readthedocs.org/pull/6683>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Use x-forwarded-host in local docker environment (`#6679 <https://github.com/readthedocs/readthedocs.org/pull/6679>`__)
* `@humitos <https://github.com/humitos>`__: Allow user to set `build.image: testing` in the config file (`#6676 <https://github.com/readthedocs/readthedocs.org/pull/6676>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Add azurite --loose option (`#6669 <https://github.com/readthedocs/readthedocs.org/pull/6669>`__)
* `@stsewd <https://github.com/stsewd>`__: Have more control over search tests (`#6644 <https://github.com/readthedocs/readthedocs.org/pull/6644>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Enable content security policy in report-only mode (`#6642 <https://github.com/readthedocs/readthedocs.org/pull/6642>`__)
* `@stsewd <https://github.com/stsewd>`__: Add test settings file for proxito (`#6623 <https://github.com/readthedocs/readthedocs.org/pull/6623>`__)
* `@stsewd <https://github.com/stsewd>`__: Guide: using private submodules in rtd.com (`#6527 <https://github.com/readthedocs/readthedocs.org/pull/6527>`__)

Version 4.0.0
-------------

:Date: February 25, 2020

**This release upgrades our codebase to run on Django 2.2**.
This is a breaking change,
so we have released it as our 4th major version.

* `@stsewd <https://github.com/stsewd>`__: Data migration for old integration models (`#6675 <https://github.com/readthedocs/readthedocs.org/pull/6675>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 3.12.0 (`#6674 <https://github.com/readthedocs/readthedocs.org/pull/6674>`__)
* `@humitos <https://github.com/humitos>`__: Upgrade to Django 2.2.9 (`#6494 <https://github.com/readthedocs/readthedocs.org/pull/6494>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Show message if version list truncated (`#6276 <https://github.com/readthedocs/readthedocs.org/pull/6276>`__)

Version 3.12.0
--------------

:Date: February 18, 2020

This version has two major changes:

* It updates our default docker images to stable=5.0 and latest=6.0.
* It changes our PR builder domain to `readthedocs.build`

* `@humitos <https://github.com/humitos>`__: Use PUBLIC_DOMAIN_USES_HTTPS for resolver tests (`#6673 <https://github.com/readthedocs/readthedocs.org/pull/6673>`__)
* `@stsewd <https://github.com/stsewd>`__: Always run CoreTagsTests with http (`#6671 <https://github.com/readthedocs/readthedocs.org/pull/6671>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Remove old docker settings (`#6670 <https://github.com/readthedocs/readthedocs.org/pull/6670>`__)
* `@stsewd <https://github.com/stsewd>`__: Update gitpython and django (`#6667 <https://github.com/readthedocs/readthedocs.org/pull/6667>`__)
* `@humitos <https://github.com/humitos>`__: New docker release (6.0 and testing) (`#6654 <https://github.com/readthedocs/readthedocs.org/pull/6654>`__)
* `@humitos <https://github.com/humitos>`__: Default python version per Docker image (`#6653 <https://github.com/readthedocs/readthedocs.org/pull/6653>`__)
* `@stsewd <https://github.com/stsewd>`__: Add pytest-custom_exit_code (`#6648 <https://github.com/readthedocs/readthedocs.org/pull/6648>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Initial attempt to serve PR builds at `readthedocs.build` (`#6629 <https://github.com/readthedocs/readthedocs.org/pull/6629>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Remove re-authing of users on downloads. (`#6619 <https://github.com/readthedocs/readthedocs.org/pull/6619>`__)
* `@stsewd <https://github.com/stsewd>`__: Don't trigger a sync twice on creation/deletion for GitHub (`#6614 <https://github.com/readthedocs/readthedocs.org/pull/6614>`__)
* `@s-weigand <https://github.com/s-weigand>`__: Add linkcheck test for the docs (`#6543 <https://github.com/readthedocs/readthedocs.org/pull/6543>`__)

Version 3.11.6
--------------

:Date: February 04, 2020

* `@ericholscher <https://github.com/ericholscher>`__: Note we aren't doing GSOC in 2020 (`#6618 <https://github.com/readthedocs/readthedocs.org/pull/6618>`__)
* `@ericholscher <https://github.com/ericholscher>`__: only serve x-rtd-slug project if it exists (`#6617 <https://github.com/readthedocs/readthedocs.org/pull/6617>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add check for a single_version project having a version_slug for PR builds (`#6615 <https://github.com/readthedocs/readthedocs.org/pull/6615>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix linter (`#6613 <https://github.com/readthedocs/readthedocs.org/pull/6613>`__)
* `@stsewd <https://github.com/stsewd>`__: Create unique container per sync (`#6612 <https://github.com/readthedocs/readthedocs.org/pull/6612>`__)
* `@stsewd <https://github.com/stsewd>`__: Check for None before assignment (`#6611 <https://github.com/readthedocs/readthedocs.org/pull/6611>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Raise exception when we get an InfiniteRedirect (`#6609 <https://github.com/readthedocs/readthedocs.org/pull/6609>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 3.11.5 (`#6608 <https://github.com/readthedocs/readthedocs.org/pull/6608>`__)
* `@humitos <https://github.com/humitos>`__: Avoid infinite redirect on El Proxito on 404 (`#6606 <https://github.com/readthedocs/readthedocs.org/pull/6606>`__)
* `@stsewd <https://github.com/stsewd>`__: Don't error when killing/removing non-existent container (`#6605 <https://github.com/readthedocs/readthedocs.org/pull/6605>`__)
* `@humitos <https://github.com/humitos>`__: Use proper path to download/install readthedocs-ext (`#6603 <https://github.com/readthedocs/readthedocs.org/pull/6603>`__)
* `@humitos <https://github.com/humitos>`__: Use timeout on internal API calls (`#6602 <https://github.com/readthedocs/readthedocs.org/pull/6602>`__)
* `@stsewd <https://github.com/stsewd>`__: Don't assume build isn't None in a docker build env (`#6599 <https://github.com/readthedocs/readthedocs.org/pull/6599>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix issue with pip 20.0 breaking on install (`#6598 <https://github.com/readthedocs/readthedocs.org/pull/6598>`__)
* `@stsewd <https://github.com/stsewd>`__: More protection against None (`#6597 <https://github.com/readthedocs/readthedocs.org/pull/6597>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Revert "Update celery requirements to its latest version" (`#6596 <https://github.com/readthedocs/readthedocs.org/pull/6596>`__)
* `@Blackcipher101 <https://github.com/Blackcipher101>`__: Changed documentation of Api v3 (`#6574 <https://github.com/readthedocs/readthedocs.org/pull/6574>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Use our standard auth mixin for proxito downloads (`#6572 <https://github.com/readthedocs/readthedocs.org/pull/6572>`__)
* `@humitos <https://github.com/humitos>`__: Move common docker compose configs to common repository (`#6539 <https://github.com/readthedocs/readthedocs.org/pull/6539>`__)

Version 3.11.5
--------------

:Date: January 29, 2020

* `@humitos <https://github.com/humitos>`__: Avoid infinite redirect on El Proxito on 404 (`#6606 <https://github.com/readthedocs/readthedocs.org/pull/6606>`__)
* `@humitos <https://github.com/humitos>`__: Use proper path to download/install readthedocs-ext (`#6603 <https://github.com/readthedocs/readthedocs.org/pull/6603>`__)
* `@stsewd <https://github.com/stsewd>`__: Don't assume build isn't None in a docker build env (`#6599 <https://github.com/readthedocs/readthedocs.org/pull/6599>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix issue with pip 20.0 breaking on install (`#6598 <https://github.com/readthedocs/readthedocs.org/pull/6598>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Revert "Update celery requirements to its latest version" (`#6596 <https://github.com/readthedocs/readthedocs.org/pull/6596>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove .cache from parent dir (`#6595 <https://github.com/readthedocs/readthedocs.org/pull/6595>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Release 3.11.4 again (`#6594 <https://github.com/readthedocs/readthedocs.org/pull/6594>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Release 3.11.4 (`#6593 <https://github.com/readthedocs/readthedocs.org/pull/6593>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Use our standard auth mixin for proxito downloads (`#6572 <https://github.com/readthedocs/readthedocs.org/pull/6572>`__)
* `@stsewd <https://github.com/stsewd>`__: Migrate doctype from project to version (`#6523 <https://github.com/readthedocs/readthedocs.org/pull/6523>`__)

Version 3.11.4
--------------

:Date: January 28, 2020

* `@humitos <https://github.com/humitos>`__: Disable django debug toolbar in El Proxito (`#6591 <https://github.com/readthedocs/readthedocs.org/pull/6591>`__)
* `@stsewd <https://github.com/stsewd>`__: Respect docker setting on repo sync (`#6589 <https://github.com/readthedocs/readthedocs.org/pull/6589>`__)
* `@humitos <https://github.com/humitos>`__: Merge pull request #6588 from readthedocs/humitos/support-ext (`#6588 <https://github.com/readthedocs/readthedocs.org/pull/6588>`__)
* `@humitos <https://github.com/humitos>`__: Fix argument of `update_repos` (`#6583 <https://github.com/readthedocs/readthedocs.org/pull/6583>`__)
* `@humitos <https://github.com/humitos>`__: Mount proper shared docker volume (`#6581 <https://github.com/readthedocs/readthedocs.org/pull/6581>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Use our standard auth mixin for proxito downloads (`#6572 <https://github.com/readthedocs/readthedocs.org/pull/6572>`__)
* `@stsewd <https://github.com/stsewd>`__: Delete .cache dir on wipe (`#6571 <https://github.com/readthedocs/readthedocs.org/pull/6571>`__)
* `@humitos <https://github.com/humitos>`__: Run old redirect tests via El Proxito (`#6570 <https://github.com/readthedocs/readthedocs.org/pull/6570>`__)
* `@humitos <https://github.com/humitos>`__: Remove 'build environment' from guides (`#6568 <https://github.com/readthedocs/readthedocs.org/pull/6568>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix /en/latest redirects (`#6564 <https://github.com/readthedocs/readthedocs.org/pull/6564>`__)
* `@stsewd <https://github.com/stsewd>`__: Merge pull request #6561 from stsewd/move-method (`#6561 <https://github.com/readthedocs/readthedocs.org/pull/6561>`__)
* `@stsewd <https://github.com/stsewd>`__: Use settings override in footer (`#6560 <https://github.com/readthedocs/readthedocs.org/pull/6560>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix proxito redirects breaking without a / (`#6558 <https://github.com/readthedocs/readthedocs.org/pull/6558>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove unused file (`#6557 <https://github.com/readthedocs/readthedocs.org/pull/6557>`__)
* `@mgeier <https://github.com/mgeier>`__: DOC: Change a lot of http links to https (`#6553 <https://github.com/readthedocs/readthedocs.org/pull/6553>`__)
* `@stsewd <https://github.com/stsewd>`__: Don't use an instance of VCS when isn't needed (`#6548 <https://github.com/readthedocs/readthedocs.org/pull/6548>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Add GitHub OAuth App Permission issue to PR Builder Troubleshooting docs (`#6547 <https://github.com/readthedocs/readthedocs.org/pull/6547>`__)
* `@humitos <https://github.com/humitos>`__: Move common docker compose configs to common repository (`#6539 <https://github.com/readthedocs/readthedocs.org/pull/6539>`__)
* `@preetmishra <https://github.com/preetmishra>`__: Update Transifex Integration details in Internationalization page. (`#6531 <https://github.com/readthedocs/readthedocs.org/pull/6531>`__)
* `@stsewd <https://github.com/stsewd>`__: Migrate doctype from project to version (`#6523 <https://github.com/readthedocs/readthedocs.org/pull/6523>`__)
* `@stsewd <https://github.com/stsewd>`__: Simplify docker image (`#6519 <https://github.com/readthedocs/readthedocs.org/pull/6519>`__)
* `@Parth1811 <https://github.com/Parth1811>`__: Fixes #5388 -- Added Documentation for constraint while using Conda (`#6509 <https://github.com/readthedocs/readthedocs.org/pull/6509>`__)
* `@stsewd <https://github.com/stsewd>`__: Improve test for sync_repo (`#6504 <https://github.com/readthedocs/readthedocs.org/pull/6504>`__)
* `@humitos <https://github.com/humitos>`__: Show debug toolbar when running docker compose (`#6488 <https://github.com/readthedocs/readthedocs.org/pull/6488>`__)
* `@dibyaaaaax <https://github.com/dibyaaaaax>`__: Add python examples for API v3 Documentation (`#6487 <https://github.com/readthedocs/readthedocs.org/pull/6487>`__)

Version 3.11.3
--------------

:Date: January 21, 2020

* `@ericholscher <https://github.com/ericholscher>`__: Pass proper path to redirect code (`#6555 <https://github.com/readthedocs/readthedocs.org/pull/6555>`__)
* `@Daniel-Mietchen <https://github.com/Daniel-Mietchen>`__: Fixing a broken link (`#6550 <https://github.com/readthedocs/readthedocs.org/pull/6550>`__)
* `@stsewd <https://github.com/stsewd>`__: Guide: Intersphinx in Read the Docs (`#6520 <https://github.com/readthedocs/readthedocs.org/pull/6520>`__)
* `@humitos <https://github.com/humitos>`__: Add netcat and telnet for celery debugging with rdb (`#6518 <https://github.com/readthedocs/readthedocs.org/pull/6518>`__)
* `@humitos <https://github.com/humitos>`__: Core team development standards guide (`#6517 <https://github.com/readthedocs/readthedocs.org/pull/6517>`__)
* `@dibyaaaaax <https://github.com/dibyaaaaax>`__: Add www to the broken link (`#6513 <https://github.com/readthedocs/readthedocs.org/pull/6513>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Don't allow empty tags (`#6512 <https://github.com/readthedocs/readthedocs.org/pull/6512>`__)
* `@Parth1811 <https://github.com/Parth1811>`__: Fixes #6510 -- Removed the `show_analytics` checks from the template (`#6511 <https://github.com/readthedocs/readthedocs.org/pull/6511>`__)
* `@stsewd <https://github.com/stsewd>`__: Only install node on eslint step on travis (`#6505 <https://github.com/readthedocs/readthedocs.org/pull/6505>`__)
* `@stsewd <https://github.com/stsewd>`__: Don't pass build to environment when doing a sync (`#6503 <https://github.com/readthedocs/readthedocs.org/pull/6503>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 3.11.2 (`#6502 <https://github.com/readthedocs/readthedocs.org/pull/6502>`__)
* `@Blackcipher101 <https://github.com/Blackcipher101>`__: Added "dirhtml" target (`#6500 <https://github.com/readthedocs/readthedocs.org/pull/6500>`__)
* `@humitos <https://github.com/humitos>`__: Use CELERY_APP_NAME to call the proper celery app (`#6499 <https://github.com/readthedocs/readthedocs.org/pull/6499>`__)
* `@stsewd <https://github.com/stsewd>`__: Copy path from host only when using a LocalBuildEnviroment (`#6482 <https://github.com/readthedocs/readthedocs.org/pull/6482>`__)
* `@stsewd <https://github.com/stsewd>`__: Set env variables in the same way for DockerBuildEnvironment  and Loc… (`#6481 <https://github.com/readthedocs/readthedocs.org/pull/6481>`__)
* `@stsewd <https://github.com/stsewd>`__: Use environment variable per run, not per container (`#6480 <https://github.com/readthedocs/readthedocs.org/pull/6480>`__)
* `@humitos <https://github.com/humitos>`__: Update celery requirements to its latest version (`#6448 <https://github.com/readthedocs/readthedocs.org/pull/6448>`__)
* `@stsewd <https://github.com/stsewd>`__: Execute checkout step respecting docker setting (`#6436 <https://github.com/readthedocs/readthedocs.org/pull/6436>`__)
* `@humitos <https://github.com/humitos>`__: Serve non-html at documentation domain though El Proxito (`#6419 <https://github.com/readthedocs/readthedocs.org/pull/6419>`__)

Version 3.11.2
--------------

:Date: January 08, 2020

* `@ericholscher <https://github.com/ericholscher>`__: Fix link to my blog post breaking https (`#6495 <https://github.com/readthedocs/readthedocs.org/pull/6495>`__)
* `@humitos <https://github.com/humitos>`__: Use a fixed IP for NGINX under docker-compose (`#6491 <https://github.com/readthedocs/readthedocs.org/pull/6491>`__)
* `@humitos <https://github.com/humitos>`__: Add 'index.html' to the path before using storage.url(path) (`#6476 <https://github.com/readthedocs/readthedocs.org/pull/6476>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Release 3.11.1 (`#6473 <https://github.com/readthedocs/readthedocs.org/pull/6473>`__)
* `@humitos <https://github.com/humitos>`__: Use tasks from common (including docker ones) (`#6471 <https://github.com/readthedocs/readthedocs.org/pull/6471>`__)
* `@humitos <https://github.com/humitos>`__: Upgrade Django due a security issue (`#6470 <https://github.com/readthedocs/readthedocs.org/pull/6470>`__)
* `@humitos <https://github.com/humitos>`__: Fix celery auto-reload command (`#6469 <https://github.com/readthedocs/readthedocs.org/pull/6469>`__)
* `@humitos <https://github.com/humitos>`__: Use django storage to build URL returned by El Proxito (`#6466 <https://github.com/readthedocs/readthedocs.org/pull/6466>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Handle GitHub Push events with `deleted: true` in the JSON (`#6465 <https://github.com/readthedocs/readthedocs.org/pull/6465>`__)
* `@humitos <https://github.com/humitos>`__: Serve external version through El Proxito (`#6434 <https://github.com/readthedocs/readthedocs.org/pull/6434>`__)
* `@segevfiner <https://github.com/segevfiner>`__: Remove a stray backtick from import-guide.rst (`#6362 <https://github.com/readthedocs/readthedocs.org/pull/6362>`__)

Version 3.11.1
--------------

:Date: December 18, 2019

* `@humitos <https://github.com/humitos>`__: Upgrade Django due a security issue (`#6470 <https://github.com/readthedocs/readthedocs.org/pull/6470>`__)
* `@humitos <https://github.com/humitos>`__: Use django storage to build URL returned by El Proxito (`#6466 <https://github.com/readthedocs/readthedocs.org/pull/6466>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Handle GitHub Push events with `deleted: true` in the JSON (`#6465 <https://github.com/readthedocs/readthedocs.org/pull/6465>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Update troubleshooting steps for PR builder (`#6463 <https://github.com/readthedocs/readthedocs.org/pull/6463>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add DOCKER_NORELOAD to compose settings (`#6461 <https://github.com/readthedocs/readthedocs.org/pull/6461>`__)
* `@stsewd <https://github.com/stsewd>`__: Be explicit when using setup_env (`#6451 <https://github.com/readthedocs/readthedocs.org/pull/6451>`__)
* `@keshavvinayak01 <https://github.com/keshavvinayak01>`__: Fixed remove_search_analytics issue (`#6447 <https://github.com/readthedocs/readthedocs.org/pull/6447>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Fix logic to build internal/external versions on update_repos management command (`#6442 <https://github.com/readthedocs/readthedocs.org/pull/6442>`__)
* `@humitos <https://github.com/humitos>`__: Refactor get_downloads to make one query for default_version (`#6441 <https://github.com/readthedocs/readthedocs.org/pull/6441>`__)
* `@humitos <https://github.com/humitos>`__: Do not expose env variables on external versions (`#6440 <https://github.com/readthedocs/readthedocs.org/pull/6440>`__)
* `@humitos <https://github.com/humitos>`__: Better ES settings on docker-compose (`#6439 <https://github.com/readthedocs/readthedocs.org/pull/6439>`__)
* `@humitos <https://github.com/humitos>`__: Remove global pip cache (`#6437 <https://github.com/readthedocs/readthedocs.org/pull/6437>`__)
* `@humitos <https://github.com/humitos>`__: Bring Azure storage backend classes to this repository (`#6433 <https://github.com/readthedocs/readthedocs.org/pull/6433>`__)
* `@stsewd <https://github.com/stsewd>`__: Show predefined match on automation rules admin (`#6432 <https://github.com/readthedocs/readthedocs.org/pull/6432>`__)
* `@stsewd <https://github.com/stsewd>`__: Override production domain explicitly (`#6431 <https://github.com/readthedocs/readthedocs.org/pull/6431>`__)
* `@humitos <https://github.com/humitos>`__: inv tasks to use when developing with docker (`#6418 <https://github.com/readthedocs/readthedocs.org/pull/6418>`__)
* `@piyushpalawat99 <https://github.com/piyushpalawat99>`__: Fix #6395 (`#6402 <https://github.com/readthedocs/readthedocs.org/pull/6402>`__)
* `@stsewd <https://github.com/stsewd>`__: Only pass public versions to html context (`#6118 <https://github.com/readthedocs/readthedocs.org/pull/6118>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add an "Edit Versions" listing to the Admin menu (`#6110 <https://github.com/readthedocs/readthedocs.org/pull/6110>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Extend webhook notifications with build status (`#5621 <https://github.com/readthedocs/readthedocs.org/pull/5621>`__)

Version 3.11.0
--------------

:Date: December 03, 2019

* `@davidfischer <https://github.com/davidfischer>`__: Use media availability instead of querying the filesystem (`#6428 <https://github.com/readthedocs/readthedocs.org/pull/6428>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove beta note about sharing by password and header auth (`#6426 <https://github.com/readthedocs/readthedocs.org/pull/6426>`__)
* `@humitos <https://github.com/humitos>`__: Use trigger_build for update_repos command (`#6422 <https://github.com/readthedocs/readthedocs.org/pull/6422>`__)
* `@humitos <https://github.com/humitos>`__: Add more supported field to APIv3 docs (`#6417 <https://github.com/readthedocs/readthedocs.org/pull/6417>`__)
* `@humitos <https://github.com/humitos>`__: Add AuthenticationMiddleware to El Proxito tests (`#6416 <https://github.com/readthedocs/readthedocs.org/pull/6416>`__)
* `@stsewd <https://github.com/stsewd>`__: Update docs on sharing (`#6410 <https://github.com/readthedocs/readthedocs.org/pull/6410>`__)
* `@humitos <https://github.com/humitos>`__: Use WORKDIR to cd into a directory in Dockerfile (`#6409 <https://github.com/readthedocs/readthedocs.org/pull/6409>`__)
* `@humitos <https://github.com/humitos>`__: Use /data inside Azurite container to persist data (`#6407 <https://github.com/readthedocs/readthedocs.org/pull/6407>`__)
* `@humitos <https://github.com/humitos>`__: Serve non-html files from nginx (X-Accel-Redirect) (`#6404 <https://github.com/readthedocs/readthedocs.org/pull/6404>`__)
* `@humitos <https://github.com/humitos>`__: Perform redirects at DB level (`#6398 <https://github.com/readthedocs/readthedocs.org/pull/6398>`__)
* `@humitos <https://github.com/humitos>`__: Allow to extend El Proxito views from commercial (`#6397 <https://github.com/readthedocs/readthedocs.org/pull/6397>`__)
* `@humitos <https://github.com/humitos>`__: Migrate El Proxito views to class-based views (`#6396 <https://github.com/readthedocs/readthedocs.org/pull/6396>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Fix CSS and how we were handling html in automation rule UI (`#6394 <https://github.com/readthedocs/readthedocs.org/pull/6394>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 3.10.0 (`#6391 <https://github.com/readthedocs/readthedocs.org/pull/6391>`__)
* `@stsewd <https://github.com/stsewd>`__: Set privacy level explicitly (`#6390 <https://github.com/readthedocs/readthedocs.org/pull/6390>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Redirect index files in proxito instead of serving (`#6387 <https://github.com/readthedocs/readthedocs.org/pull/6387>`__)
* `@humitos <https://github.com/humitos>`__: Fully working docker-compose file (`#6295 <https://github.com/readthedocs/readthedocs.org/pull/6295>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Refactor Subproject validation to use it for Forms and API (`#6285 <https://github.com/readthedocs/readthedocs.org/pull/6285>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Refactor Gold Views (`#6272 <https://github.com/readthedocs/readthedocs.org/pull/6272>`__)
* `@stsewd <https://github.com/stsewd>`__: Add docs for automatin rules (`#6072 <https://github.com/readthedocs/readthedocs.org/pull/6072>`__)

Version 3.10.0
--------------

:Date: November 19, 2019

* `@stsewd <https://github.com/stsewd>`__: Set privacy level explicitly (`#6390 <https://github.com/readthedocs/readthedocs.org/pull/6390>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Redirect index files in proxito instead of serving (`#6387 <https://github.com/readthedocs/readthedocs.org/pull/6387>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix search indexing (`#6380 <https://github.com/readthedocs/readthedocs.org/pull/6380>`__)
* `@humitos <https://github.com/humitos>`__: Include creditcard.png image (`#6379 <https://github.com/readthedocs/readthedocs.org/pull/6379>`__)
* `@stsewd <https://github.com/stsewd>`__: Silent curl (`#6377 <https://github.com/readthedocs/readthedocs.org/pull/6377>`__)
* `@stsewd <https://github.com/stsewd>`__: Use github actions to trigger tests in corporate (`#6376 <https://github.com/readthedocs/readthedocs.org/pull/6376>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Show only users projects in the APIv3 browsable form (`#6374 <https://github.com/readthedocs/readthedocs.org/pull/6374>`__)
* `@humitos <https://github.com/humitos>`__: Release 3.9.0 (`#6371 <https://github.com/readthedocs/readthedocs.org/pull/6371>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Pin the node dependencies with a package-lock (`#6370 <https://github.com/readthedocs/readthedocs.org/pull/6370>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Small optimization to not compute the highest version when it isn't displayed (`#6360 <https://github.com/readthedocs/readthedocs.org/pull/6360>`__)
* `@krptic07 <https://github.com/krptic07>`__: remove rss feed (`#6348 <https://github.com/readthedocs/readthedocs.org/pull/6348>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 44 (`#6347 <https://github.com/readthedocs/readthedocs.org/pull/6347>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Port additional features to proxito (`#6286 <https://github.com/readthedocs/readthedocs.org/pull/6286>`__)
* `@stsewd <https://github.com/stsewd>`__: Add docs for automatin rules (`#6072 <https://github.com/readthedocs/readthedocs.org/pull/6072>`__)
* `@stsewd <https://github.com/stsewd>`__: Implement UI for automation rules (`#5996 <https://github.com/readthedocs/readthedocs.org/pull/5996>`__)

Version 3.9.0
-------------

:Date: November 12, 2019

* `@davidfischer <https://github.com/davidfischer>`__: Pin the node dependencies with a package-lock (`#6370 <https://github.com/readthedocs/readthedocs.org/pull/6370>`__)
* `@humitos <https://github.com/humitos>`__: Force PUBLIC_DOMAIN_USES_HTTPS on version compare tests (`#6367 <https://github.com/readthedocs/readthedocs.org/pull/6367>`__)
* `@segevfiner <https://github.com/segevfiner>`__: Remove a stray backtick from import-guide.rst (`#6362 <https://github.com/readthedocs/readthedocs.org/pull/6362>`__)
* `@stsewd <https://github.com/stsewd>`__: Don't compare inactive or non build versions (`#6361 <https://github.com/readthedocs/readthedocs.org/pull/6361>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix test (`#6358 <https://github.com/readthedocs/readthedocs.org/pull/6358>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Change the default of proxied_api_host to api_host (`#6355 <https://github.com/readthedocs/readthedocs.org/pull/6355>`__)
* `@stsewd <https://github.com/stsewd>`__: Dont link to dashboard from footer (`#6353 <https://github.com/readthedocs/readthedocs.org/pull/6353>`__)
* `@humitos <https://github.com/humitos>`__: Upgrade django-storages (`#6339 <https://github.com/readthedocs/readthedocs.org/pull/6339>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 43 (`#6334 <https://github.com/readthedocs/readthedocs.org/pull/6334>`__)
* `@KartikKapil <https://github.com/KartikKapil>`__: added previous year gsoc projects (`#6333 <https://github.com/readthedocs/readthedocs.org/pull/6333>`__)
* `@stsewd <https://github.com/stsewd>`__: Support 6.0rc1 build image (`#6329 <https://github.com/readthedocs/readthedocs.org/pull/6329>`__)
* `@stsewd <https://github.com/stsewd>`__: Don't error on non existing version (`#6325 <https://github.com/readthedocs/readthedocs.org/pull/6325>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove files from storage and delete indexes from ES when no longer needed (`#6323 <https://github.com/readthedocs/readthedocs.org/pull/6323>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix eslint (`#6317 <https://github.com/readthedocs/readthedocs.org/pull/6317>`__)
* `@humitos <https://github.com/humitos>`__: Revert "Adding RTD prefix for docker only in setting.py and all… (`#6315 <https://github.com/readthedocs/readthedocs.org/pull/6315>`__)
* `@anindyamanna <https://github.com/anindyamanna>`__: Fixed Broken links (`#6300 <https://github.com/readthedocs/readthedocs.org/pull/6300>`__)
* `@stsewd <https://github.com/stsewd>`__: Use sync instead of copy for blob storage (`#6298 <https://github.com/readthedocs/readthedocs.org/pull/6298>`__)
* `@sciencewhiz <https://github.com/sciencewhiz>`__: Fix missing word in wipe guide (`#6294 <https://github.com/readthedocs/readthedocs.org/pull/6294>`__)
* `@jaferkhan <https://github.com/jaferkhan>`__: Removed unused code from view and template (#6250) (`#6288 <https://github.com/readthedocs/readthedocs.org/pull/6288>`__)
* `@stsewd <https://github.com/stsewd>`__: Rename test name (`#6283 <https://github.com/readthedocs/readthedocs.org/pull/6283>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Store version media availability (`#6278 <https://github.com/readthedocs/readthedocs.org/pull/6278>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Link to the terms of service (`#6277 <https://github.com/readthedocs/readthedocs.org/pull/6277>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: API V3 Subproject Creation Bug fix (`#6275 <https://github.com/readthedocs/readthedocs.org/pull/6275>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix footer (`#6274 <https://github.com/readthedocs/readthedocs.org/pull/6274>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix tests (`#6269 <https://github.com/readthedocs/readthedocs.org/pull/6269>`__)
* `@stsewd <https://github.com/stsewd>`__: Refactor profile's views (`#6267 <https://github.com/readthedocs/readthedocs.org/pull/6267>`__)
* `@humitos <https://github.com/humitos>`__: Default to None when using the Serializer as Form for Browsable… (`#6266 <https://github.com/readthedocs/readthedocs.org/pull/6266>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix inactive version list not showing when no results returned (`#6264 <https://github.com/readthedocs/readthedocs.org/pull/6264>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Downgrade django-storges. (`#6263 <https://github.com/readthedocs/readthedocs.org/pull/6263>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 3.8.0 (`#6262 <https://github.com/readthedocs/readthedocs.org/pull/6262>`__)
* `@stsewd <https://github.com/stsewd>`__: Update doccs version detail (api v3) (`#6259 <https://github.com/readthedocs/readthedocs.org/pull/6259>`__)
* `@stsewd <https://github.com/stsewd>`__: Merge #6176 to master (`#6258 <https://github.com/readthedocs/readthedocs.org/pull/6258>`__)
* `@humitos <https://github.com/humitos>`__: Remove privacy_level field from APIv3 (`#6257 <https://github.com/readthedocs/readthedocs.org/pull/6257>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Redirect /projects/ URL to /dashboard/ (`#6255 <https://github.com/readthedocs/readthedocs.org/pull/6255>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Allow project badges for private version (`#6252 <https://github.com/readthedocs/readthedocs.org/pull/6252>`__)
* `@stsewd <https://github.com/stsewd>`__: Add pub_date to project admin (`#6244 <https://github.com/readthedocs/readthedocs.org/pull/6244>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Allow only post requests for delete views (`#6242 <https://github.com/readthedocs/readthedocs.org/pull/6242>`__)
* `@Iamshankhadeep <https://github.com/Iamshankhadeep>`__: Changing created to modified time (`#6234 <https://github.com/readthedocs/readthedocs.org/pull/6234>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Initial stub of proxito (`#6226 <https://github.com/readthedocs/readthedocs.org/pull/6226>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Add Better error message for lists in config file (`#6200 <https://github.com/readthedocs/readthedocs.org/pull/6200>`__)
* `@stsewd <https://github.com/stsewd>`__: Put view under login (`#6193 <https://github.com/readthedocs/readthedocs.org/pull/6193>`__)
* `@humitos <https://github.com/humitos>`__: Ship API v3 (`#6169 <https://github.com/readthedocs/readthedocs.org/pull/6169>`__)
* `@stsewd <https://github.com/stsewd>`__: Protection against ReDoS (`#6163 <https://github.com/readthedocs/readthedocs.org/pull/6163>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Optimize json parsing (`#6160 <https://github.com/readthedocs/readthedocs.org/pull/6160>`__)
* `@tapaswenipathak <https://github.com/tapaswenipathak>`__: Added missing i18n for footer api (`#6144 <https://github.com/readthedocs/readthedocs.org/pull/6144>`__)
* `@stsewd <https://github.com/stsewd>`__: Use different setting for footer api url (`#6131 <https://github.com/readthedocs/readthedocs.org/pull/6131>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Remove 'highlight' URL param from search results (`#6087 <https://github.com/readthedocs/readthedocs.org/pull/6087>`__)
* `@Iamshankhadeep <https://github.com/Iamshankhadeep>`__: Adding RTD prefix for docker only in setting.py and all other places where is needed (`#6040 <https://github.com/readthedocs/readthedocs.org/pull/6040>`__)
* `@stsewd <https://github.com/stsewd>`__: Design doc for organizations (`#5958 <https://github.com/readthedocs/readthedocs.org/pull/5958>`__)

Version 3.8.0
-------------

:Date: October 09, 2019

* `@stsewd <https://github.com/stsewd>`__: Update doccs version detail (api v3) (`#6259 <https://github.com/readthedocs/readthedocs.org/pull/6259>`__)
* `@stsewd <https://github.com/stsewd>`__: Merge #6176 to master (`#6258 <https://github.com/readthedocs/readthedocs.org/pull/6258>`__)
* `@humitos <https://github.com/humitos>`__: Remove privacy_level field from APIv3 (`#6257 <https://github.com/readthedocs/readthedocs.org/pull/6257>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Redirect /projects/ URL to /dashboard/ (`#6255 <https://github.com/readthedocs/readthedocs.org/pull/6255>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Allow project badges for private version (`#6252 <https://github.com/readthedocs/readthedocs.org/pull/6252>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 40 (`#6251 <https://github.com/readthedocs/readthedocs.org/pull/6251>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Add note about specifying dependencies (`#6248 <https://github.com/readthedocs/readthedocs.org/pull/6248>`__)
* `@stsewd <https://github.com/stsewd>`__: Add pub_date to project admin (`#6244 <https://github.com/readthedocs/readthedocs.org/pull/6244>`__)
* `@humitos <https://github.com/humitos>`__: Do not use --cache-dir for pip if CLEAN_AFTER_BUILD is enabled (`#6239 <https://github.com/readthedocs/readthedocs.org/pull/6239>`__)
* `@stsewd <https://github.com/stsewd>`__: Update pytest (`#6233 <https://github.com/readthedocs/readthedocs.org/pull/6233>`__)
* `@iambenzo <https://github.com/iambenzo>`__: remove /projects/ (`#6228 <https://github.com/readthedocs/readthedocs.org/pull/6228>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Initial stub of proxito (`#6226 <https://github.com/readthedocs/readthedocs.org/pull/6226>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Improve the version listview (`#6224 <https://github.com/readthedocs/readthedocs.org/pull/6224>`__)
* `@stsewd <https://github.com/stsewd>`__: Override production media artifacts on test (`#6220 <https://github.com/readthedocs/readthedocs.org/pull/6220>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Customize default build media storage for the FS (`#6215 <https://github.com/readthedocs/readthedocs.org/pull/6215>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Release 3.7.5 (`#6214 <https://github.com/readthedocs/readthedocs.org/pull/6214>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove dead code (`#6213 <https://github.com/readthedocs/readthedocs.org/pull/6213>`__)
* `@stsewd <https://github.com/stsewd>`__: Only use the sphinx way to mock (`#6212 <https://github.com/readthedocs/readthedocs.org/pull/6212>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Only Build Active Versions from Build List Page Form (`#6205 <https://github.com/readthedocs/readthedocs.org/pull/6205>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Make raw_config private (`#6199 <https://github.com/readthedocs/readthedocs.org/pull/6199>`__)
* `@Iamshankhadeep <https://github.com/Iamshankhadeep>`__: moved expandable_fields to meta class (`#6198 <https://github.com/readthedocs/readthedocs.org/pull/6198>`__)
* `@stsewd <https://github.com/stsewd>`__: Put view under login (`#6193 <https://github.com/readthedocs/readthedocs.org/pull/6193>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Remove pie-chart from search analytics page (`#6192 <https://github.com/readthedocs/readthedocs.org/pull/6192>`__)
* `@stsewd <https://github.com/stsewd>`__: Refactor SearchAnalytics view (`#6190 <https://github.com/readthedocs/readthedocs.org/pull/6190>`__)
* `@stsewd <https://github.com/stsewd>`__: Refactor ProjectRedirects views (`#6187 <https://github.com/readthedocs/readthedocs.org/pull/6187>`__)
* `@stsewd <https://github.com/stsewd>`__: Refactor ProjectTranslations views (`#6185 <https://github.com/readthedocs/readthedocs.org/pull/6185>`__)
* `@stsewd <https://github.com/stsewd>`__: Refactor ProjectNotications views (`#6183 <https://github.com/readthedocs/readthedocs.org/pull/6183>`__)
* `@stsewd <https://github.com/stsewd>`__: Refactor views ProjectUsers (`#6178 <https://github.com/readthedocs/readthedocs.org/pull/6178>`__)
* `@humitos <https://github.com/humitos>`__: Create subproject relationship via APIv3 endpoint (`#6176 <https://github.com/readthedocs/readthedocs.org/pull/6176>`__)
* `@stsewd <https://github.com/stsewd>`__: Refactor views ProjectVersion (`#6175 <https://github.com/readthedocs/readthedocs.org/pull/6175>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Add terms of service (`#6174 <https://github.com/readthedocs/readthedocs.org/pull/6174>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Document connected account permissions (`#6172 <https://github.com/readthedocs/readthedocs.org/pull/6172>`__)
* `@stsewd <https://github.com/stsewd>`__: Refactor views projects (`#6171 <https://github.com/readthedocs/readthedocs.org/pull/6171>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Optimize json parsing (`#6160 <https://github.com/readthedocs/readthedocs.org/pull/6160>`__)
* `@humitos <https://github.com/humitos>`__: APIv3 endpoint: allow to modify a Project once it's imported (`#5952 <https://github.com/readthedocs/readthedocs.org/pull/5952>`__)

Version 3.7.5
-------------

:Date: September 26, 2019

* `@davidfischer <https://github.com/davidfischer>`__: Remove if storage blocks (`#6191 <https://github.com/readthedocs/readthedocs.org/pull/6191>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Update security docs (`#6179 <https://github.com/readthedocs/readthedocs.org/pull/6179>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Add the private spamfighting module to INSTALLED_APPS (`#6177 <https://github.com/readthedocs/readthedocs.org/pull/6177>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Document connected account permissions (`#6172 <https://github.com/readthedocs/readthedocs.org/pull/6172>`__)
* `@stsewd <https://github.com/stsewd>`__: Require login for old redirect (`#6170 <https://github.com/readthedocs/readthedocs.org/pull/6170>`__)
* `@humitos <https://github.com/humitos>`__: Remove old and unused code (`#6167 <https://github.com/readthedocs/readthedocs.org/pull/6167>`__)
* `@stsewd <https://github.com/stsewd>`__: Clean up views (`#6166 <https://github.com/readthedocs/readthedocs.org/pull/6166>`__)
* `@stsewd <https://github.com/stsewd>`__: Update docs for sharing (`#6164 <https://github.com/readthedocs/readthedocs.org/pull/6164>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 36 (`#6158 <https://github.com/readthedocs/readthedocs.org/pull/6158>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Remove PR Builder Project Idea from RTD GSoC Docs (`#6147 <https://github.com/readthedocs/readthedocs.org/pull/6147>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Serialize time in search queries properly (`#6142 <https://github.com/readthedocs/readthedocs.org/pull/6142>`__)
* `@humitos <https://github.com/humitos>`__: Allow to extend DomainCreate view (`#6139 <https://github.com/readthedocs/readthedocs.org/pull/6139>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Integration Re-sync Bug Fix (`#6124 <https://github.com/readthedocs/readthedocs.org/pull/6124>`__)
* `@stsewd <https://github.com/stsewd>`__: Don't log BuildEnvironmentWarning as error (`#6112 <https://github.com/readthedocs/readthedocs.org/pull/6112>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Add Search Guide (`#6101 <https://github.com/readthedocs/readthedocs.org/pull/6101>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Add PR Builder guide to docs (`#6093 <https://github.com/readthedocs/readthedocs.org/pull/6093>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Record search queries smartly (`#6088 <https://github.com/readthedocs/readthedocs.org/pull/6088>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Remove 'highlight' URL param from search results (`#6087 <https://github.com/readthedocs/readthedocs.org/pull/6087>`__)

Version 3.7.4
-------------

:Date: September 05, 2019

* `@ericholscher <https://github.com/ericholscher>`__: Remove paid support callout (`#6140 <https://github.com/readthedocs/readthedocs.org/pull/6140>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix IntegrationAdmin with raw_id_fields for Projects (`#6136 <https://github.com/readthedocs/readthedocs.org/pull/6136>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix link to html_extra_path (`#6135 <https://github.com/readthedocs/readthedocs.org/pull/6135>`__)
* `@stsewd <https://github.com/stsewd>`__: Move out authorization from FooterHTML view (`#6133 <https://github.com/readthedocs/readthedocs.org/pull/6133>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Add setting for always cleaning the build post-build (`#6132 <https://github.com/readthedocs/readthedocs.org/pull/6132>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 35 (`#6129 <https://github.com/readthedocs/readthedocs.org/pull/6129>`__)
* `@stsewd <https://github.com/stsewd>`__:  Refactor footer_html view to class (`#6125 <https://github.com/readthedocs/readthedocs.org/pull/6125>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Use raw_id_fields in the TokenAdmin (`#6116 <https://github.com/readthedocs/readthedocs.org/pull/6116>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Fixed footer ads supported on all themes (`#6115 <https://github.com/readthedocs/readthedocs.org/pull/6115>`__)
* `@stsewd <https://github.com/stsewd>`__: Don't log BuildEnvironmentWarning as error (`#6112 <https://github.com/readthedocs/readthedocs.org/pull/6112>`__)
* `@pllim <https://github.com/pllim>`__: Use the force when fetching with Git (`#6109 <https://github.com/readthedocs/readthedocs.org/pull/6109>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Record search queries smartly (`#6088 <https://github.com/readthedocs/readthedocs.org/pull/6088>`__)
* `@stsewd <https://github.com/stsewd>`__: Add move method to automation rule (`#5998 <https://github.com/readthedocs/readthedocs.org/pull/5998>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Index more domain data into elasticsearch (`#5979 <https://github.com/readthedocs/readthedocs.org/pull/5979>`__)

Version 3.7.3
-------------

:Date: August 27, 2019

* `@pllim <https://github.com/pllim>`__: Use the force when fetching with Git (`#6109 <https://github.com/readthedocs/readthedocs.org/pull/6109>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Small improvements to the SEO guide (`#6105 <https://github.com/readthedocs/readthedocs.org/pull/6105>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Update intersphinx mapping with canonical sources (`#6085 <https://github.com/readthedocs/readthedocs.org/pull/6085>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Fix lingering 500 issues (`#6079 <https://github.com/readthedocs/readthedocs.org/pull/6079>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Technical docs SEO guide (`#6077 <https://github.com/readthedocs/readthedocs.org/pull/6077>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: GitLab Build Status Reporting for PR Builder (`#6076 <https://github.com/readthedocs/readthedocs.org/pull/6076>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Update ad details docs (`#6074 <https://github.com/readthedocs/readthedocs.org/pull/6074>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Gold makes projects ad-free again (`#6073 <https://github.com/readthedocs/readthedocs.org/pull/6073>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Auto Sync and Re-Sync for Manually Created Integrations (`#6071 <https://github.com/readthedocs/readthedocs.org/pull/6071>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 32 (`#6067 <https://github.com/readthedocs/readthedocs.org/pull/6067>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: PR Builder GitLab Integration (`#6066 <https://github.com/readthedocs/readthedocs.org/pull/6066>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Send media downloads to analytics (`#6063 <https://github.com/readthedocs/readthedocs.org/pull/6063>`__)
* `@davidfischer <https://github.com/davidfischer>`__: IPv6 in X-Forwarded-For fix (`#6062 <https://github.com/readthedocs/readthedocs.org/pull/6062>`__)
* `@humitos <https://github.com/humitos>`__: Remove warning about beta state of conda support (`#6056 <https://github.com/readthedocs/readthedocs.org/pull/6056>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Update GitLab Webhook creating to enable merge request events (`#6055 <https://github.com/readthedocs/readthedocs.org/pull/6055>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 3.7.2 (`#6054 <https://github.com/readthedocs/readthedocs.org/pull/6054>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Update feature flags docs (`#6053 <https://github.com/readthedocs/readthedocs.org/pull/6053>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Add indelx.html filename to the external doc url (`#6051 <https://github.com/readthedocs/readthedocs.org/pull/6051>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Search analytics improvements (`#6050 <https://github.com/readthedocs/readthedocs.org/pull/6050>`__)
* `@stsewd <https://github.com/stsewd>`__: Sort versions taking into consideration the vcs type (`#6049 <https://github.com/readthedocs/readthedocs.org/pull/6049>`__)
* `@humitos <https://github.com/humitos>`__: Avoid returning invalid domain when using USE_SUBDOMAIN=True in dev (`#6026 <https://github.com/readthedocs/readthedocs.org/pull/6026>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Search analytics (`#6019 <https://github.com/readthedocs/readthedocs.org/pull/6019>`__)
* `@tapaswenipathak <https://github.com/tapaswenipathak>`__: Remove django-guardian model (`#6005 <https://github.com/readthedocs/readthedocs.org/pull/6005>`__)
* `@stsewd <https://github.com/stsewd>`__: Add manager and description field to AutomationRule model (`#5995 <https://github.com/readthedocs/readthedocs.org/pull/5995>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Cleanup project tags (`#5983 <https://github.com/readthedocs/readthedocs.org/pull/5983>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Search indexing with storage (`#5854 <https://github.com/readthedocs/readthedocs.org/pull/5854>`__)
* `@wilvk <https://github.com/wilvk>`__: fix sphinx startup guide to not to fail on rtd build as per #2569 (`#5753 <https://github.com/readthedocs/readthedocs.org/pull/5753>`__)

Version 3.7.2
-------------

:Date: August 08, 2019

* `@dojutsu-user <https://github.com/dojutsu-user>`__: Update feature flags docs (`#6053 <https://github.com/readthedocs/readthedocs.org/pull/6053>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Add indelx.html filename to the external doc url (`#6051 <https://github.com/readthedocs/readthedocs.org/pull/6051>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Search analytics improvements (`#6050 <https://github.com/readthedocs/readthedocs.org/pull/6050>`__)
* `@stsewd <https://github.com/stsewd>`__: Sort versions taking into consideration the vcs type (`#6049 <https://github.com/readthedocs/readthedocs.org/pull/6049>`__)
* `@ericholscher <https://github.com/ericholscher>`__: When called via SyncRepositoryTaskStep this doesn't exist (`#6048 <https://github.com/readthedocs/readthedocs.org/pull/6048>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Fix around community ads with an explicit ad placement (`#6047 <https://github.com/readthedocs/readthedocs.org/pull/6047>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 3.7.1 (`#6045 <https://github.com/readthedocs/readthedocs.org/pull/6045>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Do not delete media storage files for external version (`#6035 <https://github.com/readthedocs/readthedocs.org/pull/6035>`__)
* `@tapaswenipathak <https://github.com/tapaswenipathak>`__: Remove django-guardian model (`#6005 <https://github.com/readthedocs/readthedocs.org/pull/6005>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Cleanup project tags (`#5983 <https://github.com/readthedocs/readthedocs.org/pull/5983>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Search indexing with storage (`#5854 <https://github.com/readthedocs/readthedocs.org/pull/5854>`__)

Version 3.7.1
-------------

:Date: August 07, 2019

* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 31 (`#6042 <https://github.com/readthedocs/readthedocs.org/pull/6042>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Fix issue with save on translation form (`#6037 <https://github.com/readthedocs/readthedocs.org/pull/6037>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Do not delete media storage files for external version (`#6035 <https://github.com/readthedocs/readthedocs.org/pull/6035>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Do not show wipe version message on build details page for External versions (`#6034 <https://github.com/readthedocs/readthedocs.org/pull/6034>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Send site notification on Build status reporting failure and follow DRY (`#6033 <https://github.com/readthedocs/readthedocs.org/pull/6033>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Use Read the Docs for Business everywhere (`#6029 <https://github.com/readthedocs/readthedocs.org/pull/6029>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Remove project count on homepage (`#6028 <https://github.com/readthedocs/readthedocs.org/pull/6028>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix missing arg in tests (`#6022 <https://github.com/readthedocs/readthedocs.org/pull/6022>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Update get_absolute_url for External Versions (`#6020 <https://github.com/readthedocs/readthedocs.org/pull/6020>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Search analytics (`#6019 <https://github.com/readthedocs/readthedocs.org/pull/6019>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Fix issues around remote repository for sending Build status reports (`#6017 <https://github.com/readthedocs/readthedocs.org/pull/6017>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Expand the scope between `before_vcs` and `after_vcs` (`#6015 <https://github.com/readthedocs/readthedocs.org/pull/6015>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Handle .x in version sorting (`#6012 <https://github.com/readthedocs/readthedocs.org/pull/6012>`__)
* `@tapaswenipathak <https://github.com/tapaswenipathak>`__: Update note (`#6008 <https://github.com/readthedocs/readthedocs.org/pull/6008>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Link to Read the Docs for Business docs from relevant sections (`#6004 <https://github.com/readthedocs/readthedocs.org/pull/6004>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Note RTD for Biz requires SSL for custom domains (`#6003 <https://github.com/readthedocs/readthedocs.org/pull/6003>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Allow searching in the Django Admin for gold (`#6001 <https://github.com/readthedocs/readthedocs.org/pull/6001>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: More explicit tests for build managers (`#6000 <https://github.com/readthedocs/readthedocs.org/pull/6000>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Fix logic involving creation of Sphinx Domains (`#5997 <https://github.com/readthedocs/readthedocs.org/pull/5997>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Fix: no highlighting of matched keywords in search results (`#5994 <https://github.com/readthedocs/readthedocs.org/pull/5994>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Do not copy external version artifacts twice (`#5992 <https://github.com/readthedocs/readthedocs.org/pull/5992>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Update GitHub build status details URL (`#5987 <https://github.com/readthedocs/readthedocs.org/pull/5987>`__)
* `@humitos <https://github.com/humitos>`__: Missing list.extend line when appending conda dependencies (`#5986 <https://github.com/readthedocs/readthedocs.org/pull/5986>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Fix github build status reporting bug (`#5985 <https://github.com/readthedocs/readthedocs.org/pull/5985>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Use try...catch block with underscore.js template. (`#5984 <https://github.com/readthedocs/readthedocs.org/pull/5984>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Cleanup project tags (`#5983 <https://github.com/readthedocs/readthedocs.org/pull/5983>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 3.7.0 (`#5982 <https://github.com/readthedocs/readthedocs.org/pull/5982>`__)
* `@stsewd <https://github.com/stsewd>`__: More explicit tests for version managers (`#5981 <https://github.com/readthedocs/readthedocs.org/pull/5981>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Search Fix: `section_subtitle_link` is not defined (`#5980 <https://github.com/readthedocs/readthedocs.org/pull/5980>`__)
* `@stsewd <https://github.com/stsewd>`__: More explicit setup for tests (`#5977 <https://github.com/readthedocs/readthedocs.org/pull/5977>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 29 (`#5975 <https://github.com/readthedocs/readthedocs.org/pull/5975>`__)
* `@stsewd <https://github.com/stsewd>`__: Update gitpython (`#5974 <https://github.com/readthedocs/readthedocs.org/pull/5974>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Community only ads for more themes (`#5973 <https://github.com/readthedocs/readthedocs.org/pull/5973>`__)
* `@darrowco <https://github.com/darrowco>`__: updated to psycopg2 (2.8.3) (`#5965 <https://github.com/readthedocs/readthedocs.org/pull/5965>`__)
* `@humitos <https://github.com/humitos>`__: Append core requirements to Conda environment file (`#5956 <https://github.com/readthedocs/readthedocs.org/pull/5956>`__)
* `@humitos <https://github.com/humitos>`__: Show APIv3 Token under Profile settings (`#5954 <https://github.com/readthedocs/readthedocs.org/pull/5954>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove skip submodules flag (`#5406 <https://github.com/readthedocs/readthedocs.org/pull/5406>`__)

Version 3.7.0
-------------

:Date: July 23, 2019

* `@dojutsu-user <https://github.com/dojutsu-user>`__: Search Fix: `section_subtitle_link` is not defined (`#5980 <https://github.com/readthedocs/readthedocs.org/pull/5980>`__)
* `@stsewd <https://github.com/stsewd>`__: More explicit setup for tests (`#5977 <https://github.com/readthedocs/readthedocs.org/pull/5977>`__)
* `@stsewd <https://github.com/stsewd>`__: Update gitpython (`#5974 <https://github.com/readthedocs/readthedocs.org/pull/5974>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Community only ads for more themes (`#5973 <https://github.com/readthedocs/readthedocs.org/pull/5973>`__)
* ``@kittenking``: Fix typos across readthedocs.org repository (`#5971 <https://github.com/readthedocs/readthedocs.org/pull/5971>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Fix: `parse_json` also including html in titles (`#5970 <https://github.com/readthedocs/readthedocs.org/pull/5970>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: update external version check for notification task (`#5969 <https://github.com/readthedocs/readthedocs.org/pull/5969>`__)
* `@pranay414 <https://github.com/pranay414>`__: Improve error message for invalid submodule URLs (`#5957 <https://github.com/readthedocs/readthedocs.org/pull/5957>`__)
* `@humitos <https://github.com/humitos>`__: Append core requirements to Conda environment file (`#5956 <https://github.com/readthedocs/readthedocs.org/pull/5956>`__)
* `@Abhi-khandelwal <https://github.com/Abhi-khandelwal>`__: Exclude Spam projects count from total_projects count (`#5955 <https://github.com/readthedocs/readthedocs.org/pull/5955>`__)
* `@humitos <https://github.com/humitos>`__: Show APIv3 Token under Profile settings (`#5954 <https://github.com/readthedocs/readthedocs.org/pull/5954>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 3.6.1 (`#5953 <https://github.com/readthedocs/readthedocs.org/pull/5953>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Missed a couple places to set READTHEDOCS_LANGUAGE (`#5951 <https://github.com/readthedocs/readthedocs.org/pull/5951>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Hotfix: Return empty dict when no highlight dict is present (`#5950 <https://github.com/readthedocs/readthedocs.org/pull/5950>`__)
* `@humitos <https://github.com/humitos>`__: Use a cwd where the user has access inside the container (`#5949 <https://github.com/readthedocs/readthedocs.org/pull/5949>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Small Changes to PR Builder Code (`#5948 <https://github.com/readthedocs/readthedocs.org/pull/5948>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: update build status message for github (`#5947 <https://github.com/readthedocs/readthedocs.org/pull/5947>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Integrate indoc search into our prod docs (`#5946 <https://github.com/readthedocs/readthedocs.org/pull/5946>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Explicitly delete SphinxDomain objects from previous versions (`#5945 <https://github.com/readthedocs/readthedocs.org/pull/5945>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Properly return None when there's no highlight on a hit. (`#5944 <https://github.com/readthedocs/readthedocs.org/pull/5944>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add READTHEDOCS_LANGUAGE to the environment during builds (`#5941 <https://github.com/readthedocs/readthedocs.org/pull/5941>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Merge the GSOC 2019 in-doc search changes (`#5919 <https://github.com/readthedocs/readthedocs.org/pull/5919>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Add check for external version in conf.py.tmpl for warning banner (`#5900 <https://github.com/readthedocs/readthedocs.org/pull/5900>`__)
* `@Abhi-khandelwal <https://github.com/Abhi-khandelwal>`__: Point users to commercial solution for their private repositories (`#5849 <https://github.com/readthedocs/readthedocs.org/pull/5849>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Merge initial work from Pull Request Builder GSOC (`#5823 <https://github.com/readthedocs/readthedocs.org/pull/5823>`__)

Version 3.6.1
-------------

:Date: July 17, 2019

* `@ericholscher <https://github.com/ericholscher>`__: Missed a couple places to set READTHEDOCS_LANGUAGE (`#5951 <https://github.com/readthedocs/readthedocs.org/pull/5951>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Hotfix: Return empty dict when no highlight dict is present (`#5950 <https://github.com/readthedocs/readthedocs.org/pull/5950>`__)
* `@humitos <https://github.com/humitos>`__: Use a cwd where the user has access inside the container (`#5949 <https://github.com/readthedocs/readthedocs.org/pull/5949>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Small Changes to PR Builder Code (`#5948 <https://github.com/readthedocs/readthedocs.org/pull/5948>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Explicitly delete SphinxDomain objects from previous versions (`#5945 <https://github.com/readthedocs/readthedocs.org/pull/5945>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Properly return None when there's no highlight on a hit. (`#5944 <https://github.com/readthedocs/readthedocs.org/pull/5944>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 3.6.0 (`#5943 <https://github.com/readthedocs/readthedocs.org/pull/5943>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Bump the Sphinx extension to 1.0 (`#5942 <https://github.com/readthedocs/readthedocs.org/pull/5942>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add READTHEDOCS_LANGUAGE to the environment during builds (`#5941 <https://github.com/readthedocs/readthedocs.org/pull/5941>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Small search doc fix (`#5940 <https://github.com/readthedocs/readthedocs.org/pull/5940>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Indexing speedup (`#5939 <https://github.com/readthedocs/readthedocs.org/pull/5939>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Small improvement in parse_json (`#5938 <https://github.com/readthedocs/readthedocs.org/pull/5938>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Use `attrgetter` in sorted function (`#5936 <https://github.com/readthedocs/readthedocs.org/pull/5936>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Refine PR Builder Code (`#5933 <https://github.com/readthedocs/readthedocs.org/pull/5933>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Fix spacing between the results and add highlight url param (`#5932 <https://github.com/readthedocs/readthedocs.org/pull/5932>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Merge the GSOC 2019 in-doc search changes (`#5919 <https://github.com/readthedocs/readthedocs.org/pull/5919>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Add tests for section-linking (`#5918 <https://github.com/readthedocs/readthedocs.org/pull/5918>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Update build list and detail page UX (`#5916 <https://github.com/readthedocs/readthedocs.org/pull/5916>`__)
* `@humitos <https://github.com/humitos>`__: APIv3 endpoint to manage Environment Variables (`#5913 <https://github.com/readthedocs/readthedocs.org/pull/5913>`__)
* `@humitos <https://github.com/humitos>`__: Split APIv3 tests on different files (`#5911 <https://github.com/readthedocs/readthedocs.org/pull/5911>`__)
* `@stsewd <https://github.com/stsewd>`__: Better msg when gitpython fails (`#5903 <https://github.com/readthedocs/readthedocs.org/pull/5903>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Add check for external version in conf.py.tmpl for warning banner (`#5900 <https://github.com/readthedocs/readthedocs.org/pull/5900>`__)
* `@humitos <https://github.com/humitos>`__: Update APIv3 documentation with latest changes (`#5895 <https://github.com/readthedocs/readthedocs.org/pull/5895>`__)

Version 3.6.0
-------------

:Date: July 16, 2019

* `@ericholscher <https://github.com/ericholscher>`__: Bump the Sphinx extension to 1.0 (`#5942 <https://github.com/readthedocs/readthedocs.org/pull/5942>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add READTHEDOCS_LANGUAGE to the environment during builds (`#5941 <https://github.com/readthedocs/readthedocs.org/pull/5941>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Small search doc fix (`#5940 <https://github.com/readthedocs/readthedocs.org/pull/5940>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Indexing speedup (`#5939 <https://github.com/readthedocs/readthedocs.org/pull/5939>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Small improvement in parse_json (`#5938 <https://github.com/readthedocs/readthedocs.org/pull/5938>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Use `attrgetter` in sorted function (`#5936 <https://github.com/readthedocs/readthedocs.org/pull/5936>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Refine PR Builder Code (`#5933 <https://github.com/readthedocs/readthedocs.org/pull/5933>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Fix spacing between the results and add highlight url param (`#5932 <https://github.com/readthedocs/readthedocs.org/pull/5932>`__)
* `@Abhi-khandelwal <https://github.com/Abhi-khandelwal>`__: remove the usage of six (`#5930 <https://github.com/readthedocs/readthedocs.org/pull/5930>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Fix count value of docsearch REST api (`#5926 <https://github.com/readthedocs/readthedocs.org/pull/5926>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Merge the GSOC 2019 in-doc search changes (`#5919 <https://github.com/readthedocs/readthedocs.org/pull/5919>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Add tests for section-linking (`#5918 <https://github.com/readthedocs/readthedocs.org/pull/5918>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Update build list and detail page UX (`#5916 <https://github.com/readthedocs/readthedocs.org/pull/5916>`__)
* `@humitos <https://github.com/humitos>`__: These Project's methods are not used (`#5915 <https://github.com/readthedocs/readthedocs.org/pull/5915>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Github Status reporting Test fix (`#5914 <https://github.com/readthedocs/readthedocs.org/pull/5914>`__)
* `@humitos <https://github.com/humitos>`__: APIv3 endpoint to manage Environment Variables (`#5913 <https://github.com/readthedocs/readthedocs.org/pull/5913>`__)
* `@humitos <https://github.com/humitos>`__: Split APIv3 tests on different files (`#5911 <https://github.com/readthedocs/readthedocs.org/pull/5911>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Add Feature Flag to Enable External Version Building (`#5910 <https://github.com/readthedocs/readthedocs.org/pull/5910>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Pass the build_pk to the task instead of the build object itself (`#5904 <https://github.com/readthedocs/readthedocs.org/pull/5904>`__)
* `@stsewd <https://github.com/stsewd>`__: Better msg when gitpython fails (`#5903 <https://github.com/readthedocs/readthedocs.org/pull/5903>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Exclude external versions from get_latest_build (`#5901 <https://github.com/readthedocs/readthedocs.org/pull/5901>`__)
* `@humitos <https://github.com/humitos>`__: Update conda at startup (`#5897 <https://github.com/readthedocs/readthedocs.org/pull/5897>`__)
* `@humitos <https://github.com/humitos>`__: Update APIv3 documentation with latest changes (`#5895 <https://github.com/readthedocs/readthedocs.org/pull/5895>`__)
* `@stsewd <https://github.com/stsewd>`__: Add tests for version and project querysets (`#5894 <https://github.com/readthedocs/readthedocs.org/pull/5894>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Rework on documentation guides (`#5893 <https://github.com/readthedocs/readthedocs.org/pull/5893>`__)
* `@humitos <https://github.com/humitos>`__: Lint (pep257: D415) (`#5892 <https://github.com/readthedocs/readthedocs.org/pull/5892>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Fix spaces in email subject link (`#5891 <https://github.com/readthedocs/readthedocs.org/pull/5891>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Build only HTML and Save external version artifacts in different directory (`#5886 <https://github.com/readthedocs/readthedocs.org/pull/5886>`__)
* `@humitos <https://github.com/humitos>`__: APIv3 CRUD for Redirect objects (`#5879 <https://github.com/readthedocs/readthedocs.org/pull/5879>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add config to Build and Version admin (`#5877 <https://github.com/readthedocs/readthedocs.org/pull/5877>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 26 (`#5874 <https://github.com/readthedocs/readthedocs.org/pull/5874>`__)
* `@stsewd <https://github.com/stsewd>`__: Call distinct to the end of the querysets (`#5872 <https://github.com/readthedocs/readthedocs.org/pull/5872>`__)
* `@pranay414 <https://github.com/pranay414>`__: Change rtfd to readthedocs (`#5871 <https://github.com/readthedocs/readthedocs.org/pull/5871>`__)
* `@humitos <https://github.com/humitos>`__: APIv3 refactor some fields (`#5868 <https://github.com/readthedocs/readthedocs.org/pull/5868>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Send Build Status Report Using GitHub Status API (`#5865 <https://github.com/readthedocs/readthedocs.org/pull/5865>`__)
* `@humitos <https://github.com/humitos>`__: APIv3 "Import Project" endpoint (`#5857 <https://github.com/readthedocs/readthedocs.org/pull/5857>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove django guardian from querysets (`#5853 <https://github.com/readthedocs/readthedocs.org/pull/5853>`__)
* `@humitos <https://github.com/humitos>`__: Hide "Protected" privacy level from users (`#5833 <https://github.com/readthedocs/readthedocs.org/pull/5833>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Add section linking for the search result (`#5829 <https://github.com/readthedocs/readthedocs.org/pull/5829>`__)

Version 3.5.3
-------------

:Date: June 19, 2019

* `@davidfischer <https://github.com/davidfischer>`__: Treat docs warnings as errors (`#5825 <https://github.com/readthedocs/readthedocs.org/pull/5825>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Fix some unclear verbiage (`#5820 <https://github.com/readthedocs/readthedocs.org/pull/5820>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Rework documentation index page (`#5819 <https://github.com/readthedocs/readthedocs.org/pull/5819>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Upgrade intersphinx to Django 1.11 (`#5818 <https://github.com/readthedocs/readthedocs.org/pull/5818>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 24 (`#5817 <https://github.com/readthedocs/readthedocs.org/pull/5817>`__)
* `@humitos <https://github.com/humitos>`__: Disable changing domain when editing the object (`#5816 <https://github.com/readthedocs/readthedocs.org/pull/5816>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Update docs with sitemap sort order change (`#5815 <https://github.com/readthedocs/readthedocs.org/pull/5815>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Optimize requests to APIv3 (`#5803 <https://github.com/readthedocs/readthedocs.org/pull/5803>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Show build length in the admin (`#5802 <https://github.com/readthedocs/readthedocs.org/pull/5802>`__)
* `@stsewd <https://github.com/stsewd>`__: Move search functions (`#5801 <https://github.com/readthedocs/readthedocs.org/pull/5801>`__)
* `@ericholscher <https://github.com/ericholscher>`__: A few small improvements to help with search admin stuff (`#5800 <https://github.com/readthedocs/readthedocs.org/pull/5800>`__)
* `@stsewd <https://github.com/stsewd>`__: Simplify es indexing (`#5798 <https://github.com/readthedocs/readthedocs.org/pull/5798>`__)
* `@humitos <https://github.com/humitos>`__: Use a real SessionBase object on FooterNoSessionMiddleware (`#5797 <https://github.com/readthedocs/readthedocs.org/pull/5797>`__)
* `@stsewd <https://github.com/stsewd>`__: Add logging in magic methods (`#5795 <https://github.com/readthedocs/readthedocs.org/pull/5795>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix unbound var in search view (`#5794 <https://github.com/readthedocs/readthedocs.org/pull/5794>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Mention security issue in the changelog (`#5790 <https://github.com/readthedocs/readthedocs.org/pull/5790>`__)
* `@stsewd <https://github.com/stsewd>`__: Index path with original path name (`#5785 <https://github.com/readthedocs/readthedocs.org/pull/5785>`__)
* `@stsewd <https://github.com/stsewd>`__: Use querysets from the class not from an instance (`#5783 <https://github.com/readthedocs/readthedocs.org/pull/5783>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Add Build managers and Update Build Querysets. (`#5779 <https://github.com/readthedocs/readthedocs.org/pull/5779>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Project advertising page/form update (`#5777 <https://github.com/readthedocs/readthedocs.org/pull/5777>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Update docs around opt-out of ads (`#5776 <https://github.com/readthedocs/readthedocs.org/pull/5776>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Sitemap sort order priorities updated (`#5724 <https://github.com/readthedocs/readthedocs.org/pull/5724>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: [Design Doc] In Doc Search UI (`#5707 <https://github.com/readthedocs/readthedocs.org/pull/5707>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Pull Request Builder Design Doc (`#5705 <https://github.com/readthedocs/readthedocs.org/pull/5705>`__)
* `@humitos <https://github.com/humitos>`__: Support single version subprojects URLs to serve from Django (`#5690 <https://github.com/readthedocs/readthedocs.org/pull/5690>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Add a contrib Dockerfile for local build image on Linux (`#4608 <https://github.com/readthedocs/readthedocs.org/pull/4608>`__)

Version 3.5.2
-------------

This is a quick hotfix to the previous version.

:Date: June 11, 2019

* `@ericholscher <https://github.com/ericholscher>`__: Fix version of our sphinx-ext we're installing (`#5789 <https://github.com/readthedocs/readthedocs.org/pull/5789>`__)
* `@stsewd <https://github.com/stsewd>`__: Get version from the api (`#5788 <https://github.com/readthedocs/readthedocs.org/pull/5788>`__)

Version 3.5.1
-------------

This version contained a `security fix <https://github.com/readthedocs/readthedocs.org/security/advisories/GHSA-2mw9-4c46-qrcv>`_
for an open redirect issue.
The problem has been fixed and deployed on readthedocs.org.
For users who depend on the Read the Docs code line for a private instance of Read the Docs,
you are encouraged to update to 3.5.1 as soon as possible.

:Date: June 11, 2019

* `@stsewd <https://github.com/stsewd>`__: Update build images in docs (`#5782 <https://github.com/readthedocs/readthedocs.org/pull/5782>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Validate dict when parsing the mkdocs.yml file (`#5775 <https://github.com/readthedocs/readthedocs.org/pull/5775>`__)
* `@stsewd <https://github.com/stsewd>`__: Pin textclassifier dependencies (`#5773 <https://github.com/readthedocs/readthedocs.org/pull/5773>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix tests on master (`#5769 <https://github.com/readthedocs/readthedocs.org/pull/5769>`__)
* `@stsewd <https://github.com/stsewd>`__: Don't use implicit relative import (`#5767 <https://github.com/readthedocs/readthedocs.org/pull/5767>`__)
* `@stsewd <https://github.com/stsewd>`__: Use version_pk to trigger builds (`#5765 <https://github.com/readthedocs/readthedocs.org/pull/5765>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Domain UI improvements (`#5764 <https://github.com/readthedocs/readthedocs.org/pull/5764>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Try to fix Elastic connection pooling issues (`#5763 <https://github.com/readthedocs/readthedocs.org/pull/5763>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 22 (`#5762 <https://github.com/readthedocs/readthedocs.org/pull/5762>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Try to fix Elastic connection pooling issues (`#5760 <https://github.com/readthedocs/readthedocs.org/pull/5760>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Escape variables in mkdocs data (`#5759 <https://github.com/readthedocs/readthedocs.org/pull/5759>`__)
* `@humitos <https://github.com/humitos>`__: Serve 404/index.html file for htmldir Sphinx builder (`#5754 <https://github.com/readthedocs/readthedocs.org/pull/5754>`__)
* `@wilvk <https://github.com/wilvk>`__: fix sphinx startup guide to not to fail on rtd build as per #2569 (`#5753 <https://github.com/readthedocs/readthedocs.org/pull/5753>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix mkdocs relpath (`#5749 <https://github.com/readthedocs/readthedocs.org/pull/5749>`__)
* `@stsewd <https://github.com/stsewd>`__: Call lock per task (`#5748 <https://github.com/readthedocs/readthedocs.org/pull/5748>`__)
* `@stsewd <https://github.com/stsewd>`__: Pin kombu to 4.3.0 (`#5747 <https://github.com/readthedocs/readthedocs.org/pull/5747>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Clarify latexmk option usage (`#5745 <https://github.com/readthedocs/readthedocs.org/pull/5745>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Hotfix latexmx builder to ignore error codes (`#5744 <https://github.com/readthedocs/readthedocs.org/pull/5744>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Hide the Code API search in the UX for now. (`#5743 <https://github.com/readthedocs/readthedocs.org/pull/5743>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Add init.py under readthedocs/api (`#5742 <https://github.com/readthedocs/readthedocs.org/pull/5742>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Fix design docs missing from toctree (`#5741 <https://github.com/readthedocs/readthedocs.org/pull/5741>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 3.5.0 (`#5740 <https://github.com/readthedocs/readthedocs.org/pull/5740>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Pytest Timezone Warning Fixed (`#5739 <https://github.com/readthedocs/readthedocs.org/pull/5739>`__)
* `@humitos <https://github.com/humitos>`__: Filter by projects with no banned users (`#5733 <https://github.com/readthedocs/readthedocs.org/pull/5733>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Fix the sidebar ad color (`#5731 <https://github.com/readthedocs/readthedocs.org/pull/5731>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Permanent redirect feature added (`#5727 <https://github.com/readthedocs/readthedocs.org/pull/5727>`__)
* `@humitos <https://github.com/humitos>`__: Move version "Clean" button to details page (`#5706 <https://github.com/readthedocs/readthedocs.org/pull/5706>`__)
* `@gorshunovr <https://github.com/gorshunovr>`__: Update flags documentation (`#5701 <https://github.com/readthedocs/readthedocs.org/pull/5701>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Storage updates (`#5698 <https://github.com/readthedocs/readthedocs.org/pull/5698>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove files after build (`#5680 <https://github.com/readthedocs/readthedocs.org/pull/5680>`__)
* `@stsewd <https://github.com/stsewd>`__: Move community support to email (`#5651 <https://github.com/readthedocs/readthedocs.org/pull/5651>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Optimizations and UX improvements to the dashboard screen (`#5637 <https://github.com/readthedocs/readthedocs.org/pull/5637>`__)
* `@chrisjsewell <https://github.com/chrisjsewell>`__: Use `--upgrade` instead of `--force-reinstall` for pip installs (`#5635 <https://github.com/readthedocs/readthedocs.org/pull/5635>`__)
* `@stsewd <https://github.com/stsewd>`__: Move file validations out of the config module (`#5627 <https://github.com/readthedocs/readthedocs.org/pull/5627>`__)
* `@humitos <https://github.com/humitos>`__: Remove old/deprecated build endpoints (`#5479 <https://github.com/readthedocs/readthedocs.org/pull/5479>`__)
* `@shivanshu1234 <https://github.com/shivanshu1234>`__: Add link to in-progress build from dashboard. (`#5431 <https://github.com/readthedocs/readthedocs.org/pull/5431>`__)
* `@stsewd <https://github.com/stsewd>`__: Downgrade pytest-django (`#5294 <https://github.com/readthedocs/readthedocs.org/pull/5294>`__)

Version 3.5.0
-------------

:Date: May 30, 2019

* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 21 (`#5737 <https://github.com/readthedocs/readthedocs.org/pull/5737>`__)
* `@humitos <https://github.com/humitos>`__: Update feature flags exposed to user in docs (`#5734 <https://github.com/readthedocs/readthedocs.org/pull/5734>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Fix the sidebar ad color (`#5731 <https://github.com/readthedocs/readthedocs.org/pull/5731>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Create a funding file (`#5729 <https://github.com/readthedocs/readthedocs.org/pull/5729>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Small commercial hosting page rework (`#5728 <https://github.com/readthedocs/readthedocs.org/pull/5728>`__)
* `@mattparrilla <https://github.com/mattparrilla>`__: Add note about lack of support for private repos (`#5726 <https://github.com/readthedocs/readthedocs.org/pull/5726>`__)
* `@humitos <https://github.com/humitos>`__: Canonical consistency example (`#5722 <https://github.com/readthedocs/readthedocs.org/pull/5722>`__)
* `@humitos <https://github.com/humitos>`__: Use nonstopmode for latexmk (`#5714 <https://github.com/readthedocs/readthedocs.org/pull/5714>`__)
* `@cclauss <https://github.com/cclauss>`__: Identity is not the same thing as equality in Python (`#5713 <https://github.com/readthedocs/readthedocs.org/pull/5713>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 20 (`#5712 <https://github.com/readthedocs/readthedocs.org/pull/5712>`__)
* `@humitos <https://github.com/humitos>`__: Move version "Clean" button to details page (`#5706 <https://github.com/readthedocs/readthedocs.org/pull/5706>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Explicitly mention a support email (`#5703 <https://github.com/readthedocs/readthedocs.org/pull/5703>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Storage updates (`#5698 <https://github.com/readthedocs/readthedocs.org/pull/5698>`__)
* `@humitos <https://github.com/humitos>`__: Enable auth validate passwords (`#5696 <https://github.com/readthedocs/readthedocs.org/pull/5696>`__)
* `@stsewd <https://github.com/stsewd>`__: Simplify lock acquire (`#5695 <https://github.com/readthedocs/readthedocs.org/pull/5695>`__)
* `@stsewd <https://github.com/stsewd>`__: Simplify update docs task (`#5694 <https://github.com/readthedocs/readthedocs.org/pull/5694>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 19 (`#5692 <https://github.com/readthedocs/readthedocs.org/pull/5692>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Warning about using sqlite 3.26.0 for development (`#5681 <https://github.com/readthedocs/readthedocs.org/pull/5681>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Configure the security middleware (`#5679 <https://github.com/readthedocs/readthedocs.org/pull/5679>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix bug in notifications (`#5678 <https://github.com/readthedocs/readthedocs.org/pull/5678>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 18 (`#5667 <https://github.com/readthedocs/readthedocs.org/pull/5667>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: pylint fix for notifications, restapi and config (`#5664 <https://github.com/readthedocs/readthedocs.org/pull/5664>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: pylint fix for readthedocs.search (`#5663 <https://github.com/readthedocs/readthedocs.org/pull/5663>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: pylint fix for readthedocs.projects (`#5662 <https://github.com/readthedocs/readthedocs.org/pull/5662>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: pylint fix for readthedocs.doc_builder (`#5660 <https://github.com/readthedocs/readthedocs.org/pull/5660>`__)
* `@humitos <https://github.com/humitos>`__: Support Docker 5.0 image (`#5657 <https://github.com/readthedocs/readthedocs.org/pull/5657>`__)
* `@humitos <https://github.com/humitos>`__: Use latexmk if Sphinx > 1.6 (`#5656 <https://github.com/readthedocs/readthedocs.org/pull/5656>`__)
* `@humitos <https://github.com/humitos>`__: Upgrade docker python package to latest release (`#5654 <https://github.com/readthedocs/readthedocs.org/pull/5654>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: pylint fix for readthedocs.core (`#5650 <https://github.com/readthedocs/readthedocs.org/pull/5650>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 17 (`#5645 <https://github.com/readthedocs/readthedocs.org/pull/5645>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Serve custom 404 pages from Django (`#5644 <https://github.com/readthedocs/readthedocs.org/pull/5644>`__)
* `@yarons <https://github.com/yarons>`__: Typo fix (`#5642 <https://github.com/readthedocs/readthedocs.org/pull/5642>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Sitemap hreflang syntax invalid for regional language variants fix (`#5638 <https://github.com/readthedocs/readthedocs.org/pull/5638>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Optimizations and UX improvements to the dashboard screen (`#5637 <https://github.com/readthedocs/readthedocs.org/pull/5637>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Redirect project slugs with underscores (`#5634 <https://github.com/readthedocs/readthedocs.org/pull/5634>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Standardizing the use of settings directly (`#5632 <https://github.com/readthedocs/readthedocs.org/pull/5632>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Note for Docker image size in Docker instructions (`#5630 <https://github.com/readthedocs/readthedocs.org/pull/5630>`__)
* `@davidfischer <https://github.com/davidfischer>`__: UX improvements around SSL certificates (`#5629 <https://github.com/readthedocs/readthedocs.org/pull/5629>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Gold project sponsorship changes (`#5628 <https://github.com/readthedocs/readthedocs.org/pull/5628>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Make sure there's a contact when opting out of advertising (`#5626 <https://github.com/readthedocs/readthedocs.org/pull/5626>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove unused volume from docker (`#5625 <https://github.com/readthedocs/readthedocs.org/pull/5625>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: hotfix: correct way of getting environment variables (`#5622 <https://github.com/readthedocs/readthedocs.org/pull/5622>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 16 (`#5619 <https://github.com/readthedocs/readthedocs.org/pull/5619>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 3.4.2 (`#5613 <https://github.com/readthedocs/readthedocs.org/pull/5613>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add explicit egg version to unicode-slugify (`#5612 <https://github.com/readthedocs/readthedocs.org/pull/5612>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Remove ProxyMiddleware (`#5607 <https://github.com/readthedocs/readthedocs.org/pull/5607>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Remove 'Versions' tab from Admin Dashboard. (`#5600 <https://github.com/readthedocs/readthedocs.org/pull/5600>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Notify the user when deleting a superproject (`#5596 <https://github.com/readthedocs/readthedocs.org/pull/5596>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Handle 401, 403 and 404  when setting up webhooks (`#5589 <https://github.com/readthedocs/readthedocs.org/pull/5589>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Unify usage of settings and remove the usage of getattr for settings (`#5588 <https://github.com/readthedocs/readthedocs.org/pull/5588>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Note about admin page in the docs (`#5585 <https://github.com/readthedocs/readthedocs.org/pull/5585>`__)
* `@humitos <https://github.com/humitos>`__: Remove USE_SETUPTOOLS_LATEST feature flag (`#5578 <https://github.com/readthedocs/readthedocs.org/pull/5578>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Validate docs dir before writing custom js (`#5569 <https://github.com/readthedocs/readthedocs.org/pull/5569>`__)
* `@rshrc <https://github.com/rshrc>`__: Added note in YAML docs (`#5565 <https://github.com/readthedocs/readthedocs.org/pull/5565>`__)
* `@shivanshu1234 <https://github.com/shivanshu1234>`__: Specify python3 in installation instructions. (`#5552 <https://github.com/readthedocs/readthedocs.org/pull/5552>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Write build artifacts to (cloud) storage from build servers (`#5549 <https://github.com/readthedocs/readthedocs.org/pull/5549>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: "Default branch: latest" does not exist Fix. (`#5547 <https://github.com/readthedocs/readthedocs.org/pull/5547>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Update ``readthedocs-environment.json`` file when env vars are added/deleted (`#5540 <https://github.com/readthedocs/readthedocs.org/pull/5540>`__)
* `@humitos <https://github.com/humitos>`__: Update common to its latest version (`#5517 <https://github.com/readthedocs/readthedocs.org/pull/5517>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Profile page performance issue Fix (`#5472 <https://github.com/readthedocs/readthedocs.org/pull/5472>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove unused form (`#5443 <https://github.com/readthedocs/readthedocs.org/pull/5443>`__)
* `@stsewd <https://github.com/stsewd>`__: Use relative paths in config module (`#5377 <https://github.com/readthedocs/readthedocs.org/pull/5377>`__)
* `@humitos <https://github.com/humitos>`__: Initial structure for APIv3 (`#5356 <https://github.com/readthedocs/readthedocs.org/pull/5356>`__)
* `@stsewd <https://github.com/stsewd>`__: Add models for automation rules (`#5323 <https://github.com/readthedocs/readthedocs.org/pull/5323>`__)
* `@stsewd <https://github.com/stsewd>`__: Downgrade pytest-django (`#5294 <https://github.com/readthedocs/readthedocs.org/pull/5294>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add search for DomainData objects (`#5290 <https://github.com/readthedocs/readthedocs.org/pull/5290>`__)
* `@gorshunovr <https://github.com/gorshunovr>`__: Change version references to :latest tag (`#5245 <https://github.com/readthedocs/readthedocs.org/pull/5245>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Fix buttons problems in 'Change Email' section. (`#5219 <https://github.com/readthedocs/readthedocs.org/pull/5219>`__)

Version 3.4.2
-------------

:Date: April 22, 2019

* `@ericholscher <https://github.com/ericholscher>`__: Add explicit egg version to unicode-slugify (`#5612 <https://github.com/readthedocs/readthedocs.org/pull/5612>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Update Environmental Variable character limit (`#5597 <https://github.com/readthedocs/readthedocs.org/pull/5597>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Add meta descriptions to top documentation (`#5593 <https://github.com/readthedocs/readthedocs.org/pull/5593>`__)
* `@stsewd <https://github.com/stsewd>`__: Ignore pytest-xdist from pyupdate (`#5590 <https://github.com/readthedocs/readthedocs.org/pull/5590>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Note about admin page in the docs (`#5585 <https://github.com/readthedocs/readthedocs.org/pull/5585>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 14 (`#5580 <https://github.com/readthedocs/readthedocs.org/pull/5580>`__)
* `@stsewd <https://github.com/stsewd>`__: Use downloads.html in template (`#5579 <https://github.com/readthedocs/readthedocs.org/pull/5579>`__)
* `@ihnorton <https://github.com/ihnorton>`__: Fix typo in conda.rst (`#5576 <https://github.com/readthedocs/readthedocs.org/pull/5576>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Fix for Firefox to close the ad correctly (`#5571 <https://github.com/readthedocs/readthedocs.org/pull/5571>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Non mobile fixed footer ads (`#5567 <https://github.com/readthedocs/readthedocs.org/pull/5567>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 3.4.1 (`#5566 <https://github.com/readthedocs/readthedocs.org/pull/5566>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Update ``readthedocs-environment.json`` file when env vars are added/deleted (`#5540 <https://github.com/readthedocs/readthedocs.org/pull/5540>`__)
* `@stsewd <https://github.com/stsewd>`__: Allow build mkdocs outside root (`#5539 <https://github.com/readthedocs/readthedocs.org/pull/5539>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Sitemap assumes that all versions are translated Fix. (`#5535 <https://github.com/readthedocs/readthedocs.org/pull/5535>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Remove Header Login button from login page (`#5534 <https://github.com/readthedocs/readthedocs.org/pull/5534>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Optimize database performance of the footer API (`#5530 <https://github.com/readthedocs/readthedocs.org/pull/5530>`__)
* `@stsewd <https://github.com/stsewd>`__: Don't depend of enabled pdf/epub to show downloads  (`#5502 <https://github.com/readthedocs/readthedocs.org/pull/5502>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Don't allow to create subprojects with same alias (`#5404 <https://github.com/readthedocs/readthedocs.org/pull/5404>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Improve project translation listing Design under admin tab (`#5380 <https://github.com/readthedocs/readthedocs.org/pull/5380>`__)

Version 3.4.1
-------------

:Date: April 03, 2019

* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 13 (`#5558 <https://github.com/readthedocs/readthedocs.org/pull/5558>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix advanced settings form (`#5544 <https://github.com/readthedocs/readthedocs.org/pull/5544>`__)
* `@stsewd <https://github.com/stsewd>`__: Call mkdocs using -m (`#5542 <https://github.com/readthedocs/readthedocs.org/pull/5542>`__)
* `@stsewd <https://github.com/stsewd>`__: Allow build mkdocs outside root (`#5539 <https://github.com/readthedocs/readthedocs.org/pull/5539>`__)
* `@stsewd <https://github.com/stsewd>`__: Use patch method to update has_valid_clone (`#5538 <https://github.com/readthedocs/readthedocs.org/pull/5538>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 12 (`#5536 <https://github.com/readthedocs/readthedocs.org/pull/5536>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Sitemap assumes that all versions are translated Fix. (`#5535 <https://github.com/readthedocs/readthedocs.org/pull/5535>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Remove Header Login button from login page (`#5534 <https://github.com/readthedocs/readthedocs.org/pull/5534>`__)
* `@stevepiercy <https://github.com/stevepiercy>`__: Add pylons-sphinx-themes to list of supported themes (`#5533 <https://github.com/readthedocs/readthedocs.org/pull/5533>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Optimize database performance of the footer API (`#5530 <https://github.com/readthedocs/readthedocs.org/pull/5530>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix extra origin in urls (`#5523 <https://github.com/readthedocs/readthedocs.org/pull/5523>`__)
* `@davidjb <https://github.com/davidjb>`__:  Update contributing docs for RTD's own docs (`#5522 <https://github.com/readthedocs/readthedocs.org/pull/5522>`__)
* `@davidjb <https://github.com/davidjb>`__: Use HTTPS for intersphinx mappings (`#5521 <https://github.com/readthedocs/readthedocs.org/pull/5521>`__)
* `@davidjb <https://github.com/davidjb>`__: Fix formatting for CentOS/RHEL installs (`#5520 <https://github.com/readthedocs/readthedocs.org/pull/5520>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Guide users to the YAML config from the build detail page (`#5519 <https://github.com/readthedocs/readthedocs.org/pull/5519>`__)
* `@davidjb <https://github.com/davidjb>`__: Add to and reorder GitHub webhook docs (`#5514 <https://github.com/readthedocs/readthedocs.org/pull/5514>`__)
* `@stsewd <https://github.com/stsewd>`__: Link to the docdir of the remote repo in non-rtd themes for mkdocs (`#5513 <https://github.com/readthedocs/readthedocs.org/pull/5513>`__)
* `@stevepiercy <https://github.com/stevepiercy>`__: Tidy up grammar, promote Unicode characters (`#5511 <https://github.com/readthedocs/readthedocs.org/pull/5511>`__)
* `@stsewd <https://github.com/stsewd>`__: Catch specific exception for config not found (`#5510 <https://github.com/readthedocs/readthedocs.org/pull/5510>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Use ValueError instead of InvalidParamsException (`#5509 <https://github.com/readthedocs/readthedocs.org/pull/5509>`__)
* `@humitos <https://github.com/humitos>`__: Force Sphinx to not use xindy (`#5507 <https://github.com/readthedocs/readthedocs.org/pull/5507>`__)
* `@stsewd <https://github.com/stsewd>`__: Update mkdocs (`#5505 <https://github.com/readthedocs/readthedocs.org/pull/5505>`__)
* `@stsewd <https://github.com/stsewd>`__: Don't depend of enabled pdf/epub to show downloads  (`#5502 <https://github.com/readthedocs/readthedocs.org/pull/5502>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Remove search & API from robots.txt (`#5501 <https://github.com/readthedocs/readthedocs.org/pull/5501>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Make /random/ path work (`#5496 <https://github.com/readthedocs/readthedocs.org/pull/5496>`__)
* `@humitos <https://github.com/humitos>`__: Typo on conf.py.tmpl (`#5495 <https://github.com/readthedocs/readthedocs.org/pull/5495>`__)
* `@rshrc <https://github.com/rshrc>`__: Added note warning about using sqlite 3.26.0 in development (`#5491 <https://github.com/readthedocs/readthedocs.org/pull/5491>`__)
* `@stsewd <https://github.com/stsewd>`__: Regroup advanced settings (`#5489 <https://github.com/readthedocs/readthedocs.org/pull/5489>`__)
* `@ericholscher <https://github.com/ericholscher>`__:     Fix bug that caused search objects not to delete (`#5487 <https://github.com/readthedocs/readthedocs.org/pull/5487>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 3.4.0 (`#5486 <https://github.com/readthedocs/readthedocs.org/pull/5486>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Promote the YAML config (`#5485 <https://github.com/readthedocs/readthedocs.org/pull/5485>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 11 (`#5483 <https://github.com/readthedocs/readthedocs.org/pull/5483>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Dashboard screen performance fix (`#5471 <https://github.com/readthedocs/readthedocs.org/pull/5471>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Build List Screen Performance Issue Fix. (`#5470 <https://github.com/readthedocs/readthedocs.org/pull/5470>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Remove Haystack reference in Docs (`#5469 <https://github.com/readthedocs/readthedocs.org/pull/5469>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Enable Django Debug Toolbar in development (`#5464 <https://github.com/readthedocs/readthedocs.org/pull/5464>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Optimize the version list screen (`#5460 <https://github.com/readthedocs/readthedocs.org/pull/5460>`__)
* `@stsewd <https://github.com/stsewd>`__: Regroup settings (`#5459 <https://github.com/readthedocs/readthedocs.org/pull/5459>`__)
* `@humitos <https://github.com/humitos>`__: Guide to build PDF for non-ASCII language (`#5453 <https://github.com/readthedocs/readthedocs.org/pull/5453>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Remove asserts from code. (`#5452 <https://github.com/readthedocs/readthedocs.org/pull/5452>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Optimize the repos API query (`#5451 <https://github.com/readthedocs/readthedocs.org/pull/5451>`__)
* `@stsewd <https://github.com/stsewd>`__: Update version of setuptools (`#5450 <https://github.com/readthedocs/readthedocs.org/pull/5450>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove unused validator (`#5442 <https://github.com/readthedocs/readthedocs.org/pull/5442>`__)
* `@humitos <https://github.com/humitos>`__: Build PDF files using latexmk (`#5437 <https://github.com/readthedocs/readthedocs.org/pull/5437>`__)
* `@stsewd <https://github.com/stsewd>`__: Always update the commit of the stable version (`#5421 <https://github.com/readthedocs/readthedocs.org/pull/5421>`__)
* `@stsewd <https://github.com/stsewd>`__: Share doctree between builders (`#5407 <https://github.com/readthedocs/readthedocs.org/pull/5407>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove unused template (`#5401 <https://github.com/readthedocs/readthedocs.org/pull/5401>`__)
* `@orlnub123 <https://github.com/orlnub123>`__: Fix pip installs (`#5386 <https://github.com/readthedocs/readthedocs.org/pull/5386>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Add an application form for community ads (`#5379 <https://github.com/readthedocs/readthedocs.org/pull/5379>`__)

Version 3.4.0
-------------

:Date: March 18, 2019

* `@davidfischer <https://github.com/davidfischer>`__: Promote the YAML config (`#5485 <https://github.com/readthedocs/readthedocs.org/pull/5485>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Dashboard screen performance fix (`#5471 <https://github.com/readthedocs/readthedocs.org/pull/5471>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Build List Screen Performance Issue Fix. (`#5470 <https://github.com/readthedocs/readthedocs.org/pull/5470>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Remove Haystack reference in Docs (`#5469 <https://github.com/readthedocs/readthedocs.org/pull/5469>`__)
* `@mashrikt <https://github.com/mashrikt>`__: gitignore dev.db-journal file #5463 (`#5466 <https://github.com/readthedocs/readthedocs.org/pull/5466>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Enable Django Debug Toolbar in development (`#5464 <https://github.com/readthedocs/readthedocs.org/pull/5464>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Optimize the version list screen (`#5460 <https://github.com/readthedocs/readthedocs.org/pull/5460>`__)
* `@stsewd <https://github.com/stsewd>`__: Regroup settings (`#5459 <https://github.com/readthedocs/readthedocs.org/pull/5459>`__)
* `@Mariatta <https://github.com/Mariatta>`__: Fix typo: leave the field black -> blank (`#5457 <https://github.com/readthedocs/readthedocs.org/pull/5457>`__)
* `@stsewd <https://github.com/stsewd>`__: Use Ubuntu xenial on travis (`#5456 <https://github.com/readthedocs/readthedocs.org/pull/5456>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Update links to point to `stable` version. (`#5455 <https://github.com/readthedocs/readthedocs.org/pull/5455>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Fix inconsistency in footer links (`#5454 <https://github.com/readthedocs/readthedocs.org/pull/5454>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Optimize the repos API query (`#5451 <https://github.com/readthedocs/readthedocs.org/pull/5451>`__)
* `@stsewd <https://github.com/stsewd>`__: Update version of setuptools (`#5450 <https://github.com/readthedocs/readthedocs.org/pull/5450>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove unused validator (`#5442 <https://github.com/readthedocs/readthedocs.org/pull/5442>`__)
* `@humitos <https://github.com/humitos>`__: Build PDF files using latexmk (`#5437 <https://github.com/readthedocs/readthedocs.org/pull/5437>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 10 (`#5432 <https://github.com/readthedocs/readthedocs.org/pull/5432>`__)
* `@shivanshu1234 <https://github.com/shivanshu1234>`__: Remove invalid example from v2.rst (`#5430 <https://github.com/readthedocs/readthedocs.org/pull/5430>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Removed unused constant from core.models (`#5424 <https://github.com/readthedocs/readthedocs.org/pull/5424>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix reraise of exception (`#5423 <https://github.com/readthedocs/readthedocs.org/pull/5423>`__)
* `@stsewd <https://github.com/stsewd>`__: Always update the commit of the stable version (`#5421 <https://github.com/readthedocs/readthedocs.org/pull/5421>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix warnings in code (`#5419 <https://github.com/readthedocs/readthedocs.org/pull/5419>`__)
* `@stsewd <https://github.com/stsewd>`__: Refactor move_files (`#5418 <https://github.com/readthedocs/readthedocs.org/pull/5418>`__)
* `@agarwalrounak <https://github.com/agarwalrounak>`__: Document that people can create a version named stable (`#5417 <https://github.com/readthedocs/readthedocs.org/pull/5417>`__)
* `@agarwalrounak <https://github.com/agarwalrounak>`__: Update installation guide to include submodules (`#5416 <https://github.com/readthedocs/readthedocs.org/pull/5416>`__)
* `@stsewd <https://github.com/stsewd>`__: Update docs for building with markdown (`#5415 <https://github.com/readthedocs/readthedocs.org/pull/5415>`__)
* `@stsewd <https://github.com/stsewd>`__: Share doctree between builders (`#5407 <https://github.com/readthedocs/readthedocs.org/pull/5407>`__)
* `@humitos <https://github.com/humitos>`__: Communicate the project slug can be changed by requesting it (`#5403 <https://github.com/readthedocs/readthedocs.org/pull/5403>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove unused template (`#5401 <https://github.com/readthedocs/readthedocs.org/pull/5401>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove view docs dropdown (`#5400 <https://github.com/readthedocs/readthedocs.org/pull/5400>`__)
* `@humitos <https://github.com/humitos>`__: Minimum upgrade of the builds docs (`#5398 <https://github.com/readthedocs/readthedocs.org/pull/5398>`__)
* `@stsewd <https://github.com/stsewd>`__: Update internal requirements (`#5396 <https://github.com/readthedocs/readthedocs.org/pull/5396>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 09 (`#5395 <https://github.com/readthedocs/readthedocs.org/pull/5395>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Trigger build on default branch when saving a project (`#5393 <https://github.com/readthedocs/readthedocs.org/pull/5393>`__)
* `@Mike-Dai <https://github.com/Mike-Dai>`__: Removed un-needed python dependencies (`#5389 <https://github.com/readthedocs/readthedocs.org/pull/5389>`__)
* `@orlnub123 <https://github.com/orlnub123>`__: Fix pip installs (`#5386 <https://github.com/readthedocs/readthedocs.org/pull/5386>`__)
* `@rshrc <https://github.com/rshrc>`__: Addressed Issue #5327 (`#5383 <https://github.com/readthedocs/readthedocs.org/pull/5383>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Be extra explicit about the CNAME (`#5382 <https://github.com/readthedocs/readthedocs.org/pull/5382>`__)
* `@stsewd <https://github.com/stsewd>`__: Better MkDocs integration as GSoC idea (`#5378 <https://github.com/readthedocs/readthedocs.org/pull/5378>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 3.3.1 (`#5376 <https://github.com/readthedocs/readthedocs.org/pull/5376>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add a GSOC section for openAPI (`#5375 <https://github.com/readthedocs/readthedocs.org/pull/5375>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Make 'default_version` field as readonly if no active versions are found. (`#5374 <https://github.com/readthedocs/readthedocs.org/pull/5374>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Be more defensive with our storage uploading (`#5371 <https://github.com/readthedocs/readthedocs.org/pull/5371>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Check for two paths for each file (`#5370 <https://github.com/readthedocs/readthedocs.org/pull/5370>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Don't show projects in Sphinx Domain Admin sidebar (`#5367 <https://github.com/readthedocs/readthedocs.org/pull/5367>`__)
* `@stsewd <https://github.com/stsewd>`__: Start building with sphinx 1.8 (`#5366 <https://github.com/readthedocs/readthedocs.org/pull/5366>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: Remove pytest warnings (`#5346 <https://github.com/readthedocs/readthedocs.org/pull/5346>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Remove the v1 API (`#5293 <https://github.com/readthedocs/readthedocs.org/pull/5293>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove doctype from resolver (`#5230 <https://github.com/readthedocs/readthedocs.org/pull/5230>`__)
* `@humitos <https://github.com/humitos>`__: Implementation of APIv3 (`#4863 <https://github.com/readthedocs/readthedocs.org/pull/4863>`__)

Version 3.3.1
-------------

:Date: February 28, 2019

* `@ericholscher <https://github.com/ericholscher>`__: Be more defensive with our storage uploading (`#5371 <https://github.com/readthedocs/readthedocs.org/pull/5371>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Check for two paths for each file (`#5370 <https://github.com/readthedocs/readthedocs.org/pull/5370>`__)
* `@stsewd <https://github.com/stsewd>`__: Protect against anchors with # (`#5369 <https://github.com/readthedocs/readthedocs.org/pull/5369>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Don't show projects in Sphinx Domain Admin sidebar (`#5367 <https://github.com/readthedocs/readthedocs.org/pull/5367>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix sphinx domain models and migrations (`#5363 <https://github.com/readthedocs/readthedocs.org/pull/5363>`__)
* `@stsewd <https://github.com/stsewd>`__: Try to put back codecov integration (`#5362 <https://github.com/readthedocs/readthedocs.org/pull/5362>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 3.3.0 (`#5361 <https://github.com/readthedocs/readthedocs.org/pull/5361>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix search bug when an empty list of objects_id was passed (`#5357 <https://github.com/readthedocs/readthedocs.org/pull/5357>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Add admin methods for reindexing versions from project and version admin. (`#5343 <https://github.com/readthedocs/readthedocs.org/pull/5343>`__)
* `@stsewd <https://github.com/stsewd>`__: Cleanup a little of documentation_type from footer (`#5315 <https://github.com/readthedocs/readthedocs.org/pull/5315>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add modeling for intersphinx data (`#5289 <https://github.com/readthedocs/readthedocs.org/pull/5289>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove doctype from resolver (`#5230 <https://github.com/readthedocs/readthedocs.org/pull/5230>`__)
* `@stsewd <https://github.com/stsewd>`__: Validate webhook's payload (`#4940 <https://github.com/readthedocs/readthedocs.org/pull/4940>`__)
* `@stsewd <https://github.com/stsewd>`__: Start testing config v2 on our project (`#4838 <https://github.com/readthedocs/readthedocs.org/pull/4838>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Revert "Merge pull request #4636 from readthedocs/search_upgrade" (`#4716 <https://github.com/readthedocs/readthedocs.org/pull/4716>`__)
* `@safwanrahman <https://github.com/safwanrahman>`__: [GSoC 2018] All Search Improvements (`#4636 <https://github.com/readthedocs/readthedocs.org/pull/4636>`__)
* `@stsewd <https://github.com/stsewd>`__: Add schema for configuration file with yamale (`#4084 <https://github.com/readthedocs/readthedocs.org/pull/4084>`__)
* `@stsewd <https://github.com/stsewd>`__: Add note about mercurial on tests (`#3358 <https://github.com/readthedocs/readthedocs.org/pull/3358>`__)

Version 3.3.0
-------------

:Date: February 27, 2019

* `@ericholscher <https://github.com/ericholscher>`__: Fix search bug when an empty list of objects_id was passed (`#5357 <https://github.com/readthedocs/readthedocs.org/pull/5357>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Update UI translations (`#5354 <https://github.com/readthedocs/readthedocs.org/pull/5354>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Update GSOC page to mention we're accepted. (`#5353 <https://github.com/readthedocs/readthedocs.org/pull/5353>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 08 (`#5352 <https://github.com/readthedocs/readthedocs.org/pull/5352>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Increase path's max_length for ImportedFile model to 4096 (`#5345 <https://github.com/readthedocs/readthedocs.org/pull/5345>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: improvement on inserting mkdocs media (`#5344 <https://github.com/readthedocs/readthedocs.org/pull/5344>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Add admin methods for reindexing versions from project and version admin. (`#5343 <https://github.com/readthedocs/readthedocs.org/pull/5343>`__)
* `@stsewd <https://github.com/stsewd>`__: Initialize local variable before using it (`#5342 <https://github.com/readthedocs/readthedocs.org/pull/5342>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Remove deprecated code (`#5341 <https://github.com/readthedocs/readthedocs.org/pull/5341>`__)
* `@stsewd <https://github.com/stsewd>`__: Require conda.file when using conda in v1 (`#5338 <https://github.com/readthedocs/readthedocs.org/pull/5338>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove unused setting (`#5336 <https://github.com/readthedocs/readthedocs.org/pull/5336>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix comment (`#5329 <https://github.com/readthedocs/readthedocs.org/pull/5329>`__)
* `@stsewd <https://github.com/stsewd>`__: Don't depend on specific data when catching exception (`#5326 <https://github.com/readthedocs/readthedocs.org/pull/5326>`__)
* `@regisb <https://github.com/regisb>`__: Fix "clean_builds" command argument parsing (`#5320 <https://github.com/readthedocs/readthedocs.org/pull/5320>`__)
* `@stsewd <https://github.com/stsewd>`__: Cleanup a little of documentation_type from footer (`#5315 <https://github.com/readthedocs/readthedocs.org/pull/5315>`__)
* `@humitos <https://github.com/humitos>`__: Warning note about running ES locally for tests (`#5314 <https://github.com/readthedocs/readthedocs.org/pull/5314>`__)
* `@humitos <https://github.com/humitos>`__: Update documentation on running test for python environment (`#5313 <https://github.com/readthedocs/readthedocs.org/pull/5313>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 3.2.3 (`#5312 <https://github.com/readthedocs/readthedocs.org/pull/5312>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add basic auth to the generic webhook API. (`#5311 <https://github.com/readthedocs/readthedocs.org/pull/5311>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix an issue where we were not properly filtering projects (`#5309 <https://github.com/readthedocs/readthedocs.org/pull/5309>`__)
* `@stsewd <https://github.com/stsewd>`__: Rstrip repo url (`#5308 <https://github.com/readthedocs/readthedocs.org/pull/5308>`__)
* `@rexzing <https://github.com/rexzing>`__: Incompatible dependency for prospector with pylint-django (`#5306 <https://github.com/readthedocs/readthedocs.org/pull/5306>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Allow extensions to control URL structure (`#5296 <https://github.com/readthedocs/readthedocs.org/pull/5296>`__)
* `@stsewd <https://github.com/stsewd>`__: Downgrade pytest-django (`#5294 <https://github.com/readthedocs/readthedocs.org/pull/5294>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add modeling for intersphinx data (`#5289 <https://github.com/readthedocs/readthedocs.org/pull/5289>`__)
* `@ovc <https://github.com/ovc>`__: Tweek css for sphinx_prompt (`#5281 <https://github.com/readthedocs/readthedocs.org/pull/5281>`__)
* `@saadmk11 <https://github.com/saadmk11>`__: #4036 Updated build list to include an alert state (`#5222 <https://github.com/readthedocs/readthedocs.org/pull/5222>`__)
* `@humitos <https://github.com/humitos>`__: Use unicode-slugify to generate Version.slug (`#5186 <https://github.com/readthedocs/readthedocs.org/pull/5186>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Add admin functions for wiping a version (`#5140 <https://github.com/readthedocs/readthedocs.org/pull/5140>`__)
* `@humitos <https://github.com/humitos>`__: Generate general sitemap.xml for projects (`#5122 <https://github.com/readthedocs/readthedocs.org/pull/5122>`__)
* `@humitos <https://github.com/humitos>`__: Logging exceptions rework (`#5118 <https://github.com/readthedocs/readthedocs.org/pull/5118>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Store ePubs and PDFs in media storage (`#4947 <https://github.com/readthedocs/readthedocs.org/pull/4947>`__)
* `@stsewd <https://github.com/stsewd>`__: Validate webhook's payload (`#4940 <https://github.com/readthedocs/readthedocs.org/pull/4940>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Revert "Merge pull request #4636 from readthedocs/search_upgrade" (`#4716 <https://github.com/readthedocs/readthedocs.org/pull/4716>`__)
* `@safwanrahman <https://github.com/safwanrahman>`__: [GSoC 2018] All Search Improvements (`#4636 <https://github.com/readthedocs/readthedocs.org/pull/4636>`__)

Version 3.2.3
-------------

:Date: February 19, 2019

* `@ericholscher <https://github.com/ericholscher>`__: Add basic auth to the generic webhook API. (`#5311 <https://github.com/readthedocs/readthedocs.org/pull/5311>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix an issue where we were not properly filtering projects (`#5309 <https://github.com/readthedocs/readthedocs.org/pull/5309>`__)
* `@stsewd <https://github.com/stsewd>`__: Rstrip repo url (`#5308 <https://github.com/readthedocs/readthedocs.org/pull/5308>`__)
* `@stsewd <https://github.com/stsewd>`__: Use autosectionlabel for docs in security (`#5307 <https://github.com/readthedocs/readthedocs.org/pull/5307>`__)
* `@rexzing <https://github.com/rexzing>`__: Incompatible dependency for prospector with pylint-django (`#5306 <https://github.com/readthedocs/readthedocs.org/pull/5306>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: pyup:  Scheduled weekly dependency update for week 07 (`#5305 <https://github.com/readthedocs/readthedocs.org/pull/5305>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Allow extensions to control URL structure (`#5296 <https://github.com/readthedocs/readthedocs.org/pull/5296>`__)
* `@stsewd <https://github.com/stsewd>`__: Downgrade pytest-django (`#5294 <https://github.com/readthedocs/readthedocs.org/pull/5294>`__)
* `@rexzing <https://github.com/rexzing>`__: Docs reformatting with :guilabel: (`#5161 <https://github.com/readthedocs/readthedocs.org/pull/5161>`__)

Version 3.2.2
-------------

:Date: February 13, 2019

* `@ericholscher <https://github.com/ericholscher>`__: Support old jquery where responseJSON doesn't exist (`#5285 <https://github.com/readthedocs/readthedocs.org/pull/5285>`__)
* `@humitos <https://github.com/humitos>`__: pyup.yml syntax fixed (`#5284 <https://github.com/readthedocs/readthedocs.org/pull/5284>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Fix error of travis (rename migration file) (`#5282 <https://github.com/readthedocs/readthedocs.org/pull/5282>`__)
* `@humitos <https://github.com/humitos>`__: pyup YAML configuration file (`#5279 <https://github.com/readthedocs/readthedocs.org/pull/5279>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: Pin ipdb to latest version 0.11 (`#5278 <https://github.com/readthedocs/readthedocs.org/pull/5278>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: Pin datadiff to latest version 2.0.0 (`#5277 <https://github.com/readthedocs/readthedocs.org/pull/5277>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: Pin pytest-cov to latest version 2.6.1 (`#5276 <https://github.com/readthedocs/readthedocs.org/pull/5276>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: Pin pillow to latest version 5.4.1 (`#5275 <https://github.com/readthedocs/readthedocs.org/pull/5275>`__)
* `@pyup-bot <https://github.com/pyup-bot>`__: Update elasticsearch to 6.3.1 (`#5274 <https://github.com/readthedocs/readthedocs.org/pull/5274>`__)
* `@discdiver <https://github.com/discdiver>`__: clarify github integration needs ``https://`` prepended (`#5273 <https://github.com/readthedocs/readthedocs.org/pull/5273>`__)
* `@humitos <https://github.com/humitos>`__: Setup and configure pyup.io (`#5272 <https://github.com/readthedocs/readthedocs.org/pull/5272>`__)
* `@humitos <https://github.com/humitos>`__: Update all Python dependencies (`#5269 <https://github.com/readthedocs/readthedocs.org/pull/5269>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Add note about security issue (`#5263 <https://github.com/readthedocs/readthedocs.org/pull/5263>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Don’t delay search delete on project delete (`#5262 <https://github.com/readthedocs/readthedocs.org/pull/5262>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Automate docs version from our setup.cfg (`#5259 <https://github.com/readthedocs/readthedocs.org/pull/5259>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Add admin actions for building versions (`#5255 <https://github.com/readthedocs/readthedocs.org/pull/5255>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Give the 404 page a title. (`#5252 <https://github.com/readthedocs/readthedocs.org/pull/5252>`__)
* `@humitos <https://github.com/humitos>`__: Make our SUFFIX default selection py2/3 compatible (`#5251 <https://github.com/readthedocs/readthedocs.org/pull/5251>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 3.2.1 (`#5248 <https://github.com/readthedocs/readthedocs.org/pull/5248>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Remove excluding files on search. (`#5246 <https://github.com/readthedocs/readthedocs.org/pull/5246>`__)
* `@gorshunovr <https://github.com/gorshunovr>`__: Change version references to :latest tag (`#5245 <https://github.com/readthedocs/readthedocs.org/pull/5245>`__)
* `@humitos <https://github.com/humitos>`__: Remove py2 compatibility (`#5241 <https://github.com/readthedocs/readthedocs.org/pull/5241>`__)
* `@stsewd <https://github.com/stsewd>`__: Allow to override trigger_build from demo project (`#5236 <https://github.com/readthedocs/readthedocs.org/pull/5236>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Change some info logging to debug to clean up build output (`#5233 <https://github.com/readthedocs/readthedocs.org/pull/5233>`__)
* `@stsewd <https://github.com/stsewd>`__: Fake auth middleware in tests (`#5206 <https://github.com/readthedocs/readthedocs.org/pull/5206>`__)
* `@EJEP <https://github.com/EJEP>`__: Clarify 'more info' link in admin settings page (`#5180 <https://github.com/readthedocs/readthedocs.org/pull/5180>`__)
* `@rexzing <https://github.com/rexzing>`__: Docs reformatting with :guilabel: (`#5161 <https://github.com/readthedocs/readthedocs.org/pull/5161>`__)

Version 3.2.1
-------------

:Date: February 07, 2019

* `@ericholscher <https://github.com/ericholscher>`__: Remove excluding files on search. (`#5246 <https://github.com/readthedocs/readthedocs.org/pull/5246>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Don't update search on HTMLFile save (`#5244 <https://github.com/readthedocs/readthedocs.org/pull/5244>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Be more defensive in our 404 handler (`#5243 <https://github.com/readthedocs/readthedocs.org/pull/5243>`__)
* `@humitos <https://github.com/humitos>`__: Install sphinx-notfound-page for building 404.html custom page (`#5242 <https://github.com/readthedocs/readthedocs.org/pull/5242>`__)
* `@humitos <https://github.com/humitos>`__: Remove py2 compatibility (`#5241 <https://github.com/readthedocs/readthedocs.org/pull/5241>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 3.2.0 (`#5240 <https://github.com/readthedocs/readthedocs.org/pull/5240>`__)

Version 3.2.0
-------------

:Date: February 06, 2019

* `@ericholscher <https://github.com/ericholscher>`__: Support passing an explicit `index_name` for search indexing (`#5239 <https://github.com/readthedocs/readthedocs.org/pull/5239>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Tweak some ad styles (`#5237 <https://github.com/readthedocs/readthedocs.org/pull/5237>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix conda issue link (`#5226 <https://github.com/readthedocs/readthedocs.org/pull/5226>`__)
* `@humitos <https://github.com/humitos>`__: Add Santos to the development team (`#5224 <https://github.com/readthedocs/readthedocs.org/pull/5224>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Update our GSOC page for 2019 (`#5210 <https://github.com/readthedocs/readthedocs.org/pull/5210>`__)
* `@humitos <https://github.com/humitos>`__: Do not allow to merge 'Status: blocked' PRs (`#5205 <https://github.com/readthedocs/readthedocs.org/pull/5205>`__)
* `@stsewd <https://github.com/stsewd>`__: Inject user to middleware tests (`#5203 <https://github.com/readthedocs/readthedocs.org/pull/5203>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Remove approvals requirement from mergeable (`#5200 <https://github.com/readthedocs/readthedocs.org/pull/5200>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Update project notification copy to past tense (`#5199 <https://github.com/readthedocs/readthedocs.org/pull/5199>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove feature flag for v2 (`#5198 <https://github.com/readthedocs/readthedocs.org/pull/5198>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Refactor search code (`#5197 <https://github.com/readthedocs/readthedocs.org/pull/5197>`__)
* `@stsewd <https://github.com/stsewd>`__: Update mergeable settings to v2 (`#5196 <https://github.com/readthedocs/readthedocs.org/pull/5196>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix mergeable bot (`#5195 <https://github.com/readthedocs/readthedocs.org/pull/5195>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix broken links for badges (`#5190 <https://github.com/readthedocs/readthedocs.org/pull/5190>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Change badge style (`#5189 <https://github.com/readthedocs/readthedocs.org/pull/5189>`__)
* `@humitos <https://github.com/humitos>`__: Allow source_suffix to be a dictionary (`#5183 <https://github.com/readthedocs/readthedocs.org/pull/5183>`__)
* `@humitos <https://github.com/humitos>`__: Upgrade all packages removing py2 compatibility (`#5179 <https://github.com/readthedocs/readthedocs.org/pull/5179>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Small docs fix (`#5176 <https://github.com/readthedocs/readthedocs.org/pull/5176>`__)
* `@stsewd <https://github.com/stsewd>`__: Sync all services even if  one social accoun fails (`#5171 <https://github.com/readthedocs/readthedocs.org/pull/5171>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 3.1.0 (`#5170 <https://github.com/readthedocs/readthedocs.org/pull/5170>`__)
* `@rvmzes <https://github.com/rvmzes>`__: SyntaxError caused by comma in python3 (`#5156 <https://github.com/readthedocs/readthedocs.org/pull/5156>`__)
* `@humitos <https://github.com/humitos>`__: Use latest docker images as default (`#5155 <https://github.com/readthedocs/readthedocs.org/pull/5155>`__)
* `@stsewd <https://github.com/stsewd>`__:  Remove logic for guessing slug from an unregistered domain (`#5143 <https://github.com/readthedocs/readthedocs.org/pull/5143>`__)
* `@humitos <https://github.com/humitos>`__: Allow custom 404.html on projects (`#5130 <https://github.com/readthedocs/readthedocs.org/pull/5130>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Docs for feature flag (`#5043 <https://github.com/readthedocs/readthedocs.org/pull/5043>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove usage of project.documentation_type in tasks (`#4896 <https://github.com/readthedocs/readthedocs.org/pull/4896>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Reapply the Elastic Search upgrade to `master` (`#4722 <https://github.com/readthedocs/readthedocs.org/pull/4722>`__)
* `@stsewd <https://github.com/stsewd>`__: Config file v2 docs (`#4451 <https://github.com/readthedocs/readthedocs.org/pull/4451>`__)
* `@stsewd <https://github.com/stsewd>`__: Set python3 as default interpreter (`#3581 <https://github.com/readthedocs/readthedocs.org/pull/3581>`__)

Version 3.1.0
-------------

This version greatly improves our search capabilities,
thanks to the Google Summer of Code.
We're hoping to have another version of search coming soon after this,
but this is a large upgrade moving to the latest Elastic Search.

:Date: January 24, 2019

* `@ericholscher <https://github.com/ericholscher>`__: Fix docs build (`#5164 <https://github.com/readthedocs/readthedocs.org/pull/5164>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 3.0.0 (`#5163 <https://github.com/readthedocs/readthedocs.org/pull/5163>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix tests on master (`#5162 <https://github.com/readthedocs/readthedocs.org/pull/5162>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Sort versions smartly everywhere (`#5157 <https://github.com/readthedocs/readthedocs.org/pull/5157>`__)
* `@stsewd <https://github.com/stsewd>`__: Allow query params in redirects (`#5081 <https://github.com/readthedocs/readthedocs.org/pull/5081>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Implement get objects or log (`#4900 <https://github.com/readthedocs/readthedocs.org/pull/4900>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove usage of project.documentation_type in tasks (`#4896 <https://github.com/readthedocs/readthedocs.org/pull/4896>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Reapply the Elastic Search upgrade to `master` (`#4722 <https://github.com/readthedocs/readthedocs.org/pull/4722>`__)

Version 3.0.0
-------------

**Read the Docs now only supports Python 3.6+**.
This is for people running the software on their own servers,
builds continue to work across all supported Python versions.

:Date: January 23, 2019

* `@stsewd <https://github.com/stsewd>`__: Fix tests on master (`#5162 <https://github.com/readthedocs/readthedocs.org/pull/5162>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Sort versions smartly everywhere (`#5157 <https://github.com/readthedocs/readthedocs.org/pull/5157>`__)
* `@rvmzes <https://github.com/rvmzes>`__: SyntaxError caused by comma in python3 (`#5156 <https://github.com/readthedocs/readthedocs.org/pull/5156>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix Sphinx conf.py inserts (`#5150 <https://github.com/readthedocs/readthedocs.org/pull/5150>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Upgrade recommonmark to latest and fix integration (`#5146 <https://github.com/readthedocs/readthedocs.org/pull/5146>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix requirements for local installation (`#5138 <https://github.com/readthedocs/readthedocs.org/pull/5138>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix local-docs-build requirements (`#5136 <https://github.com/readthedocs/readthedocs.org/pull/5136>`__)
* `@humitos <https://github.com/humitos>`__: Upgrade all dependencies (`#5134 <https://github.com/readthedocs/readthedocs.org/pull/5134>`__)
* `@humitos <https://github.com/humitos>`__: Configuration file for ProBot Mergeable Bot (`#5132 <https://github.com/readthedocs/readthedocs.org/pull/5132>`__)
* `@xavfernandez <https://github.com/xavfernandez>`__: docs: fix integration typos (`#5128 <https://github.com/readthedocs/readthedocs.org/pull/5128>`__)
* ``@Hamdy722``: Update LICENSE (`#5125 <https://github.com/readthedocs/readthedocs.org/pull/5125>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove doctype from search (`#5121 <https://github.com/readthedocs/readthedocs.org/pull/5121>`__)
* `@humitos <https://github.com/humitos>`__: Validate mkdocs.yml config on values that we manipulate (`#5119 <https://github.com/readthedocs/readthedocs.org/pull/5119>`__)
* `@humitos <https://github.com/humitos>`__: Use 2019 in our README (`#5117 <https://github.com/readthedocs/readthedocs.org/pull/5117>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove dead code from config module (`#5116 <https://github.com/readthedocs/readthedocs.org/pull/5116>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Check that the repo exists before trying to get a git commit (`#5115 <https://github.com/readthedocs/readthedocs.org/pull/5115>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 2.8.5 (`#5111 <https://github.com/readthedocs/readthedocs.org/pull/5111>`__)
* `@stsewd <https://github.com/stsewd>`__: Use the python path from virtualenv in Conda (`#5110 <https://github.com/readthedocs/readthedocs.org/pull/5110>`__)
* `@humitos <https://github.com/humitos>`__: Feature flag to use `readthedocs/build:testing` image (`#5109 <https://github.com/readthedocs/readthedocs.org/pull/5109>`__)
* `@stsewd <https://github.com/stsewd>`__: Use python from virtualenv's bin directory when executing commands (`#5107 <https://github.com/readthedocs/readthedocs.org/pull/5107>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Split requirements/pip.txt (`#5100 <https://github.com/readthedocs/readthedocs.org/pull/5100>`__)
* `@humitos <https://github.com/humitos>`__: Do not list banned projects under /projects/ (`#5097 <https://github.com/readthedocs/readthedocs.org/pull/5097>`__)
* `@humitos <https://github.com/humitos>`__: Do not build projects from banned users (`#5096 <https://github.com/readthedocs/readthedocs.org/pull/5096>`__)
* `@humitos <https://github.com/humitos>`__: Support custom robots.txt (`#5086 <https://github.com/readthedocs/readthedocs.org/pull/5086>`__)
* `@stsewd <https://github.com/stsewd>`__: Allow query params in redirects (`#5081 <https://github.com/readthedocs/readthedocs.org/pull/5081>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Fire a signal for domain verification (eg. for SSL) (`#5071 <https://github.com/readthedocs/readthedocs.org/pull/5071>`__)
* `@humitos <https://github.com/humitos>`__: Upgrade all code to be Python3 only (`#5065 <https://github.com/readthedocs/readthedocs.org/pull/5065>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Use default settings for Config object (`#5056 <https://github.com/readthedocs/readthedocs.org/pull/5056>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Allow large form posts via multipart encoded forms to command API (`#5000 <https://github.com/readthedocs/readthedocs.org/pull/5000>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Validate url from webhook notification (`#4983 <https://github.com/readthedocs/readthedocs.org/pull/4983>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Display error, using inbuilt notification system, if primary email is not verified (`#4964 <https://github.com/readthedocs/readthedocs.org/pull/4964>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Implement get objects or log (`#4900 <https://github.com/readthedocs/readthedocs.org/pull/4900>`__)
* `@humitos <https://github.com/humitos>`__: CRUD for EnvironmentVariables from Project's admin (`#4899 <https://github.com/readthedocs/readthedocs.org/pull/4899>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove usage of project.documentation_type in tasks (`#4896 <https://github.com/readthedocs/readthedocs.org/pull/4896>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Fix the failing domain deletion task (`#4891 <https://github.com/readthedocs/readthedocs.org/pull/4891>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove unused validations from v1 config (`#4883 <https://github.com/readthedocs/readthedocs.org/pull/4883>`__)
* `@humitos <https://github.com/humitos>`__: Appropriate logging when a LockTimeout for VCS is reached (`#4804 <https://github.com/readthedocs/readthedocs.org/pull/4804>`__)
* `@stsewd <https://github.com/stsewd>`__: Implement extended install option (`#4740 <https://github.com/readthedocs/readthedocs.org/pull/4740>`__)
* `@bansalnitish <https://github.com/bansalnitish>`__: Added a link to open new issue with prefilled details (`#3683 <https://github.com/readthedocs/readthedocs.org/pull/3683>`__)

Version 2.8.5
-------------

:Date: January 15, 2019

* `@stsewd <https://github.com/stsewd>`__: Use the python path from virtualenv in Conda (`#5110 <https://github.com/readthedocs/readthedocs.org/pull/5110>`__)
* `@humitos <https://github.com/humitos>`__: Feature flag to use `readthedocs/build:testing` image (`#5109 <https://github.com/readthedocs/readthedocs.org/pull/5109>`__)
* `@stsewd <https://github.com/stsewd>`__: Use python from virtualenv's bin directory when executing commands (`#5107 <https://github.com/readthedocs/readthedocs.org/pull/5107>`__)
* `@humitos <https://github.com/humitos>`__: Do not build projects from banned users (`#5096 <https://github.com/readthedocs/readthedocs.org/pull/5096>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Fix common pieces (`#5095 <https://github.com/readthedocs/readthedocs.org/pull/5095>`__)
* `@rainwoodman <https://github.com/rainwoodman>`__: Suppress progress bar of the conda command. (`#5094 <https://github.com/readthedocs/readthedocs.org/pull/5094>`__)
* `@humitos <https://github.com/humitos>`__: Remove unused suggestion block from 404 pages (`#5087 <https://github.com/readthedocs/readthedocs.org/pull/5087>`__)
* `@humitos <https://github.com/humitos>`__: Remove header nav (Login/Logout button) on 404 pages (`#5085 <https://github.com/readthedocs/readthedocs.org/pull/5085>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix little typo (`#5084 <https://github.com/readthedocs/readthedocs.org/pull/5084>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Split up deprecated view notification to GitHub and other webhook endpoints (`#5083 <https://github.com/readthedocs/readthedocs.org/pull/5083>`__)
* `@humitos <https://github.com/humitos>`__: Install ProBot (`#5082 <https://github.com/readthedocs/readthedocs.org/pull/5082>`__)
* `@stsewd <https://github.com/stsewd>`__: Update docs about contributing to docs (`#5077 <https://github.com/readthedocs/readthedocs.org/pull/5077>`__)
* `@humitos <https://github.com/humitos>`__: Declare and improve invoke tasks (`#5075 <https://github.com/readthedocs/readthedocs.org/pull/5075>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Fire a signal for domain verification (eg. for SSL) (`#5071 <https://github.com/readthedocs/readthedocs.org/pull/5071>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Update copy on notifications for github services deprecation (`#5067 <https://github.com/readthedocs/readthedocs.org/pull/5067>`__)
* `@humitos <https://github.com/humitos>`__: Upgrade all packages with pur (`#5059 <https://github.com/readthedocs/readthedocs.org/pull/5059>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Reduce logging to sentry (`#5054 <https://github.com/readthedocs/readthedocs.org/pull/5054>`__)
* `@discdiver <https://github.com/discdiver>`__: fixed missing apostrophe for possessive "project's" (`#5052 <https://github.com/readthedocs/readthedocs.org/pull/5052>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Template improvements in "gold/subscription_form.html" (`#5049 <https://github.com/readthedocs/readthedocs.org/pull/5049>`__)
* `@merwok <https://github.com/merwok>`__: Fix link in features page (`#5048 <https://github.com/readthedocs/readthedocs.org/pull/5048>`__)
* `@stsewd <https://github.com/stsewd>`__: Update webhook docs (`#5040 <https://github.com/readthedocs/readthedocs.org/pull/5040>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove sphinx static and template dir (`#5039 <https://github.com/readthedocs/readthedocs.org/pull/5039>`__)
* `@stephenfin <https://github.com/stephenfin>`__: Add temporary method for disabling shallow cloning (#5031) (`#5036 <https://github.com/readthedocs/readthedocs.org/pull/5036>`__)
* `@stsewd <https://github.com/stsewd>`__: Raise exception in failed checkout (`#5035 <https://github.com/readthedocs/readthedocs.org/pull/5035>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Change default_branch value from Version.slug to Version.identifier (`#5034 <https://github.com/readthedocs/readthedocs.org/pull/5034>`__)
* `@humitos <https://github.com/humitos>`__: Make wipe view not CSRF exempt (`#5025 <https://github.com/readthedocs/readthedocs.org/pull/5025>`__)
* `@humitos <https://github.com/humitos>`__: Convert an IRI path to URI before setting as NGINX header (`#5024 <https://github.com/readthedocs/readthedocs.org/pull/5024>`__)
* `@safwanrahman <https://github.com/safwanrahman>`__: index project asynchronously (`#5023 <https://github.com/readthedocs/readthedocs.org/pull/5023>`__)
* `@stsewd <https://github.com/stsewd>`__: Keep command output when it's killed (`#5015 <https://github.com/readthedocs/readthedocs.org/pull/5015>`__)
* `@stsewd <https://github.com/stsewd>`__: More hints for invalid submodules (`#5012 <https://github.com/readthedocs/readthedocs.org/pull/5012>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 2.8.4 (`#5011 <https://github.com/readthedocs/readthedocs.org/pull/5011>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove `auto` doctype (`#5010 <https://github.com/readthedocs/readthedocs.org/pull/5010>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Tweak sidebar ad priority (`#5005 <https://github.com/readthedocs/readthedocs.org/pull/5005>`__)
* `@stsewd <https://github.com/stsewd>`__: Replace git status and git submodules status for gitpython (`#5002 <https://github.com/readthedocs/readthedocs.org/pull/5002>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Backport jquery 2432 to Read the Docs (`#5001 <https://github.com/readthedocs/readthedocs.org/pull/5001>`__)
* `@stsewd <https://github.com/stsewd>`__: Refactor remove_dir (`#4994 <https://github.com/readthedocs/readthedocs.org/pull/4994>`__)
* `@humitos <https://github.com/humitos>`__: Skip builds when project is not active (`#4991 <https://github.com/readthedocs/readthedocs.org/pull/4991>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Make $ unselectable in docs (`#4990 <https://github.com/readthedocs/readthedocs.org/pull/4990>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Remove deprecated "models.permalink" (`#4975 <https://github.com/readthedocs/readthedocs.org/pull/4975>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Add validation for tags of length greater than 100 characters (`#4967 <https://github.com/readthedocs/readthedocs.org/pull/4967>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Add test case for send_notifications on VersionLockedError (`#4958 <https://github.com/readthedocs/readthedocs.org/pull/4958>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Remove trailing slashes on svn checkout (`#4951 <https://github.com/readthedocs/readthedocs.org/pull/4951>`__)
* `@stsewd <https://github.com/stsewd>`__: Safe symlink on version deletion (`#4937 <https://github.com/readthedocs/readthedocs.org/pull/4937>`__)
* `@humitos <https://github.com/humitos>`__: CRUD for EnvironmentVariables from Project's admin (`#4899 <https://github.com/readthedocs/readthedocs.org/pull/4899>`__)
* `@humitos <https://github.com/humitos>`__: Notify users about the usage of deprecated webhooks (`#4898 <https://github.com/readthedocs/readthedocs.org/pull/4898>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Disable django guardian warning (`#4892 <https://github.com/readthedocs/readthedocs.org/pull/4892>`__)
* `@humitos <https://github.com/humitos>`__: Handle 401, 403 and 404 status codes when hitting GitHub for webhook (`#4805 <https://github.com/readthedocs/readthedocs.org/pull/4805>`__)

Version 2.8.4
-------------

:Date: December 17, 2018

* `@davidfischer <https://github.com/davidfischer>`__: Tweak sidebar ad priority (`#5005 <https://github.com/readthedocs/readthedocs.org/pull/5005>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Backport jquery 2432 to Read the Docs (`#5001 <https://github.com/readthedocs/readthedocs.org/pull/5001>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Remove codecov comments and project coverage CI status (`#4996 <https://github.com/readthedocs/readthedocs.org/pull/4996>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove `LOCAL_GIT_BRANCHES` from settings (`#4993 <https://github.com/readthedocs/readthedocs.org/pull/4993>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Link update on FAQ page (`#4988 <https://github.com/readthedocs/readthedocs.org/pull/4988>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Only use remote branches for our syncing. (`#4984 <https://github.com/readthedocs/readthedocs.org/pull/4984>`__)
* `@humitos <https://github.com/humitos>`__: Sanitize output and chunk it at DATA_UPLOAD_MAX_MEMORY_SIZE (`#4982 <https://github.com/readthedocs/readthedocs.org/pull/4982>`__)
* `@humitos <https://github.com/humitos>`__: Modify DB field for container_time_limit to be an integer (`#4979 <https://github.com/readthedocs/readthedocs.org/pull/4979>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Remove deprecated imports from "urlresolvers" (`#4976 <https://github.com/readthedocs/readthedocs.org/pull/4976>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Workaround for a django-storages bug (`#4963 <https://github.com/readthedocs/readthedocs.org/pull/4963>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 2.8.3 (`#4961 <https://github.com/readthedocs/readthedocs.org/pull/4961>`__)
* `@monsij <https://github.com/monsij>`__: Remove -e option (`#4960 <https://github.com/readthedocs/readthedocs.org/pull/4960>`__)
* `@nutann3 <https://github.com/nutann3>`__: Update "install Sphinx" URL (`#4959 <https://github.com/readthedocs/readthedocs.org/pull/4959>`__)
* `@stsewd <https://github.com/stsewd>`__: Shallow git clone (`#4939 <https://github.com/readthedocs/readthedocs.org/pull/4939>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Validate profile form fields (`#4910 <https://github.com/readthedocs/readthedocs.org/pull/4910>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Calculate actual ad views (`#4885 <https://github.com/readthedocs/readthedocs.org/pull/4885>`__)
* `@humitos <https://github.com/humitos>`__: Allow all /api/v2/ CORS if the Domain is known (`#4880 <https://github.com/readthedocs/readthedocs.org/pull/4880>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Disable django.security.DisallowedHost from logging (`#4879 <https://github.com/readthedocs/readthedocs.org/pull/4879>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Remove 'Sphinx Template Changes' From Docs (`#4878 <https://github.com/readthedocs/readthedocs.org/pull/4878>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Make form for adopting project a choice field (`#4841 <https://github.com/readthedocs/readthedocs.org/pull/4841>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Add 'Branding' under the 'Business Info' section and 'Guidelines' on 'Design Docs' (`#4830 <https://github.com/readthedocs/readthedocs.org/pull/4830>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Raise 404 at SubdomainMiddleware if the project does not exist. (`#4795 <https://github.com/readthedocs/readthedocs.org/pull/4795>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Add help_text in the form for adopting a project (`#4781 <https://github.com/readthedocs/readthedocs.org/pull/4781>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Remove /embed API endpoint (`#4771 <https://github.com/readthedocs/readthedocs.org/pull/4771>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Improve unexpected error message when build fails (`#4754 <https://github.com/readthedocs/readthedocs.org/pull/4754>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Change the way of using login_required decorator (`#4723 <https://github.com/readthedocs/readthedocs.org/pull/4723>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Fix the form for adopting a project (`#4721 <https://github.com/readthedocs/readthedocs.org/pull/4721>`__)

Version 2.8.3
-------------

:Date: December 05, 2018

* `@nutann3 <https://github.com/nutann3>`__: Update "install Sphinx" URL (`#4959 <https://github.com/readthedocs/readthedocs.org/pull/4959>`__)
* `@humitos <https://github.com/humitos>`__: Pin redis to the current stable and compatible version (`#4956 <https://github.com/readthedocs/readthedocs.org/pull/4956>`__)
* `@humitos <https://github.com/humitos>`__: Properly set LANG environment variables (`#4954 <https://github.com/readthedocs/readthedocs.org/pull/4954>`__)
* `@humitos <https://github.com/humitos>`__: Adapt code to remove and ignore warnings (`#4953 <https://github.com/readthedocs/readthedocs.org/pull/4953>`__)
* `@stsewd <https://github.com/stsewd>`__: Shallow git clone (`#4939 <https://github.com/readthedocs/readthedocs.org/pull/4939>`__)
* `@stsewd <https://github.com/stsewd>`__: Install latest version of pip (`#4938 <https://github.com/readthedocs/readthedocs.org/pull/4938>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix svn update (`#4933 <https://github.com/readthedocs/readthedocs.org/pull/4933>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 2.8.2 (`#4931 <https://github.com/readthedocs/readthedocs.org/pull/4931>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove repeated and dead code (`#4929 <https://github.com/readthedocs/readthedocs.org/pull/4929>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove deprecated sudo from travis (`#4919 <https://github.com/readthedocs/readthedocs.org/pull/4919>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Validate profile form fields (`#4910 <https://github.com/readthedocs/readthedocs.org/pull/4910>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Calculate actual ad views (`#4885 <https://github.com/readthedocs/readthedocs.org/pull/4885>`__)
* `@stsewd <https://github.com/stsewd>`__: Sync versions when creating/deleting versions (`#4876 <https://github.com/readthedocs/readthedocs.org/pull/4876>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Remove unused project model fields (`#4870 <https://github.com/readthedocs/readthedocs.org/pull/4870>`__)
* `@humitos <https://github.com/humitos>`__: All package updates (`#4792 <https://github.com/readthedocs/readthedocs.org/pull/4792>`__)
* `@humitos <https://github.com/humitos>`__: Support git unicode branches (`#4433 <https://github.com/readthedocs/readthedocs.org/pull/4433>`__)

Version 2.8.2
-------------

:Date: November 28, 2018

* `@stsewd <https://github.com/stsewd>`__: Use .exists in queryset (`#4927 <https://github.com/readthedocs/readthedocs.org/pull/4927>`__)
* `@stsewd <https://github.com/stsewd>`__: Don't rmtree symlink (`#4925 <https://github.com/readthedocs/readthedocs.org/pull/4925>`__)
* `@stsewd <https://github.com/stsewd>`__: Delete tags with same commit (`#4915 <https://github.com/readthedocs/readthedocs.org/pull/4915>`__)
* `@safwanrahman <https://github.com/safwanrahman>`__: Tuning Elasticsearch for search improvements (`#4909 <https://github.com/readthedocs/readthedocs.org/pull/4909>`__)
* `@edmondchuc <https://github.com/edmondchuc>`__: Fixed some typos. (`#4906 <https://github.com/readthedocs/readthedocs.org/pull/4906>`__)
* `@humitos <https://github.com/humitos>`__: Upgrade stripe Python package to the latest version (`#4904 <https://github.com/readthedocs/readthedocs.org/pull/4904>`__)
* `@humitos <https://github.com/humitos>`__: Retry on API failure when connecting from builders (`#4902 <https://github.com/readthedocs/readthedocs.org/pull/4902>`__)
* `@stsewd <https://github.com/stsewd>`__: Separate update and checkout steps (`#4901 <https://github.com/readthedocs/readthedocs.org/pull/4901>`__)
* `@humitos <https://github.com/humitos>`__: Expose environment variables from database into build commands (`#4894 <https://github.com/readthedocs/readthedocs.org/pull/4894>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Use python to expand the cwd instead of environment variables (`#4882 <https://github.com/readthedocs/readthedocs.org/pull/4882>`__)
* `@humitos <https://github.com/humitos>`__: Call Celery worker properly (`#4881 <https://github.com/readthedocs/readthedocs.org/pull/4881>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Disable django.security.DisallowedHost from logging (`#4879 <https://github.com/readthedocs/readthedocs.org/pull/4879>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Remove 'Sphinx Template Changes' From Docs (`#4878 <https://github.com/readthedocs/readthedocs.org/pull/4878>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Unbreak the admin on ImportedFile by using raw_id_fields (`#4874 <https://github.com/readthedocs/readthedocs.org/pull/4874>`__)
* `@stsewd <https://github.com/stsewd>`__: Check if latest exists before updating identifier (`#4873 <https://github.com/readthedocs/readthedocs.org/pull/4873>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 2.8.1 (`#4872 <https://github.com/readthedocs/readthedocs.org/pull/4872>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Update django-guardian settings (`#4871 <https://github.com/readthedocs/readthedocs.org/pull/4871>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Change 'VerisionLockedTimeout' to 'VersionLockedError' in comment. (`#4859 <https://github.com/readthedocs/readthedocs.org/pull/4859>`__)
* `@stsewd <https://github.com/stsewd>`__: Hide "edit on" when the version is a tag (`#4851 <https://github.com/readthedocs/readthedocs.org/pull/4851>`__)
* `@stsewd <https://github.com/stsewd>`__: Delete untracked tags on fetch (`#4811 <https://github.com/readthedocs/readthedocs.org/pull/4811>`__)
* `@humitos <https://github.com/humitos>`__: Appropriate logging when a LockTimeout for VCS is reached (`#4804 <https://github.com/readthedocs/readthedocs.org/pull/4804>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove support for multiple configurations in one file (`#4800 <https://github.com/readthedocs/readthedocs.org/pull/4800>`__)
* `@stsewd <https://github.com/stsewd>`__: Pipfile support (schema) (`#4782 <https://github.com/readthedocs/readthedocs.org/pull/4782>`__)
* `@stsewd <https://github.com/stsewd>`__: Save config on build model (`#4749 <https://github.com/readthedocs/readthedocs.org/pull/4749>`__)
* `@invinciblycool <https://github.com/invinciblycool>`__: Redirect to build detail post manual build (`#4622 <https://github.com/readthedocs/readthedocs.org/pull/4622>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Enable timezone support and set timezone to UTC (`#4545 <https://github.com/readthedocs/readthedocs.org/pull/4545>`__)
* `@chirathr <https://github.com/chirathr>`__: Webhook notification URL size validation check (`#3680 <https://github.com/readthedocs/readthedocs.org/pull/3680>`__)

Version 2.8.1
-------------

:Date: November 06, 2018

* `@ericholscher <https://github.com/ericholscher>`__: Fix migration name on modified date migration (`#4867 <https://github.com/readthedocs/readthedocs.org/pull/4867>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Change 'VerisionLockedTimeout' to 'VersionLockedError' in comment. (`#4859 <https://github.com/readthedocs/readthedocs.org/pull/4859>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix rtd config file (`#4857 <https://github.com/readthedocs/readthedocs.org/pull/4857>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Shorten project name to match slug length (`#4856 <https://github.com/readthedocs/readthedocs.org/pull/4856>`__)
* `@stsewd <https://github.com/stsewd>`__: Generic message for parser error of config file (`#4853 <https://github.com/readthedocs/readthedocs.org/pull/4853>`__)
* `@stsewd <https://github.com/stsewd>`__: Use $HOME as CWD for virtualenv creation (`#4852 <https://github.com/readthedocs/readthedocs.org/pull/4852>`__)
* `@stsewd <https://github.com/stsewd>`__: Hide "edit on" when the version is a tag (`#4851 <https://github.com/readthedocs/readthedocs.org/pull/4851>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add modified_date to ImportedFile. (`#4850 <https://github.com/readthedocs/readthedocs.org/pull/4850>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Use raw_id_fields so that the Feature admin loads (`#4849 <https://github.com/readthedocs/readthedocs.org/pull/4849>`__)
* `@stsewd <https://github.com/stsewd>`__: Allow to change project's VCS (`#4845 <https://github.com/readthedocs/readthedocs.org/pull/4845>`__)
* `@benjaoming <https://github.com/benjaoming>`__: Version compare warning text (`#4842 <https://github.com/readthedocs/readthedocs.org/pull/4842>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Make form for adopting project a choice field (`#4841 <https://github.com/readthedocs/readthedocs.org/pull/4841>`__)
* `@humitos <https://github.com/humitos>`__: Do not send notification on VersionLockedError (`#4839 <https://github.com/readthedocs/readthedocs.org/pull/4839>`__)
* `@stsewd <https://github.com/stsewd>`__: Start testing config v2 on our project (`#4838 <https://github.com/readthedocs/readthedocs.org/pull/4838>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add all migrations that are missing from model changes (`#4837 <https://github.com/readthedocs/readthedocs.org/pull/4837>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add docstring to DrfJsonSerializer so we know why it's there (`#4836 <https://github.com/readthedocs/readthedocs.org/pull/4836>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Show the project's slug in the dashboard (`#4834 <https://github.com/readthedocs/readthedocs.org/pull/4834>`__)
* `@humitos <https://github.com/humitos>`__: Avoid infinite redirection (`#4833 <https://github.com/readthedocs/readthedocs.org/pull/4833>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Allow filtering builds by commit. (`#4831 <https://github.com/readthedocs/readthedocs.org/pull/4831>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Add 'Branding' under the 'Business Info' section and 'Guidelines' on 'Design Docs' (`#4830 <https://github.com/readthedocs/readthedocs.org/pull/4830>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Migrate old passwords without "set_unusable_password" (`#4829 <https://github.com/readthedocs/readthedocs.org/pull/4829>`__)
* `@humitos <https://github.com/humitos>`__: Do not import the Celery worker when running the Django app (`#4824 <https://github.com/readthedocs/readthedocs.org/pull/4824>`__)
* `@damianz5 <https://github.com/damianz5>`__: Fix for jQuery in doc-embed call (`#4819 <https://github.com/readthedocs/readthedocs.org/pull/4819>`__)
* `@invinciblycool <https://github.com/invinciblycool>`__: Add MkDocsYAMLParseError (`#4814 <https://github.com/readthedocs/readthedocs.org/pull/4814>`__)
* `@stsewd <https://github.com/stsewd>`__: Delete untracked tags on fetch (`#4811 <https://github.com/readthedocs/readthedocs.org/pull/4811>`__)
* `@stsewd <https://github.com/stsewd>`__: Don't activate version on build (`#4810 <https://github.com/readthedocs/readthedocs.org/pull/4810>`__)
* `@humitos <https://github.com/humitos>`__: Feature flag to make `readthedocs` theme default on MkDocs docs (`#4802 <https://github.com/readthedocs/readthedocs.org/pull/4802>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Allow use of `file://` urls in repos during development. (`#4801 <https://github.com/readthedocs/readthedocs.org/pull/4801>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 2.7.2 (`#4796 <https://github.com/readthedocs/readthedocs.org/pull/4796>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Raise 404 at SubdomainMiddleware if the project does not exist. (`#4795 <https://github.com/readthedocs/readthedocs.org/pull/4795>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Add help_text in the form for adopting a project (`#4781 <https://github.com/readthedocs/readthedocs.org/pull/4781>`__)
* `@humitos <https://github.com/humitos>`__: Add VAT ID field for Gold User (`#4776 <https://github.com/readthedocs/readthedocs.org/pull/4776>`__)
* `@sriks123 <https://github.com/sriks123>`__: Remove logic around finding config file inside directories (`#4755 <https://github.com/readthedocs/readthedocs.org/pull/4755>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Improve unexpected error message when build fails (`#4754 <https://github.com/readthedocs/readthedocs.org/pull/4754>`__)
* `@stsewd <https://github.com/stsewd>`__: Don't build latest on webhook if it is deactivated (`#4733 <https://github.com/readthedocs/readthedocs.org/pull/4733>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Change the way of using login_required decorator (`#4723 <https://github.com/readthedocs/readthedocs.org/pull/4723>`__)
* `@invinciblycool <https://github.com/invinciblycool>`__: Remove unused views and their translations. (`#4632 <https://github.com/readthedocs/readthedocs.org/pull/4632>`__)
* `@invinciblycool <https://github.com/invinciblycool>`__: Redirect to build detail post manual build (`#4622 <https://github.com/readthedocs/readthedocs.org/pull/4622>`__)
* `@anubhavsinha98 <https://github.com/anubhavsinha98>`__: Issue #4551 Changed mock docks to use sphinx (`#4569 <https://github.com/readthedocs/readthedocs.org/pull/4569>`__)
* `@xrmx <https://github.com/xrmx>`__: search: mark more strings for translation (`#4438 <https://github.com/readthedocs/readthedocs.org/pull/4438>`__)
* `@Alig1493 <https://github.com/Alig1493>`__: Fix for issue #4092: Remove unused field from Project model (`#4431 <https://github.com/readthedocs/readthedocs.org/pull/4431>`__)
* `@mashrikt <https://github.com/mashrikt>`__: Remove pytest _describe (`#4429 <https://github.com/readthedocs/readthedocs.org/pull/4429>`__)
* `@xrmx <https://github.com/xrmx>`__: static: use modern getJSON callbacks (`#4382 <https://github.com/readthedocs/readthedocs.org/pull/4382>`__)
* `@jaraco <https://github.com/jaraco>`__: Script for creating a project (`#4370 <https://github.com/readthedocs/readthedocs.org/pull/4370>`__)
* `@xrmx <https://github.com/xrmx>`__: make it easier to use a different default theme (`#4278 <https://github.com/readthedocs/readthedocs.org/pull/4278>`__)
* `@humitos <https://github.com/humitos>`__: Document alternate domains for business site (`#4271 <https://github.com/readthedocs/readthedocs.org/pull/4271>`__)
* `@xrmx <https://github.com/xrmx>`__: restapi/client: don't use DRF parser for parsing (`#4160 <https://github.com/readthedocs/readthedocs.org/pull/4160>`__)
* `@julienmalard <https://github.com/julienmalard>`__: New languages (`#3759 <https://github.com/readthedocs/readthedocs.org/pull/3759>`__)
* `@stsewd <https://github.com/stsewd>`__: Improve installation guide (`#3631 <https://github.com/readthedocs/readthedocs.org/pull/3631>`__)
* `@stsewd <https://github.com/stsewd>`__: Allow to hide version warning (`#3595 <https://github.com/readthedocs/readthedocs.org/pull/3595>`__)
* `@Alig1493 <https://github.com/Alig1493>`__: [Fixed #872] Filter Builds according to commit (`#3544 <https://github.com/readthedocs/readthedocs.org/pull/3544>`__)
* `@stsewd <https://github.com/stsewd>`__: Make slug field a valid DNS label (`#3464 <https://github.com/readthedocs/readthedocs.org/pull/3464>`__)

Version 2.8.0
-------------

:Date: October 30, 2018

Major change is an upgrade to Django 1.11.

* `@humitos <https://github.com/humitos>`__: Cleanup old code (remove old_div) (`#4817 <https://github.com/readthedocs/readthedocs.org/pull/4817>`__)
* `@humitos <https://github.com/humitos>`__: Remove unnecessary migration (`#4806 <https://github.com/readthedocs/readthedocs.org/pull/4806>`__)
* `@humitos <https://github.com/humitos>`__: Feature flag to make `readthedocs` theme default on MkDocs docs (`#4802 <https://github.com/readthedocs/readthedocs.org/pull/4802>`__)
* `@stsewd <https://github.com/stsewd>`__: Add codecov badge (`#4799 <https://github.com/readthedocs/readthedocs.org/pull/4799>`__)
* `@humitos <https://github.com/humitos>`__: Pin missing dependency for the MkDocs guide compatibility (`#4798 <https://github.com/readthedocs/readthedocs.org/pull/4798>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 2.7.2 (`#4796 <https://github.com/readthedocs/readthedocs.org/pull/4796>`__)
* `@humitos <https://github.com/humitos>`__: Do not log as error a webhook with an invalid branch name (`#4779 <https://github.com/readthedocs/readthedocs.org/pull/4779>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Run travis on release branches (`#4763 <https://github.com/readthedocs/readthedocs.org/pull/4763>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Remove Eric & Anthony from ADMINS & MANAGERS settings (`#4762 <https://github.com/readthedocs/readthedocs.org/pull/4762>`__)
* `@stsewd <https://github.com/stsewd>`__: Don't use RequestsContext (`#4759 <https://github.com/readthedocs/readthedocs.org/pull/4759>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Django 1.11 upgrade (`#4750 <https://github.com/readthedocs/readthedocs.org/pull/4750>`__)
* `@stsewd <https://github.com/stsewd>`__: Dropdown to select Advanced Settings (`#4710 <https://github.com/readthedocs/readthedocs.org/pull/4710>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove hardcoded constant from config module (`#4704 <https://github.com/readthedocs/readthedocs.org/pull/4704>`__)
* `@stsewd <https://github.com/stsewd>`__: Update tastypie (`#4325 <https://github.com/readthedocs/readthedocs.org/pull/4325>`__)
* `@stsewd <https://github.com/stsewd>`__: Update to Django 1.10 (`#4319 <https://github.com/readthedocs/readthedocs.org/pull/4319>`__)

Version 2.7.2
-------------

:Date: October 23, 2018

* `@humitos <https://github.com/humitos>`__: Validate the slug generated is valid before importing a project (`#4780 <https://github.com/readthedocs/readthedocs.org/pull/4780>`__)
* `@humitos <https://github.com/humitos>`__: Do not log as error a webhook with an invalid branch name (`#4779 <https://github.com/readthedocs/readthedocs.org/pull/4779>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add an index page to our design docs. (`#4775 <https://github.com/readthedocs/readthedocs.org/pull/4775>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Remove /embed API endpoint (`#4771 <https://github.com/readthedocs/readthedocs.org/pull/4771>`__)
* `@stsewd <https://github.com/stsewd>`__: Upgrade logs from debug on middleware (`#4769 <https://github.com/readthedocs/readthedocs.org/pull/4769>`__)
* `@humitos <https://github.com/humitos>`__: Link to SSL for Custom Domains fixed (`#4766 <https://github.com/readthedocs/readthedocs.org/pull/4766>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Remove Eric & Anthony from ADMINS & MANAGERS settings (`#4762 <https://github.com/readthedocs/readthedocs.org/pull/4762>`__)
* `@humitos <https://github.com/humitos>`__: Do not re-raise the exception if the one that we are checking (`#4761 <https://github.com/readthedocs/readthedocs.org/pull/4761>`__)
* `@humitos <https://github.com/humitos>`__: Do not fail when unlinking an non-existing path (`#4760 <https://github.com/readthedocs/readthedocs.org/pull/4760>`__)
* `@humitos <https://github.com/humitos>`__: Allow to extend the DomainForm from outside (`#4752 <https://github.com/readthedocs/readthedocs.org/pull/4752>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Fixes an OSX issue with the test suite (`#4748 <https://github.com/readthedocs/readthedocs.org/pull/4748>`__)
* `@humitos <https://github.com/humitos>`__: Use Docker time limit for max lock age (`#4747 <https://github.com/readthedocs/readthedocs.org/pull/4747>`__)
* `@xyNNN <https://github.com/xyNNN>`__: Fixed link of PagerDuty (`#4744 <https://github.com/readthedocs/readthedocs.org/pull/4744>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Make storage syncers extend from a base class (`#4742 <https://github.com/readthedocs/readthedocs.org/pull/4742>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Revert "Upgrade theme media to 0.4.2" (`#4735 <https://github.com/readthedocs/readthedocs.org/pull/4735>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Upgrade theme media to 0.4.2 (`#4734 <https://github.com/readthedocs/readthedocs.org/pull/4734>`__)
* `@stsewd <https://github.com/stsewd>`__: Extend install option from config file (v2, schema only) (`#4732 <https://github.com/readthedocs/readthedocs.org/pull/4732>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove /cname endpoint (`#4731 <https://github.com/readthedocs/readthedocs.org/pull/4731>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix get_vcs_repo by moving it to the Mixin (`#4727 <https://github.com/readthedocs/readthedocs.org/pull/4727>`__)
* `@humitos <https://github.com/humitos>`__: Guide explaining how to keep compatibility with mkdocs (`#4726 <https://github.com/readthedocs/readthedocs.org/pull/4726>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 2.7.1 (`#4725 <https://github.com/readthedocs/readthedocs.org/pull/4725>`__)
* `@dojutsu-user <https://github.com/dojutsu-user>`__: Fix the form for adopting a project (`#4721 <https://github.com/readthedocs/readthedocs.org/pull/4721>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Remove logging verbosity on syncer failure (`#4717 <https://github.com/readthedocs/readthedocs.org/pull/4717>`__)
* `@humitos <https://github.com/humitos>`__: Lint requirement file for py2 (`#4712 <https://github.com/readthedocs/readthedocs.org/pull/4712>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Improve the getting started docs (`#4676 <https://github.com/readthedocs/readthedocs.org/pull/4676>`__)
* `@stsewd <https://github.com/stsewd>`__: Strict validation in configuration file (v2 only) (`#4607 <https://github.com/readthedocs/readthedocs.org/pull/4607>`__)
* `@stsewd <https://github.com/stsewd>`__: Run coverage on travis (`#4605 <https://github.com/readthedocs/readthedocs.org/pull/4605>`__)

Version 2.7.1
-------------

:Date: October 04, 2018

* `@ericholscher <https://github.com/ericholscher>`__: Revert "Merge pull request #4636 from readthedocs/search_upgrade" (`#4716 <https://github.com/readthedocs/readthedocs.org/pull/4716>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Reduce the logging we do on CNAME 404 (`#4715 <https://github.com/readthedocs/readthedocs.org/pull/4715>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Minor redirect admin improvements (`#4709 <https://github.com/readthedocs/readthedocs.org/pull/4709>`__)
* `@humitos <https://github.com/humitos>`__: Define the doc_search reverse URL from inside the __init__ on test (`#4703 <https://github.com/readthedocs/readthedocs.org/pull/4703>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Revert "auto refresh false" (`#4701 <https://github.com/readthedocs/readthedocs.org/pull/4701>`__)
* `@browniebroke <https://github.com/browniebroke>`__: Remove unused package nilsimsa (`#4697 <https://github.com/readthedocs/readthedocs.org/pull/4697>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix broken url on sphinx projects (`#4696 <https://github.com/readthedocs/readthedocs.org/pull/4696>`__)
* `@safwanrahman <https://github.com/safwanrahman>`__: Tuning elasticsearch shard and replica (`#4689 <https://github.com/readthedocs/readthedocs.org/pull/4689>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix bug where we were not indexing Sphinx HTMLDir projects (`#4685 <https://github.com/readthedocs/readthedocs.org/pull/4685>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix the queryset used in chunking (`#4683 <https://github.com/readthedocs/readthedocs.org/pull/4683>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix python 2 syntax for getting first key in search index update (`#4682 <https://github.com/readthedocs/readthedocs.org/pull/4682>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Release 2.7.0 (`#4681 <https://github.com/readthedocs/readthedocs.org/pull/4681>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Increase footer ad text size (`#4678 <https://github.com/readthedocs/readthedocs.org/pull/4678>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Fix broken docs links (`#4677 <https://github.com/readthedocs/readthedocs.org/pull/4677>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Remove search autosync from tests so local tests work (`#4675 <https://github.com/readthedocs/readthedocs.org/pull/4675>`__)
* `@stsewd <https://github.com/stsewd>`__: Refactor tasks into decorators (`#4666 <https://github.com/readthedocs/readthedocs.org/pull/4666>`__)
* `@stsewd <https://github.com/stsewd>`__: Clean up logging (`#4665 <https://github.com/readthedocs/readthedocs.org/pull/4665>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Ad customization docs (`#4659 <https://github.com/readthedocs/readthedocs.org/pull/4659>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Fix a typo in the privacy policy (`#4658 <https://github.com/readthedocs/readthedocs.org/pull/4658>`__)
* `@stsewd <https://github.com/stsewd>`__: Refactor PublicTask into a decorator task (`#4656 <https://github.com/readthedocs/readthedocs.org/pull/4656>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove -r option from update_repos command (`#4653 <https://github.com/readthedocs/readthedocs.org/pull/4653>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Create an explicit ad placement (`#4647 <https://github.com/readthedocs/readthedocs.org/pull/4647>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Use collectstatic on `media/`, without collecting user files (`#4502 <https://github.com/readthedocs/readthedocs.org/pull/4502>`__)
* `@stsewd <https://github.com/stsewd>`__: Implement submodules key from v2 config (`#4493 <https://github.com/readthedocs/readthedocs.org/pull/4493>`__)
* `@stsewd <https://github.com/stsewd>`__: Implement mkdocs key from v2 config (`#4486 <https://github.com/readthedocs/readthedocs.org/pull/4486>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Add docs on our roadmap process (`#4469 <https://github.com/readthedocs/readthedocs.org/pull/4469>`__)
* `@humitos <https://github.com/humitos>`__: Send notifications when generic/unhandled failures (`#3864 <https://github.com/readthedocs/readthedocs.org/pull/3864>`__)
* `@stsewd <https://github.com/stsewd>`__: Use relative path for docroot on mkdocs (`#3525 <https://github.com/readthedocs/readthedocs.org/pull/3525>`__)

Version 2.7.0
-------------

:Date: September 29, 2018

**Reverted, do not use**

Version 2.6.6
-------------

:Date: September 25, 2018

* `@davidfischer <https://github.com/davidfischer>`__: Fix a markdown test error (`#4663 <https://github.com/readthedocs/readthedocs.org/pull/4663>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Ad customization docs (`#4659 <https://github.com/readthedocs/readthedocs.org/pull/4659>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Fix a typo in the privacy policy (`#4658 <https://github.com/readthedocs/readthedocs.org/pull/4658>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Put search step back into project build task (`#4655 <https://github.com/readthedocs/readthedocs.org/pull/4655>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Create an explicit ad placement (`#4647 <https://github.com/readthedocs/readthedocs.org/pull/4647>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix some typos in docs and code (`#4646 <https://github.com/readthedocs/readthedocs.org/pull/4646>`__)
* `@stsewd <https://github.com/stsewd>`__: Downgrade celery (`#4644 <https://github.com/readthedocs/readthedocs.org/pull/4644>`__)
* `@stsewd <https://github.com/stsewd>`__: Downgrade django-taggit (`#4639 <https://github.com/readthedocs/readthedocs.org/pull/4639>`__)
* `@safwanrahman <https://github.com/safwanrahman>`__: [Fix #4247] deleting old search code (`#4635 <https://github.com/readthedocs/readthedocs.org/pull/4635>`__)
* `@stsewd <https://github.com/stsewd>`__: Add change versions slug to faq (`#4633 <https://github.com/readthedocs/readthedocs.org/pull/4633>`__)
* `@stsewd <https://github.com/stsewd>`__: Pin sphinx to a compatible version (`#4631 <https://github.com/readthedocs/readthedocs.org/pull/4631>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Make ads more obvious that they are ads (`#4628 <https://github.com/readthedocs/readthedocs.org/pull/4628>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Change mentions of "CNAME" -> custom domain (`#4627 <https://github.com/readthedocs/readthedocs.org/pull/4627>`__)
* `@invinciblycool <https://github.com/invinciblycool>`__: Use validate_dict for more accurate error messages (`#4617 <https://github.com/readthedocs/readthedocs.org/pull/4617>`__)
* `@safwanrahman <https://github.com/safwanrahman>`__: fixing the indexing (`#4615 <https://github.com/readthedocs/readthedocs.org/pull/4615>`__)
* `@humitos <https://github.com/humitos>`__: Update our sponsors to mention Azure (`#4614 <https://github.com/readthedocs/readthedocs.org/pull/4614>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Add cwd to subprocess calls (`#4611 <https://github.com/readthedocs/readthedocs.org/pull/4611>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Make restapi URL additions conditional (`#4609 <https://github.com/readthedocs/readthedocs.org/pull/4609>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Ability to use supervisor from python 2.7 and still run Python 3 (`#4606 <https://github.com/readthedocs/readthedocs.org/pull/4606>`__)
* `@humitos <https://github.com/humitos>`__: Return 404 for inactive versions and allow redirects on them (`#4599 <https://github.com/readthedocs/readthedocs.org/pull/4599>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Fixes an issue with duplicate gold subscriptions (`#4597 <https://github.com/readthedocs/readthedocs.org/pull/4597>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Fix ad block nag project issue (`#4596 <https://github.com/readthedocs/readthedocs.org/pull/4596>`__)
* `@humitos <https://github.com/humitos>`__: Run all our tests with Python 3.6 on Travis (`#4592 <https://github.com/readthedocs/readthedocs.org/pull/4592>`__)
* `@humitos <https://github.com/humitos>`__: Sanitize command output when running under DockerBuildEnvironment (`#4591 <https://github.com/readthedocs/readthedocs.org/pull/4591>`__)
* `@humitos <https://github.com/humitos>`__: Force resolver to use PUBLIC_DOMAIN over HTTPS if not Domain.https (`#4579 <https://github.com/readthedocs/readthedocs.org/pull/4579>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Updates and simplification for mkdocs (`#4556 <https://github.com/readthedocs/readthedocs.org/pull/4556>`__)
* `@humitos <https://github.com/humitos>`__: Docs for hiding "On ..." section from versions menu (`#4547 <https://github.com/readthedocs/readthedocs.org/pull/4547>`__)
* `@stsewd <https://github.com/stsewd>`__: Implement sphinx key from v2 config (`#4482 <https://github.com/readthedocs/readthedocs.org/pull/4482>`__)
* `@safwanrahman <https://github.com/safwanrahman>`__: [Fix #4268] Adding Documentation for upgraded Search (`#4467 <https://github.com/readthedocs/readthedocs.org/pull/4467>`__)
* `@humitos <https://github.com/humitos>`__: Upgrade all packages using pur (`#4318 <https://github.com/readthedocs/readthedocs.org/pull/4318>`__)
* `@humitos <https://github.com/humitos>`__: Clean CC sensible data on Gold subscriptions (`#4291 <https://github.com/readthedocs/readthedocs.org/pull/4291>`__)
* `@stsewd <https://github.com/stsewd>`__: Update docs to match the new triague guidelines (`#4260 <https://github.com/readthedocs/readthedocs.org/pull/4260>`__)
* `@xrmx <https://github.com/xrmx>`__: Make the STABLE and LATEST constants overridable (`#4099 <https://github.com/readthedocs/readthedocs.org/pull/4099>`__)
* `@stsewd <https://github.com/stsewd>`__: Use str to get the exception message (`#3912 <https://github.com/readthedocs/readthedocs.org/pull/3912>`__)

Version 2.6.5
-------------

:Date: August 29, 2018

* `@stsewd <https://github.com/stsewd>`__: Tests for yaml file regex (`#4587 <https://github.com/readthedocs/readthedocs.org/pull/4587>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Respect user language when caching homepage (`#4585 <https://github.com/readthedocs/readthedocs.org/pull/4585>`__)
* `@humitos <https://github.com/humitos>`__: Add start and termination to YAML file regex (`#4584 <https://github.com/readthedocs/readthedocs.org/pull/4584>`__)
* `@safwanrahman <https://github.com/safwanrahman>`__: [Fix #4576] Do not delete projects which have multiple users (`#4577 <https://github.com/readthedocs/readthedocs.org/pull/4577>`__)

Version 2.6.4
-------------

:Date: August 29, 2018

* `@stsewd <https://github.com/stsewd>`__: Update tests failing on master (`#4575 <https://github.com/readthedocs/readthedocs.org/pull/4575>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Add a flag to disable docsearch (`#4570 <https://github.com/readthedocs/readthedocs.org/pull/4570>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix nested syntax in docs (`#4567 <https://github.com/readthedocs/readthedocs.org/pull/4567>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix incorrect reraise (`#4566 <https://github.com/readthedocs/readthedocs.org/pull/4566>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Add a note about specifying the version of build tools (`#4562 <https://github.com/readthedocs/readthedocs.org/pull/4562>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Serve badges directly from local filesystem (`#4561 <https://github.com/readthedocs/readthedocs.org/pull/4561>`__)
* `@humitos <https://github.com/humitos>`__: Build JSON artifacts in HTML builder (`#4554 <https://github.com/readthedocs/readthedocs.org/pull/4554>`__)
* `@humitos <https://github.com/humitos>`__: Route task to proper queue (`#4553 <https://github.com/readthedocs/readthedocs.org/pull/4553>`__)
* `@humitos <https://github.com/humitos>`__: Sanitize BuildCommand.output by removing NULL characters (`#4552 <https://github.com/readthedocs/readthedocs.org/pull/4552>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Fix changelog for 2.6.3 (`#4548 <https://github.com/readthedocs/readthedocs.org/pull/4548>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Remove hiredis (`#4542 <https://github.com/readthedocs/readthedocs.org/pull/4542>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Use the STATIC_URL for static files to avoid redirection (`#4522 <https://github.com/readthedocs/readthedocs.org/pull/4522>`__)
* `@stsewd <https://github.com/stsewd>`__: Update docs about build process (`#4515 <https://github.com/readthedocs/readthedocs.org/pull/4515>`__)
* `@StefanoChiodino <https://github.com/StefanoChiodino>`__: Allow for period as a prefix and yaml extension for config file (`#4512 <https://github.com/readthedocs/readthedocs.org/pull/4512>`__)
* `@AumitLeon <https://github.com/AumitLeon>`__: Update information on mkdocs build process (`#4508 <https://github.com/readthedocs/readthedocs.org/pull/4508>`__)
* `@humitos <https://github.com/humitos>`__: Fix Exact Redirect to work properly when using $rest keyword (`#4501 <https://github.com/readthedocs/readthedocs.org/pull/4501>`__)
* `@humitos <https://github.com/humitos>`__: Mark some BuildEnvironmentError exceptions as Warning and do not log them (`#4495 <https://github.com/readthedocs/readthedocs.org/pull/4495>`__)
* `@xrmx <https://github.com/xrmx>`__: projects: don't explode trying to update UpdateDocsTaskStep state (`#4485 <https://github.com/readthedocs/readthedocs.org/pull/4485>`__)
* `@humitos <https://github.com/humitos>`__: Note with the developer flow to update our app translations (`#4481 <https://github.com/readthedocs/readthedocs.org/pull/4481>`__)
* `@humitos <https://github.com/humitos>`__: Add `trimmed` to all multilines `blocktrans` tags (`#4480 <https://github.com/readthedocs/readthedocs.org/pull/4480>`__)
* `@humitos <https://github.com/humitos>`__: Example and note with usage of trimmed option in blocktrans (`#4479 <https://github.com/readthedocs/readthedocs.org/pull/4479>`__)
* `@humitos <https://github.com/humitos>`__: Update Transifex resources for our documentation (`#4478 <https://github.com/readthedocs/readthedocs.org/pull/4478>`__)
* `@humitos <https://github.com/humitos>`__: Documentation for Manage Translations (`#4470 <https://github.com/readthedocs/readthedocs.org/pull/4470>`__)
* `@stsewd <https://github.com/stsewd>`__: Port https://github.com/readthedocs/readthedocs-build/pull/38/ (`#4461 <https://github.com/readthedocs/readthedocs.org/pull/4461>`__)
* `@stsewd <https://github.com/stsewd>`__: Match v1 config interface to new one (`#4456 <https://github.com/readthedocs/readthedocs.org/pull/4456>`__)
* `@humitos <https://github.com/humitos>`__: Skip tags that point to blob objects instead of commits (`#4442 <https://github.com/readthedocs/readthedocs.org/pull/4442>`__)
* `@stsewd <https://github.com/stsewd>`__: Document python.use_system_site_packages option (`#4422 <https://github.com/readthedocs/readthedocs.org/pull/4422>`__)
* `@humitos <https://github.com/humitos>`__: More tips about how to reduce resources usage (`#4419 <https://github.com/readthedocs/readthedocs.org/pull/4419>`__)
* `@xrmx <https://github.com/xrmx>`__: projects: user in ProjectQuerySetBase.for_admin_user is mandatory (`#4417 <https://github.com/readthedocs/readthedocs.org/pull/4417>`__)

Version 2.6.3
-------------

:Date: August 18, 2018

Release to Azure!

* `@davidfischer <https://github.com/davidfischer>`__: Add Sponsors list to footer (`#4424 <https://github.com/readthedocs/readthedocs.org/pull/4424>`__)
* `@stsewd <https://github.com/stsewd>`__: Cache node_modules to speed up CI (`#4484 <https://github.com/readthedocs/readthedocs.org/pull/4484>`__)
* `@xrmx <https://github.com/xrmx>`__: templates: mark missing string for translation on project edit (`#4518 <https://github.com/readthedocs/readthedocs.org/pull/4518>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Performance improvement: cache version listing on the homepage (`#4526 <https://github.com/readthedocs/readthedocs.org/pull/4526>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Remove mailgun from our dependencies (`#4531 <https://github.com/readthedocs/readthedocs.org/pull/4531>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Improved ad block detection (`#4532 <https://github.com/readthedocs/readthedocs.org/pull/4532>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Revert "Remove SelectiveFileSystemFolder finder workaround" (`#4533 <https://github.com/readthedocs/readthedocs.org/pull/4533>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Slight clarification on turning off ads for a project (`#4534 <https://github.com/readthedocs/readthedocs.org/pull/4534>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Fix the sponsor image paths (`#4535 <https://github.com/readthedocs/readthedocs.org/pull/4535>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Update build assets (`#4537 <https://github.com/readthedocs/readthedocs.org/pull/4537>`__)


Version 2.6.2
-------------

:Date: August 14, 2018

* `@davidfischer <https://github.com/davidfischer>`__: Custom domain clarifications (`#4514 <https://github.com/readthedocs/readthedocs.org/pull/4514>`__)
* `@trein <https://github.com/trein>`__: Use single quote throughout the file (`#4513 <https://github.com/readthedocs/readthedocs.org/pull/4513>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Support ads on pallets themes (`#4499 <https://github.com/readthedocs/readthedocs.org/pull/4499>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Only use HostHeaderSSLAdapter for SSL/HTTPS connections (`#4498 <https://github.com/readthedocs/readthedocs.org/pull/4498>`__)
* `@keflavich <https://github.com/keflavich>`__: Very minor English correction (`#4497 <https://github.com/readthedocs/readthedocs.org/pull/4497>`__)
* `@davidfischer <https://github.com/davidfischer>`__: All static media is run through "collectstatic" (`#4489 <https://github.com/readthedocs/readthedocs.org/pull/4489>`__)
* `@humitos <https://github.com/humitos>`__: Fix reST structure (`#4488 <https://github.com/readthedocs/readthedocs.org/pull/4488>`__)
* `@nijel <https://github.com/nijel>`__: Document expected delay on CNAME change and need for CAA (`#4487 <https://github.com/readthedocs/readthedocs.org/pull/4487>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Allow enforcing HTTPS for custom domains (`#4483 <https://github.com/readthedocs/readthedocs.org/pull/4483>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Add some details around community ad qualifications (`#4436 <https://github.com/readthedocs/readthedocs.org/pull/4436>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Updates to manifest storage (`#4430 <https://github.com/readthedocs/readthedocs.org/pull/4430>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Update alt domains docs with SSL (`#4425 <https://github.com/readthedocs/readthedocs.org/pull/4425>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Add SNI support for API HTTPS endpoint (`#4423 <https://github.com/readthedocs/readthedocs.org/pull/4423>`__)
* `@davidfischer <https://github.com/davidfischer>`__: API v1 cleanup (`#4415 <https://github.com/readthedocs/readthedocs.org/pull/4415>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Allow filtering versions by active (`#4414 <https://github.com/readthedocs/readthedocs.org/pull/4414>`__)
* `@mlncn <https://github.com/mlncn>`__: Fix broken link (`#4410 <https://github.com/readthedocs/readthedocs.org/pull/4410>`__)
* `@safwanrahman <https://github.com/safwanrahman>`__: [Fix #4407] Port Project Search for Elasticsearch 6.x (`#4408 <https://github.com/readthedocs/readthedocs.org/pull/4408>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Add client ID to Google Analytics requests (`#4404 <https://github.com/readthedocs/readthedocs.org/pull/4404>`__)
* `@xrmx <https://github.com/xrmx>`__: projects: fix filtering in projects_tag_detail (`#4398 <https://github.com/readthedocs/readthedocs.org/pull/4398>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Fix a proxy model bug related to ad-free (`#4390 <https://github.com/readthedocs/readthedocs.org/pull/4390>`__)
* `@humitos <https://github.com/humitos>`__: Release 2.6.1 (`#4389 <https://github.com/readthedocs/readthedocs.org/pull/4389>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Do not access database from builds to check ad-free (`#4387 <https://github.com/readthedocs/readthedocs.org/pull/4387>`__)
* `@humitos <https://github.com/humitos>`__: Adapt YAML config integration tests (`#4385 <https://github.com/readthedocs/readthedocs.org/pull/4385>`__)
* `@stsewd <https://github.com/stsewd>`__: Set full `source_file` path for default configuration (`#4379 <https://github.com/readthedocs/readthedocs.org/pull/4379>`__)
* `@humitos <https://github.com/humitos>`__: Make `get_version` usable from a specified path (`#4376 <https://github.com/readthedocs/readthedocs.org/pull/4376>`__)
* `@humitos <https://github.com/humitos>`__: More tags when logging errors to Sentry (`#4375 <https://github.com/readthedocs/readthedocs.org/pull/4375>`__)
* `@humitos <https://github.com/humitos>`__: Check for 'options' in update_repos command (`#4373 <https://github.com/readthedocs/readthedocs.org/pull/4373>`__)
* `@safwanrahman <https://github.com/safwanrahman>`__: [Fix  #4333] Implement asynchronous search reindex functionality using celery (`#4368 <https://github.com/readthedocs/readthedocs.org/pull/4368>`__)
* `@stsewd <https://github.com/stsewd>`__: V2 of the configuration file (`#4355 <https://github.com/readthedocs/readthedocs.org/pull/4355>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Remove the UID from the GA measurement protocol (`#4347 <https://github.com/readthedocs/readthedocs.org/pull/4347>`__)
* `@humitos <https://github.com/humitos>`__: Mount `pip_cache_path` in Docker container (`#3556 <https://github.com/readthedocs/readthedocs.org/pull/3556>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Show subprojects in search results (`#1866 <https://github.com/readthedocs/readthedocs.org/pull/1866>`__)

Version 2.6.1
-------------

:Date: July 17, 2018

* `@davidfischer <https://github.com/davidfischer>`__: Do not access database from builds to check ad-free (`#4387 <https://github.com/readthedocs/readthedocs.org/pull/4387>`__)
* `@humitos <https://github.com/humitos>`__: Adapt YAML config integration tests (`#4385 <https://github.com/readthedocs/readthedocs.org/pull/4385>`__)
* `@stsewd <https://github.com/stsewd>`__: Set full `source_file` path for default configuration (`#4379 <https://github.com/readthedocs/readthedocs.org/pull/4379>`__)
* `@humitos <https://github.com/humitos>`__: More tags when logging errors to Sentry (`#4375 <https://github.com/readthedocs/readthedocs.org/pull/4375>`__)

Version 2.6.0
-------------

:Date: July 16, 2018

* Adds initial support for HTTPS on custom domains
* `@stsewd <https://github.com/stsewd>`__: Revert "projects: serve badge with same protocol as site" (`#4353 <https://github.com/readthedocs/readthedocs.org/pull/4353>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Do not overwrite sphinx context variables feature (`#4349 <https://github.com/readthedocs/readthedocs.org/pull/4349>`__)
* `@stsewd <https://github.com/stsewd>`__: Calrify docs about how rtd select the stable version (`#4348 <https://github.com/readthedocs/readthedocs.org/pull/4348>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Remove the UID from the GA measurement protocol (`#4347 <https://github.com/readthedocs/readthedocs.org/pull/4347>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix error in command (`#4345 <https://github.com/readthedocs/readthedocs.org/pull/4345>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Improvements for the build/version admin (`#4344 <https://github.com/readthedocs/readthedocs.org/pull/4344>`__)
* `@safwanrahman <https://github.com/safwanrahman>`__: [Fix #4265] Porting frontend docsearch to work with new API (`#4340 <https://github.com/readthedocs/readthedocs.org/pull/4340>`__)
* `@ktdreyer <https://github.com/ktdreyer>`__: fix spelling of "demonstrating" (`#4336 <https://github.com/readthedocs/readthedocs.org/pull/4336>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Warning about theme context implementation status (`#4335 <https://github.com/readthedocs/readthedocs.org/pull/4335>`__)
* `@Blendify <https://github.com/Blendify>`__: Docs: Let Theme Choose Pygments Theme (`#4331 <https://github.com/readthedocs/readthedocs.org/pull/4331>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Disable the ad block nag for ad-free projects (`#4329 <https://github.com/readthedocs/readthedocs.org/pull/4329>`__)
* `@safwanrahman <https://github.com/safwanrahman>`__: [fix #4265] Port Document search API for Elasticsearch 6.x (`#4309 <https://github.com/readthedocs/readthedocs.org/pull/4309>`__)
* `@stsewd <https://github.com/stsewd>`__: Refactor configuration object to class based (`#4298 <https://github.com/readthedocs/readthedocs.org/pull/4298>`__)

Version 2.5.3
-------------

:Date: July 05, 2018

* `@xrmx <https://github.com/xrmx>`__: Do less work in querysets (`#4322 <https://github.com/readthedocs/readthedocs.org/pull/4322>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix deprecations in management commands (`#4321 <https://github.com/readthedocs/readthedocs.org/pull/4321>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Add a flag for marking a project ad-free (`#4313 <https://github.com/readthedocs/readthedocs.org/pull/4313>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Use "npm run lint" from tox (`#4312 <https://github.com/readthedocs/readthedocs.org/pull/4312>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Fix issues building static assets (`#4311 <https://github.com/readthedocs/readthedocs.org/pull/4311>`__)
* `@humitos <https://github.com/humitos>`__: Use PATHs to call clear_artifacts (`#4296 <https://github.com/readthedocs/readthedocs.org/pull/4296>`__)
* `@safwanrahman <https://github.com/safwanrahman>`__: [Fix #2457] Implement exact match search (`#4292 <https://github.com/readthedocs/readthedocs.org/pull/4292>`__)
* `@davidfischer <https://github.com/davidfischer>`__: API filtering improvements (`#4285 <https://github.com/readthedocs/readthedocs.org/pull/4285>`__)
* `@annegentle <https://github.com/annegentle>`__: Remove self-referencing links for webhooks docs (`#4283 <https://github.com/readthedocs/readthedocs.org/pull/4283>`__)
* `@safwanrahman <https://github.com/safwanrahman>`__: [Fix #2328 #2013] Refresh search index and test for case insensitive search (`#4277 <https://github.com/readthedocs/readthedocs.org/pull/4277>`__)
* `@xrmx <https://github.com/xrmx>`__: doc_builder: clarify sphinx backend append_conf docstring (`#4276 <https://github.com/readthedocs/readthedocs.org/pull/4276>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Add documentation for APIv2 (`#4274 <https://github.com/readthedocs/readthedocs.org/pull/4274>`__)
* `@humitos <https://github.com/humitos>`__: Wrap notifications HTML code into a block (`#4273 <https://github.com/readthedocs/readthedocs.org/pull/4273>`__)
* `@stsewd <https://github.com/stsewd>`__: Move config.py from rtd build (`#4272 <https://github.com/readthedocs/readthedocs.org/pull/4272>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix our use of `--use-wheel` in pip. (`#4269 <https://github.com/readthedocs/readthedocs.org/pull/4269>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Revert "Merge pull request #4206 from FlorianKuckelkorn/fix/pip-breaking-change" (`#4261 <https://github.com/readthedocs/readthedocs.org/pull/4261>`__)
* `@humitos <https://github.com/humitos>`__: Fix triggering a build for a skipped project (`#4255 <https://github.com/readthedocs/readthedocs.org/pull/4255>`__)
* `@stsewd <https://github.com/stsewd>`__: Update default sphinx version (`#4250 <https://github.com/readthedocs/readthedocs.org/pull/4250>`__)
* `@stsewd <https://github.com/stsewd>`__: Move config module from rtd-build repo (`#4242 <https://github.com/readthedocs/readthedocs.org/pull/4242>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Allow staying logged in for longer (`#4236 <https://github.com/readthedocs/readthedocs.org/pull/4236>`__)
* `@safwanrahman <https://github.com/safwanrahman>`__: Upgrade Elasticsearch to version 6.x (`#4211 <https://github.com/readthedocs/readthedocs.org/pull/4211>`__)
* `@humitos <https://github.com/humitos>`__: Make tests extensible from corporate site (`#4095 <https://github.com/readthedocs/readthedocs.org/pull/4095>`__)
* `@stsewd <https://github.com/stsewd>`__: `stable` version stuck on a specific commit (`#3913 <https://github.com/readthedocs/readthedocs.org/pull/3913>`__)

Version 2.5.2
-------------

:Date: June 18, 2018

* `@davidfischer <https://github.com/davidfischer>`_: Add a page detailing ad blocking (`#4244 <https://github.com/readthedocs/readthedocs.org/pull/4244>`_)
* `@xrmx <https://github.com/xrmx>`_: projects: serve badge with same protocol as site (`#4228 <https://github.com/readthedocs/readthedocs.org/pull/4228>`_)
* `@FlorianKuckelkorn <https://github.com/FlorianKuckelkorn>`_: Fixed breaking change in pip 10.0.0b1 (2018-03-31) (`#4206 <https://github.com/readthedocs/readthedocs.org/pull/4206>`_)
* `@StefanoChiodino <https://github.com/StefanoChiodino>`_: Document that readthedocs file can now have yaml extension (`#4129 <https://github.com/readthedocs/readthedocs.org/pull/4129>`_)
* `@humitos <https://github.com/humitos>`_: Downgrade docker to 3.1.3 because of timeouts in EXEC call (`#4241 <https://github.com/readthedocs/readthedocs.org/pull/4241>`_)
* `@stsewd <https://github.com/stsewd>`_: Move parser tests from rtd-build repo (`#4225 <https://github.com/readthedocs/readthedocs.org/pull/4225>`_)
* `@humitos <https://github.com/humitos>`_: Handle revoked oauth permissions by the user (`#4074 <https://github.com/readthedocs/readthedocs.org/pull/4074>`_)
* `@humitos <https://github.com/humitos>`_: Allow to hook the initial build from outside (`#4033 <https://github.com/readthedocs/readthedocs.org/pull/4033>`_)

Version 2.5.1
-------------

:Date: June 14, 2018

* `@stsewd <https://github.com/stsewd>`_: Add feature to build json with html in the same build (`#4229 <https://github.com/readthedocs/readthedocs.org/pull/4229>`_)
* `@davidfischer <https://github.com/davidfischer>`_: Prioritize ads based on content (`#4224 <https://github.com/readthedocs/readthedocs.org/pull/4224>`_)
* `@mostaszewski <https://github.com/mostaszewski>`_: #4170 - Link the version in the footer to the changelog (`#4217 <https://github.com/readthedocs/readthedocs.org/pull/4217>`_)
* `@Jmennius <https://github.com/Jmennius>`_: Add provision_elasticsearch command (`#4216 <https://github.com/readthedocs/readthedocs.org/pull/4216>`_)
* `@SuriyaaKudoIsc <https://github.com/SuriyaaKudoIsc>`_: Use the latest YouTube share URL (`#4209 <https://github.com/readthedocs/readthedocs.org/pull/4209>`_)
* `@davidfischer <https://github.com/davidfischer>`_: Allow staff to trigger project builds (`#4207 <https://github.com/readthedocs/readthedocs.org/pull/4207>`_)
* `@davidfischer <https://github.com/davidfischer>`_: Use autosectionlabel in the privacy policy (`#4204 <https://github.com/readthedocs/readthedocs.org/pull/4204>`_)
* `@davidfischer <https://github.com/davidfischer>`_: These links weren't correct after #3632 (`#4203 <https://github.com/readthedocs/readthedocs.org/pull/4203>`_)
* `@davidfischer <https://github.com/davidfischer>`_: Release 2.5.0 (`#4200 <https://github.com/readthedocs/readthedocs.org/pull/4200>`_)
* `@ericholscher <https://github.com/ericholscher>`_: Fix Build: Convert md to rst in docs (`#4199 <https://github.com/readthedocs/readthedocs.org/pull/4199>`_)
* `@ericholscher <https://github.com/ericholscher>`_: Updates to #3850 to fix merge conflict (`#4198 <https://github.com/readthedocs/readthedocs.org/pull/4198>`_)
* `@ericholscher <https://github.com/ericholscher>`_: Build on top of #3881 and put docs in custom_installs. (`#4196 <https://github.com/readthedocs/readthedocs.org/pull/4196>`_)
* `@davidfischer <https://github.com/davidfischer>`_: Increase the max theme version (`#4195 <https://github.com/readthedocs/readthedocs.org/pull/4195>`_)
* `@ericholscher <https://github.com/ericholscher>`_: Remove maxcdn reqs (`#4194 <https://github.com/readthedocs/readthedocs.org/pull/4194>`_)
* `@ericholscher <https://github.com/ericholscher>`_: Add missing gitignore item for ES testing (`#4193 <https://github.com/readthedocs/readthedocs.org/pull/4193>`_)
* `@xrmx <https://github.com/xrmx>`_: fabfile: update i18n helpers (`#4189 <https://github.com/readthedocs/readthedocs.org/pull/4189>`_)
* `@xrmx <https://github.com/xrmx>`_: Update italian locale (`#4188 <https://github.com/readthedocs/readthedocs.org/pull/4188>`_)
* `@xrmx <https://github.com/xrmx>`_: locale: update and build the english translation (`#4187 <https://github.com/readthedocs/readthedocs.org/pull/4187>`_)
* `@humitos <https://github.com/humitos>`_: Upgrade celery to avoid AtributeError:async (`#4185 <https://github.com/readthedocs/readthedocs.org/pull/4185>`_)
* `@stsewd <https://github.com/stsewd>`_: Prepare code for custo mkdocs.yaml location (`#4184 <https://github.com/readthedocs/readthedocs.org/pull/4184>`_)
* `@agjohnson <https://github.com/agjohnson>`_: Updates to our triage guidelines (`#4180 <https://github.com/readthedocs/readthedocs.org/pull/4180>`_)
* `@davidfischer <https://github.com/davidfischer>`_: Server side analytics (`#4131 <https://github.com/readthedocs/readthedocs.org/pull/4131>`_)
* `@humitos <https://github.com/humitos>`_: Upgrade packages with pur (`#4124 <https://github.com/readthedocs/readthedocs.org/pull/4124>`_)
* `@stsewd <https://github.com/stsewd>`_: Fix resync remote repos (`#4113 <https://github.com/readthedocs/readthedocs.org/pull/4113>`_)
* `@stsewd <https://github.com/stsewd>`_: Add schema for configuration file with yamale (`#4084 <https://github.com/readthedocs/readthedocs.org/pull/4084>`_)
* `@davidfischer <https://github.com/davidfischer>`_: Ad block nag to urge people to whitelist (`#4037 <https://github.com/readthedocs/readthedocs.org/pull/4037>`_)
* `@benjaoming <https://github.com/benjaoming>`_: Add Mexican Spanish as a project language (`#3588 <https://github.com/readthedocs/readthedocs.org/pull/3588>`_)

Version 2.5.0
-------------

:Date: June 06, 2018

* `@ericholscher <https://github.com/ericholscher>`_: Fix Build: Convert md to rst in docs (`#4199 <https://github.com/readthedocs/readthedocs.org/pull/4199>`_)
* `@ericholscher <https://github.com/ericholscher>`_: Remove maxcdn reqs (`#4194 <https://github.com/readthedocs/readthedocs.org/pull/4194>`_)
* `@ericholscher <https://github.com/ericholscher>`_: Add missing gitignore item for ES testing (`#4193 <https://github.com/readthedocs/readthedocs.org/pull/4193>`_)
* `@xrmx <https://github.com/xrmx>`_: fabfile: update i18n helpers (`#4189 <https://github.com/readthedocs/readthedocs.org/pull/4189>`_)
* `@xrmx <https://github.com/xrmx>`_: Update italian locale (`#4188 <https://github.com/readthedocs/readthedocs.org/pull/4188>`_)
* `@xrmx <https://github.com/xrmx>`_: locale: update and build the english translation (`#4187 <https://github.com/readthedocs/readthedocs.org/pull/4187>`_)
* `@safwanrahman <https://github.com/safwanrahman>`_: Test for search functionality (`#4116 <https://github.com/readthedocs/readthedocs.org/pull/4116>`_)
* `@davidfischer <https://github.com/davidfischer>`_: Update mkdocs to the latest (`#4041 <https://github.com/readthedocs/readthedocs.org/pull/4041>`_)
* `@davidfischer <https://github.com/davidfischer>`_: Ad block nag to urge people to whitelist (`#4037 <https://github.com/readthedocs/readthedocs.org/pull/4037>`_)
* `@davidfischer <https://github.com/davidfischer>`_: Decouple the theme JS from readthedocs.org (`#3968 <https://github.com/readthedocs/readthedocs.org/pull/3968>`_)
* `@xrmx <https://github.com/xrmx>`_: tests: fixup url tests in test_privacy_urls (`#3966 <https://github.com/readthedocs/readthedocs.org/pull/3966>`_)
* `@fenilgandhi <https://github.com/fenilgandhi>`_: Add support for different badge styles (`#3632 <https://github.com/readthedocs/readthedocs.org/pull/3632>`_)
* `@benjaoming <https://github.com/benjaoming>`_: Add Mexican Spanish as a project language (`#3588 <https://github.com/readthedocs/readthedocs.org/pull/3588>`_)
* `@stsewd <https://github.com/stsewd>`_: Wrap versions' list to look more consistent (`#3445 <https://github.com/readthedocs/readthedocs.org/pull/3445>`_)
* `@agjohnson <https://github.com/agjohnson>`_: Move CDN code to external abstraction (`#2091 <https://github.com/readthedocs/readthedocs.org/pull/2091>`_)

Version 2.4.0
-------------

:Date: May 31, 2018

* This fixes assets that were generated against old dependencies in 2.3.14
* `@agjohnson <https://github.com/agjohnson>`_: Fix issues with search javascript (`#4176 <https://github.com/readthedocs/readthedocs.org/pull/4176>`_)
* `@stsewd <https://github.com/stsewd>`_: Use anonymous refs in CHANGELOG (`#4173 <https://github.com/readthedocs/readthedocs.org/pull/4173>`_)
* `@stsewd <https://github.com/stsewd>`_: Fix some warnings on docs (`#4172 <https://github.com/readthedocs/readthedocs.org/pull/4172>`_)
* `@davidfischer <https://github.com/davidfischer>`_: Update the privacy policy date (`#4171 <https://github.com/readthedocs/readthedocs.org/pull/4171>`_)
* `@davidfischer <https://github.com/davidfischer>`_: Note about state and metro ad targeting (`#4169 <https://github.com/readthedocs/readthedocs.org/pull/4169>`_)
* `@ericholscher <https://github.com/ericholscher>`_: Add another guide around fixing memory usage. (`#4168 <https://github.com/readthedocs/readthedocs.org/pull/4168>`_)
* `@stsewd <https://github.com/stsewd>`_: Download raw build log (`#3585 <https://github.com/readthedocs/readthedocs.org/pull/3585>`_)
* `@stsewd <https://github.com/stsewd>`_: Add "edit" and "view docs" buttons to subproject list (`#3572 <https://github.com/readthedocs/readthedocs.org/pull/3572>`_)
* `@kennethlarsen <https://github.com/kennethlarsen>`_: Remove outline reset to bring back outline (`#3512 <https://github.com/readthedocs/readthedocs.org/pull/3512>`_)

Version 2.3.14
--------------

:Date: May 30, 2018

* `@ericholscher <https://github.com/ericholscher>`__: Remove CSS override that doesn't exist. (`#4165 <https://github.com/readthedocs/readthedocs.org/pull/4165>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Include a DMCA request template (`#4164 <https://github.com/readthedocs/readthedocs.org/pull/4164>`__)
* `@davidfischer <https://github.com/davidfischer>`__: No CSRF cookie for docs pages (`#4153 <https://github.com/readthedocs/readthedocs.org/pull/4153>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Small footer rework (`#4150 <https://github.com/readthedocs/readthedocs.org/pull/4150>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix prospector dependencies (`#4149 <https://github.com/readthedocs/readthedocs.org/pull/4149>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Remove deploy directory which is unused. (`#4147 <https://github.com/readthedocs/readthedocs.org/pull/4147>`__)
* `@stsewd <https://github.com/stsewd>`__: Use autosectionlabel extension (`#4146 <https://github.com/readthedocs/readthedocs.org/pull/4146>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Add Intercom to the privacy policy (`#4145 <https://github.com/readthedocs/readthedocs.org/pull/4145>`__)
* `@humitos <https://github.com/humitos>`__: Minimum refactor to decide_if_cors (`#4143 <https://github.com/readthedocs/readthedocs.org/pull/4143>`__)
* `@stsewd <https://github.com/stsewd>`__: Ignore migrations from coverage report (`#4141 <https://github.com/readthedocs/readthedocs.org/pull/4141>`__)
* `@stsewd <https://github.com/stsewd>`__: 5xx status in old webhooks (`#4139 <https://github.com/readthedocs/readthedocs.org/pull/4139>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Fix with Lato Bold font (`#4138 <https://github.com/readthedocs/readthedocs.org/pull/4138>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Release 2.3.13 (`#4137 <https://github.com/readthedocs/readthedocs.org/pull/4137>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Build static assets (`#4136 <https://github.com/readthedocs/readthedocs.org/pull/4136>`__)
* `@xrmx <https://github.com/xrmx>`__: oauth/services: correct error handling in paginate (`#4134 <https://github.com/readthedocs/readthedocs.org/pull/4134>`__)
* `@xrmx <https://github.com/xrmx>`__: oauth/services: don't abuse log.exception (`#4133 <https://github.com/readthedocs/readthedocs.org/pull/4133>`__)
* `@cedk <https://github.com/cedk>`__: Use quiet mode to retrieve branches from mercurial (`#4114 <https://github.com/readthedocs/readthedocs.org/pull/4114>`__)
* `@humitos <https://github.com/humitos>`__: Add `has_valid_clone` and `has_valid_webhook` to ProjectAdminSerializer (`#4107 <https://github.com/readthedocs/readthedocs.org/pull/4107>`__)
* `@stsewd <https://github.com/stsewd>`__: Put the rtd extension to the beginning of the list (`#4054 <https://github.com/readthedocs/readthedocs.org/pull/4054>`__)
* `@stsewd <https://github.com/stsewd>`__: Use gitpython for tags (`#4052 <https://github.com/readthedocs/readthedocs.org/pull/4052>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Do Not Track support (`#4046 <https://github.com/readthedocs/readthedocs.org/pull/4046>`__)
* `@stsewd <https://github.com/stsewd>`__: Set urlconf to None after changing SUBDOMAIN setting (`#4032 <https://github.com/readthedocs/readthedocs.org/pull/4032>`__)
* `@humitos <https://github.com/humitos>`__: Fix /404/ testing page (`#3976 <https://github.com/readthedocs/readthedocs.org/pull/3976>`__)
* `@xrmx <https://github.com/xrmx>`__: Fix some tests with postgres (`#3958 <https://github.com/readthedocs/readthedocs.org/pull/3958>`__)
* `@xrmx <https://github.com/xrmx>`__: Fixup DJANGO_SETTINGS_SKIP_LOCAL in tests (`#3899 <https://github.com/readthedocs/readthedocs.org/pull/3899>`__)
* `@xrmx <https://github.com/xrmx>`__: templates: mark a few more strings for translations (`#3869 <https://github.com/readthedocs/readthedocs.org/pull/3869>`__)
* `@ze <https://github.com/ze>`__: Make search bar in dashboard have a more clear message. (`#3844 <https://github.com/readthedocs/readthedocs.org/pull/3844>`__)
* `@varunotelli <https://github.com/varunotelli>`__: Pointed users to Python3.6 (`#3817 <https://github.com/readthedocs/readthedocs.org/pull/3817>`__)
* `@stsewd <https://github.com/stsewd>`__: [RDY] Fix tests for environment (`#3764 <https://github.com/readthedocs/readthedocs.org/pull/3764>`__)
* `@ajatprabha <https://github.com/ajatprabha>`__: Ticket #3694: rename owners to maintainers (`#3703 <https://github.com/readthedocs/readthedocs.org/pull/3703>`__)
* `@SanketDG <https://github.com/SanketDG>`__: Refactor to replace old logging to avoid mangling (`#3677 <https://github.com/readthedocs/readthedocs.org/pull/3677>`__)
* `@stsewd <https://github.com/stsewd>`__: Add rstcheck to CI (`#3624 <https://github.com/readthedocs/readthedocs.org/pull/3624>`__)
* `@techtonik <https://github.com/techtonik>`__: Update Git on prod (`#3615 <https://github.com/readthedocs/readthedocs.org/pull/3615>`__)
* `@stsewd <https://github.com/stsewd>`__: Allow to hide version warning (`#3595 <https://github.com/readthedocs/readthedocs.org/pull/3595>`__)
* `@cclauss <https://github.com/cclauss>`__: Modernize Python 2 code to get ready for Python 3 (`#3514 <https://github.com/readthedocs/readthedocs.org/pull/3514>`__)
* `@stsewd <https://github.com/stsewd>`__: Consistent version format (`#3504 <https://github.com/readthedocs/readthedocs.org/pull/3504>`__)

Version 2.3.13
--------------

:Date: May 23, 2018

* `@davidfischer <https://github.com/davidfischer>`__: Build static assets (`#4136 <https://github.com/readthedocs/readthedocs.org/pull/4136>`__)
* `@stsewd <https://github.com/stsewd>`__: Don't sync _static dir for search builder (`#4120 <https://github.com/readthedocs/readthedocs.org/pull/4120>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Use the latest Lato release (`#4093 <https://github.com/readthedocs/readthedocs.org/pull/4093>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Update Gold Member marketing (`#4063 <https://github.com/readthedocs/readthedocs.org/pull/4063>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Fix missing fonts (`#4060 <https://github.com/readthedocs/readthedocs.org/pull/4060>`__)
* `@stsewd <https://github.com/stsewd>`__: Additional validation when changing the project language (`#3790 <https://github.com/readthedocs/readthedocs.org/pull/3790>`__)
* `@stsewd <https://github.com/stsewd>`__: Improve yaml config docs (`#3685 <https://github.com/readthedocs/readthedocs.org/pull/3685>`__)

Version 2.3.12
--------------

:Date: May 21, 2018

* `@stsewd <https://github.com/stsewd>`__: Remove Django deprecation warning (`#4112 <https://github.com/readthedocs/readthedocs.org/pull/4112>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Display feature flags in the admin (`#4108 <https://github.com/readthedocs/readthedocs.org/pull/4108>`__)
* `@humitos <https://github.com/humitos>`__: Set valid clone in project instance inside the version object also (`#4105 <https://github.com/readthedocs/readthedocs.org/pull/4105>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Use the latest theme version in the default builder (`#4096 <https://github.com/readthedocs/readthedocs.org/pull/4096>`__)
* `@humitos <https://github.com/humitos>`__: Use next field to redirect user when login is done by social (`#4083 <https://github.com/readthedocs/readthedocs.org/pull/4083>`__)
* `@humitos <https://github.com/humitos>`__: Update the `documentation_type` when it's set to 'auto' (`#4080 <https://github.com/readthedocs/readthedocs.org/pull/4080>`__)
* `@brainwane <https://github.com/brainwane>`__: Update link to license in philosophy document (`#4059 <https://github.com/readthedocs/readthedocs.org/pull/4059>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Update local assets for theme to 0.3.1 tag (`#4047 <https://github.com/readthedocs/readthedocs.org/pull/4047>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix unbalanced div (`#4044 <https://github.com/readthedocs/readthedocs.org/pull/4044>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove haystack from code base (`#4039 <https://github.com/readthedocs/readthedocs.org/pull/4039>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Subdomains use HTTPS if settings specify (`#3987 <https://github.com/readthedocs/readthedocs.org/pull/3987>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Draft Privacy Policy (`#3978 <https://github.com/readthedocs/readthedocs.org/pull/3978>`__)
* `@humitos <https://github.com/humitos>`__: Allow import Gitlab repo manually and set a webhook automatically (`#3934 <https://github.com/readthedocs/readthedocs.org/pull/3934>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Enable ads on the readthedocs mkdocs theme (`#3922 <https://github.com/readthedocs/readthedocs.org/pull/3922>`__)
* `@bansalnitish <https://github.com/bansalnitish>`__: Fixes #2953 - Url resolved with special characters (`#3725 <https://github.com/readthedocs/readthedocs.org/pull/3725>`__)
* `@Jigar3 <https://github.com/Jigar3>`__: Deleted bookmarks app (`#3663 <https://github.com/readthedocs/readthedocs.org/pull/3663>`__)

Version 2.3.11
--------------

:Date: May 01, 2018

* `@agjohnson <https://github.com/agjohnson>`__: Update local assets for theme to 0.3.1 tag (`#4047 <https://github.com/readthedocs/readthedocs.org/pull/4047>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix unbalanced div (`#4044 <https://github.com/readthedocs/readthedocs.org/pull/4044>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove haystack from code base (`#4039 <https://github.com/readthedocs/readthedocs.org/pull/4039>`__)
* `@stsewd <https://github.com/stsewd>`__: Remove dead code from api v1 (`#4038 <https://github.com/readthedocs/readthedocs.org/pull/4038>`__)
* `@humitos <https://github.com/humitos>`__: Bump sphinx default version to 1.7.4 (`#4035 <https://github.com/readthedocs/readthedocs.org/pull/4035>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Detail where ads are shown (`#4031 <https://github.com/readthedocs/readthedocs.org/pull/4031>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Make email verification optional for dev (`#4024 <https://github.com/readthedocs/readthedocs.org/pull/4024>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Support sign in and sign up with GH/GL/BB (`#4022 <https://github.com/readthedocs/readthedocs.org/pull/4022>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Remove old varnish purge utility function (`#4019 <https://github.com/readthedocs/readthedocs.org/pull/4019>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Remove build queue length warning on build list page (`#4018 <https://github.com/readthedocs/readthedocs.org/pull/4018>`__)
* `@stsewd <https://github.com/stsewd>`__: Don't check order on assertQuerysetEqual on tests for subprojects (`#4016 <https://github.com/readthedocs/readthedocs.org/pull/4016>`__)
* `@stsewd <https://github.com/stsewd>`__: Tests for view docs api response (`#4014 <https://github.com/readthedocs/readthedocs.org/pull/4014>`__)
* `@davidfischer <https://github.com/davidfischer>`__: MkDocs projects use RTD's analytics privacy improvements (`#4013 <https://github.com/readthedocs/readthedocs.org/pull/4013>`__)
* `@humitos <https://github.com/humitos>`__: Release 2.3.10 (`#4009 <https://github.com/readthedocs/readthedocs.org/pull/4009>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Remove typekit fonts (`#3982 <https://github.com/readthedocs/readthedocs.org/pull/3982>`__)
* `@stsewd <https://github.com/stsewd>`__: Move dynamic-fixture to testing requirements (`#3956 <https://github.com/readthedocs/readthedocs.org/pull/3956>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix view docs link (`#3882 <https://github.com/readthedocs/readthedocs.org/pull/3882>`__)
* `@stsewd <https://github.com/stsewd>`__: [WIP] Remove comments app (`#3802 <https://github.com/readthedocs/readthedocs.org/pull/3802>`__)
* `@Jigar3 <https://github.com/Jigar3>`__: Deleted bookmarks app (`#3663 <https://github.com/readthedocs/readthedocs.org/pull/3663>`__)

Version 2.3.10
--------------

:Date: April 24, 2018

* `@humitos <https://github.com/humitos>`__: Downgrade docker to 3.1.3 (`#4003 <https://github.com/readthedocs/readthedocs.org/pull/4003>`__)

Version 2.3.9
-------------

:Date: April 20, 2018

* `@agjohnson <https://github.com/agjohnson>`__: Fix recursion problem more generally (`#3989 <https://github.com/readthedocs/readthedocs.org/pull/3989>`__)

Version 2.3.8
-------------

:Date: April 20, 2018

* `@agjohnson <https://github.com/agjohnson>`__: Give TaskStep class knowledge of the underlying task (`#3983 <https://github.com/readthedocs/readthedocs.org/pull/3983>`__)
* `@humitos <https://github.com/humitos>`__: Resolve domain when a project is a translation of itself (`#3981 <https://github.com/readthedocs/readthedocs.org/pull/3981>`__)

Version 2.3.7
-------------

:Date: April 19, 2018

* `@humitos <https://github.com/humitos>`__: Fix server_error_500 path on single version (`#3975 <https://github.com/readthedocs/readthedocs.org/pull/3975>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Fix bookmark app lint failures (`#3969 <https://github.com/readthedocs/readthedocs.org/pull/3969>`__)
* `@humitos <https://github.com/humitos>`__: Use latest setuptools (39.0.1) by default on build process (`#3967 <https://github.com/readthedocs/readthedocs.org/pull/3967>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Fix exact redirects. (`#3965 <https://github.com/readthedocs/readthedocs.org/pull/3965>`__)
* `@humitos <https://github.com/humitos>`__: Make `resolve_domain` work when a project is subproject of itself (`#3962 <https://github.com/readthedocs/readthedocs.org/pull/3962>`__)
* `@humitos <https://github.com/humitos>`__: Remove django-celery-beat and use the default scheduler (`#3959 <https://github.com/readthedocs/readthedocs.org/pull/3959>`__)
* `@xrmx <https://github.com/xrmx>`__: Fix some tests with postgres (`#3958 <https://github.com/readthedocs/readthedocs.org/pull/3958>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Add advertising details docs (`#3955 <https://github.com/readthedocs/readthedocs.org/pull/3955>`__)
* `@humitos <https://github.com/humitos>`__: Use pur to upgrade python packages (`#3953 <https://github.com/readthedocs/readthedocs.org/pull/3953>`__)
* `@ze <https://github.com/ze>`__: Make adjustments to Projects page (`#3948 <https://github.com/readthedocs/readthedocs.org/pull/3948>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Small change to Chinese language names (`#3947 <https://github.com/readthedocs/readthedocs.org/pull/3947>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Don't share state in build task (`#3946 <https://github.com/readthedocs/readthedocs.org/pull/3946>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Fixed footer ad width fix (`#3944 <https://github.com/readthedocs/readthedocs.org/pull/3944>`__)
* `@humitos <https://github.com/humitos>`__: Allow extend Translation and Subproject form logic from corporate (`#3937 <https://github.com/readthedocs/readthedocs.org/pull/3937>`__)
* `@humitos <https://github.com/humitos>`__: Resync valid webhook for project manually imported (`#3935 <https://github.com/readthedocs/readthedocs.org/pull/3935>`__)
* `@humitos <https://github.com/humitos>`__: Resync webhooks from Admin (`#3933 <https://github.com/readthedocs/readthedocs.org/pull/3933>`__)
* `@humitos <https://github.com/humitos>`__: Fix attribute order call (`#3930 <https://github.com/readthedocs/readthedocs.org/pull/3930>`__)
* `@humitos <https://github.com/humitos>`__: Mention RTD in the Project URL of the issue template (`#3928 <https://github.com/readthedocs/readthedocs.org/pull/3928>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Correctly report mkdocs theme name (`#3920 <https://github.com/readthedocs/readthedocs.org/pull/3920>`__)
* `@xrmx <https://github.com/xrmx>`__: Fixup DJANGO_SETTINGS_SKIP_LOCAL in tests (`#3899 <https://github.com/readthedocs/readthedocs.org/pull/3899>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Show an adblock admonition in the dev console (`#3894 <https://github.com/readthedocs/readthedocs.org/pull/3894>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix view docs link (`#3882 <https://github.com/readthedocs/readthedocs.org/pull/3882>`__)
* `@xrmx <https://github.com/xrmx>`__: templates: mark a few more strings for translations (`#3869 <https://github.com/readthedocs/readthedocs.org/pull/3869>`__)
* `@ze <https://github.com/ze>`__: Update quickstart from README (`#3847 <https://github.com/readthedocs/readthedocs.org/pull/3847>`__)
* `@vidartf <https://github.com/vidartf>`__: Fix page redirect preview (`#3811 <https://github.com/readthedocs/readthedocs.org/pull/3811>`__)
* `@stsewd <https://github.com/stsewd>`__: [RDY] Fix requirements file lookup (`#3800 <https://github.com/readthedocs/readthedocs.org/pull/3800>`__)
* `@aasis21 <https://github.com/aasis21>`__: Documentation for build notifications using webhooks. (`#3671 <https://github.com/readthedocs/readthedocs.org/pull/3671>`__)
* `@mashrikt <https://github.com/mashrikt>`__: [#2967] Scheduled tasks for cleaning up messages (`#3604 <https://github.com/readthedocs/readthedocs.org/pull/3604>`__)
* `@stsewd <https://github.com/stsewd>`__: Show URLS for exact redirect (`#3593 <https://github.com/readthedocs/readthedocs.org/pull/3593>`__)
* `@marcelstoer <https://github.com/marcelstoer>`__: Doc builder template should check for mkdocs_page_input_path before using it (`#3536 <https://github.com/readthedocs/readthedocs.org/pull/3536>`__)
* `@Code0x58 <https://github.com/Code0x58>`__: Document creation of slumber user (`#3461 <https://github.com/readthedocs/readthedocs.org/pull/3461>`__)

Version 2.3.6
-------------

:Date: April 05, 2018

* `@agjohnson <https://github.com/agjohnson>`__: Drop readthedocs- prefix to submodule (`#3916 <https://github.com/readthedocs/readthedocs.org/pull/3916>`__)
* `@agjohnson <https://github.com/agjohnson>`__: This fixes two bugs apparent in nesting of translations in subprojects (`#3909 <https://github.com/readthedocs/readthedocs.org/pull/3909>`__)
* `@humitos <https://github.com/humitos>`__: Use new django celery beat scheduler (`#3908 <https://github.com/readthedocs/readthedocs.org/pull/3908>`__)
* `@humitos <https://github.com/humitos>`__: Use a proper default for `docker` attribute on UpdateDocsTask (`#3907 <https://github.com/readthedocs/readthedocs.org/pull/3907>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Handle errors from publish_parts (`#3905 <https://github.com/readthedocs/readthedocs.org/pull/3905>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Drop pdbpp from testing requirements (`#3904 <https://github.com/readthedocs/readthedocs.org/pull/3904>`__)
* `@stsewd <https://github.com/stsewd>`__: Little improve on sync_versions (`#3902 <https://github.com/readthedocs/readthedocs.org/pull/3902>`__)
* `@humitos <https://github.com/humitos>`__: Save Docker image data in JSON file only for DockerBuildEnvironment (`#3897 <https://github.com/readthedocs/readthedocs.org/pull/3897>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Single analytics file for all builders (`#3896 <https://github.com/readthedocs/readthedocs.org/pull/3896>`__)
* `@humitos <https://github.com/humitos>`__: Organize logging levels (`#3893 <https://github.com/readthedocs/readthedocs.org/pull/3893>`__)

Version 2.3.5
-------------

:Date: April 05, 2018

* `@agjohnson <https://github.com/agjohnson>`__: Drop pdbpp from testing requirements (`#3904 <https://github.com/readthedocs/readthedocs.org/pull/3904>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Resolve subproject correctly in the case of single version (`#3901 <https://github.com/readthedocs/readthedocs.org/pull/3901>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Fixed footer ads again (`#3895 <https://github.com/readthedocs/readthedocs.org/pull/3895>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Fix an Alabaster ad positioning issue (`#3889 <https://github.com/readthedocs/readthedocs.org/pull/3889>`__)
* `@humitos <https://github.com/humitos>`__: Save Docker image hash in RTD environment.json file (`#3880 <https://github.com/readthedocs/readthedocs.org/pull/3880>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Add ref links for easier intersphinx on yaml config page (`#3877 <https://github.com/readthedocs/readthedocs.org/pull/3877>`__)
* `@rajujha373 <https://github.com/rajujha373>`__: Typo correction in docs/features.rst (`#3872 <https://github.com/readthedocs/readthedocs.org/pull/3872>`__)
* `@gaborbernat <https://github.com/gaborbernat>`__: add description for tox tasks (`#3868 <https://github.com/readthedocs/readthedocs.org/pull/3868>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Another CORS hotfix for the sustainability API (`#3862 <https://github.com/readthedocs/readthedocs.org/pull/3862>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Fix up some of the logic around repo and submodule URLs (`#3860 <https://github.com/readthedocs/readthedocs.org/pull/3860>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Fix linting errors in tests (`#3855 <https://github.com/readthedocs/readthedocs.org/pull/3855>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Use gitpython to find a commit reference (`#3843 <https://github.com/readthedocs/readthedocs.org/pull/3843>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Remove pinned CSS Select version (`#3813 <https://github.com/readthedocs/readthedocs.org/pull/3813>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Use JSONP for sustainability API (`#3789 <https://github.com/readthedocs/readthedocs.org/pull/3789>`__)
* `@rajujha373 <https://github.com/rajujha373>`__: #3718: Added date to changelog (`#3788 <https://github.com/readthedocs/readthedocs.org/pull/3788>`__)
* `@xrmx <https://github.com/xrmx>`__: tests: mock test_conf_file_not_found filesystem access (`#3740 <https://github.com/readthedocs/readthedocs.org/pull/3740>`__)

.. _version-2.3.4:

Version 2.3.4
-------------

* Release for static assets

Version 2.3.3
-------------

* `@davidfischer <https://github.com/davidfischer>`__: Fix linting errors in tests (`#3855 <https://github.com/readthedocs/readthedocs.org/pull/3855>`__)
* `@humitos <https://github.com/humitos>`__: Fix linting issues (`#3838 <https://github.com/readthedocs/readthedocs.org/pull/3838>`__)
* `@humitos <https://github.com/humitos>`__: Update instance and model when `record_as_success` (`#3831 <https://github.com/readthedocs/readthedocs.org/pull/3831>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Reorder GSOC projects, and note priority order (`#3823 <https://github.com/readthedocs/readthedocs.org/pull/3823>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Add temporary method for skipping submodule checkout (`#3821 <https://github.com/readthedocs/readthedocs.org/pull/3821>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Remove pinned CSS Select version (`#3813 <https://github.com/readthedocs/readthedocs.org/pull/3813>`__)
* `@humitos <https://github.com/humitos>`__: Use readthedocs-common to share linting files across different repos (`#3808 <https://github.com/readthedocs/readthedocs.org/pull/3808>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Use JSONP for sustainability API (`#3789 <https://github.com/readthedocs/readthedocs.org/pull/3789>`__)
* `@humitos <https://github.com/humitos>`__: Define useful celery beat task for development (`#3762 <https://github.com/readthedocs/readthedocs.org/pull/3762>`__)
* `@humitos <https://github.com/humitos>`__: Auto-generate conf.py compatible with Py2 and Py3 (`#3745 <https://github.com/readthedocs/readthedocs.org/pull/3745>`__)
* `@humitos <https://github.com/humitos>`__: Task to remove orphan symlinks (`#3543 <https://github.com/readthedocs/readthedocs.org/pull/3543>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix regex for public bitbucket repo (`#3533 <https://github.com/readthedocs/readthedocs.org/pull/3533>`__)
* `@humitos <https://github.com/humitos>`__: Documentation for RTD context sent to the Sphinx theme (`#3490 <https://github.com/readthedocs/readthedocs.org/pull/3490>`__)
* `@stsewd <https://github.com/stsewd>`__: Show link to docs on a build (`#3446 <https://github.com/readthedocs/readthedocs.org/pull/3446>`__)

Version 2.3.2
-------------

This version adds a hotfix branch that adds model validation to the repository
URL to ensure strange URL patterns can't be used.

Version 2.3.1
-------------

* `@humitos <https://github.com/humitos>`__: Update instance and model when `record_as_success` (`#3831 <https://github.com/readthedocs/readthedocs.org/pull/3831>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Bump docker -> 3.1.3 (`#3828 <https://github.com/readthedocs/readthedocs.org/pull/3828>`__)
* `@Doug-AWS <https://github.com/Doug-AWS>`__: Pip install note for Windows (`#3827 <https://github.com/readthedocs/readthedocs.org/pull/3827>`__)
* `@himanshutejwani12 <https://github.com/himanshutejwani12>`__: Update index.rst (`#3824 <https://github.com/readthedocs/readthedocs.org/pull/3824>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Reorder GSOC projects, and note priority order (`#3823 <https://github.com/readthedocs/readthedocs.org/pull/3823>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Autolint cleanup for #3821 (`#3822 <https://github.com/readthedocs/readthedocs.org/pull/3822>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Add temporary method for skipping submodule checkout (`#3821 <https://github.com/readthedocs/readthedocs.org/pull/3821>`__)
* `@stsewd <https://github.com/stsewd>`__: Pin astroid to fix linter issue on travis (`#3816 <https://github.com/readthedocs/readthedocs.org/pull/3816>`__)
* `@varunotelli <https://github.com/varunotelli>`__: Update install.rst dropped the Python 2.7 only part (`#3814 <https://github.com/readthedocs/readthedocs.org/pull/3814>`__)
* `@xrmx <https://github.com/xrmx>`__: Update machine field when activating a version from project_version_detail (`#3797 <https://github.com/readthedocs/readthedocs.org/pull/3797>`__)
* `@humitos <https://github.com/humitos>`__: Allow members of "Admin" Team to wipe version envs (`#3791 <https://github.com/readthedocs/readthedocs.org/pull/3791>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Add sustainability api to CORS (`#3782 <https://github.com/readthedocs/readthedocs.org/pull/3782>`__)
* `@durwasa-chakraborty <https://github.com/durwasa-chakraborty>`__: Fixed a grammatical error (`#3780 <https://github.com/readthedocs/readthedocs.org/pull/3780>`__)
* `@humitos <https://github.com/humitos>`__: Trying to solve the end line character for a font file (`#3776 <https://github.com/readthedocs/readthedocs.org/pull/3776>`__)
* `@stsewd <https://github.com/stsewd>`__: Fix tox env for coverage (`#3772 <https://github.com/readthedocs/readthedocs.org/pull/3772>`__)
* `@bansalnitish <https://github.com/bansalnitish>`__: Added eslint rules (`#3768 <https://github.com/readthedocs/readthedocs.org/pull/3768>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Use sustainability api for advertising (`#3747 <https://github.com/readthedocs/readthedocs.org/pull/3747>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Add a sustainability API (`#3672 <https://github.com/readthedocs/readthedocs.org/pull/3672>`__)
* `@humitos <https://github.com/humitos>`__: Upgrade django-pagination to a "maintained" fork (`#3666 <https://github.com/readthedocs/readthedocs.org/pull/3666>`__)
* `@humitos <https://github.com/humitos>`__: Project updated when subproject modified (`#3649 <https://github.com/readthedocs/readthedocs.org/pull/3649>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Anonymize IP addresses for Google Analytics (`#3626 <https://github.com/readthedocs/readthedocs.org/pull/3626>`__)
* `@humitos <https://github.com/humitos>`__: Improve "Sharing" docs (`#3472 <https://github.com/readthedocs/readthedocs.org/pull/3472>`__)
* `@humitos <https://github.com/humitos>`__: Upgrade docker-py to its latest version (docker==3.1.1) (`#3243 <https://github.com/readthedocs/readthedocs.org/pull/3243>`__)
* `@humitos <https://github.com/humitos>`__: Upgrade all packages using `pur` tool (`#2916 <https://github.com/readthedocs/readthedocs.org/pull/2916>`__)
* `@rixx <https://github.com/rixx>`__: Fix page redirect preview (`#2711 <https://github.com/readthedocs/readthedocs.org/pull/2711>`__)

Version 2.3.0
-------------

.. warning::
    Version 2.3.0 includes a security fix for project translations. See
    :ref:`security:Release 2.3.0` for more information

* `@stsewd <https://github.com/stsewd>`__: Fix tox env for coverage (`#3772 <https://github.com/readthedocs/readthedocs.org/pull/3772>`__)
* `@humitos <https://github.com/humitos>`__: Try to fix end of file (`#3761 <https://github.com/readthedocs/readthedocs.org/pull/3761>`__)
* `@berkerpeksag <https://github.com/berkerpeksag>`__: Fix indentation in docs/faq.rst (`#3758 <https://github.com/readthedocs/readthedocs.org/pull/3758>`__)
* `@stsewd <https://github.com/stsewd>`__: Check for http protocol before urlize (`#3755 <https://github.com/readthedocs/readthedocs.org/pull/3755>`__)
* `@rajujha373 <https://github.com/rajujha373>`__: #3741: replaced Go Crazy text with Search (`#3752 <https://github.com/readthedocs/readthedocs.org/pull/3752>`__)
* `@humitos <https://github.com/humitos>`__: Log in the proper place and add the image name used (`#3750 <https://github.com/readthedocs/readthedocs.org/pull/3750>`__)
* `@shubham76 <https://github.com/shubham76>`__: Changed 'Submit' text on buttons with something more meaningful (`#3749 <https://github.com/readthedocs/readthedocs.org/pull/3749>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Fix tests for Git submodule (`#3737 <https://github.com/readthedocs/readthedocs.org/pull/3737>`__)
* `@bansalnitish <https://github.com/bansalnitish>`__: Add eslint rules and fix errors (`#3726 <https://github.com/readthedocs/readthedocs.org/pull/3726>`__)
* `@davidfischer <https://github.com/davidfischer>`__: Prevent bots indexing promos (`#3719 <https://github.com/readthedocs/readthedocs.org/pull/3719>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Add argument to skip errorlist through knockout on common form (`#3704 <https://github.com/readthedocs/readthedocs.org/pull/3704>`__)
* `@ajatprabha <https://github.com/ajatprabha>`__: Fixed #3701: added closing tag for div element (`#3702 <https://github.com/readthedocs/readthedocs.org/pull/3702>`__)
* `@bansalnitish <https://github.com/bansalnitish>`__: Fixes internal reference (`#3695 <https://github.com/readthedocs/readthedocs.org/pull/3695>`__)
* `@humitos <https://github.com/humitos>`__: Always record the git branch command as success (`#3693 <https://github.com/readthedocs/readthedocs.org/pull/3693>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Show the project slug in the project admin (to make it more explicit what project is what) (`#3681 <https://github.com/readthedocs/readthedocs.org/pull/3681>`__)
* `@humitos <https://github.com/humitos>`__: Upgrade django-taggit to 0.22.2 (`#3667 <https://github.com/readthedocs/readthedocs.org/pull/3667>`__)
* `@stsewd <https://github.com/stsewd>`__: Check for submodules (`#3661 <https://github.com/readthedocs/readthedocs.org/pull/3661>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Hotfix for adding logging call back into project sync task (`#3657 <https://github.com/readthedocs/readthedocs.org/pull/3657>`__)
* `@agjohnson <https://github.com/agjohnson>`__: Fix issue with missing setting in oauth SyncRepo task (`#3656 <https://github.com/readthedocs/readthedocs.org/pull/3656>`__)
* `@ericholscher <https://github.com/ericholscher>`__: Remove error logging that isn't an error. (`#3650 <https://github.com/readthedocs/readthedocs.org/pull/3650>`__)
* `@humitos <https://github.com/humitos>`__: Project updated when subproject modified (`#3649 <https://github.com/readthedocs/readthedocs.org/pull/3649>`__)
* `@aasis21 <https://github.com/aasis21>`__: formatting buttons in edit project text editor (`#3633 <https://github.com/readthedocs/readthedocs.org/pull/3633>`__)
* `@humitos <https://github.com/humitos>`__: Filter by my own repositories at Import Remote Project (`#3548 <https://github.com/readthedocs/readthedocs.org/pull/3548>`__)
* `@funkyHat <https://github.com/funkyHat>`__: check for matching alias before subproject slug (`#2787 <https://github.com/readthedocs/readthedocs.org/pull/2787>`__)

Version 2.2.1
-------------

Version ``2.2.1`` is a bug fix release for the several issues found in
production during the ``2.2.0`` release.

 * `@agjohnson <https://github.com/agjohnson>`__: Hotfix for adding logging call back into project sync task (`#3657 <https://github.com/readthedocs/readthedocs.org/pull/3657>`__)
 * `@agjohnson <https://github.com/agjohnson>`__: Fix issue with missing setting in oauth SyncRepo task (`#3656 <https://github.com/readthedocs/readthedocs.org/pull/3656>`__)
 * `@humitos <https://github.com/humitos>`__: Tests for build notifications (`#3654 <https://github.com/readthedocs/readthedocs.org/pull/3654>`__)
 * `@humitos <https://github.com/humitos>`__: Send proper context to celery email notification task (`#3653 <https://github.com/readthedocs/readthedocs.org/pull/3653>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Remove error logging that isn't an error. (`#3650 <https://github.com/readthedocs/readthedocs.org/pull/3650>`__)
 * `@davidfischer <https://github.com/davidfischer>`__: Update RTD security docs (`#3641 <https://github.com/readthedocs/readthedocs.org/pull/3641>`__)
 * `@humitos <https://github.com/humitos>`__: Ability to override the creation of the Celery App (`#3623 <https://github.com/readthedocs/readthedocs.org/pull/3623>`__)

Version 2.2.0
-------------

 * `@humitos <https://github.com/humitos>`__: Tests for build notifications (`#3654 <https://github.com/readthedocs/readthedocs.org/pull/3654>`__)
 * `@humitos <https://github.com/humitos>`__: Send proper context to celery email notification task (`#3653 <https://github.com/readthedocs/readthedocs.org/pull/3653>`__)
 * `@xrmx <https://github.com/xrmx>`__: Update django-formtools to 2.1 (`#3648 <https://github.com/readthedocs/readthedocs.org/pull/3648>`__)
 * `@xrmx <https://github.com/xrmx>`__: Update Django to 1.9.13 (`#3647 <https://github.com/readthedocs/readthedocs.org/pull/3647>`__)
 * `@davidfischer <https://github.com/davidfischer>`__: Fix a 500 when searching for files with API v1 (`#3645 <https://github.com/readthedocs/readthedocs.org/pull/3645>`__)
 * `@davidfischer <https://github.com/davidfischer>`__: Update RTD security docs (`#3641 <https://github.com/readthedocs/readthedocs.org/pull/3641>`__)
 * `@humitos <https://github.com/humitos>`__: Fix SVN initialization for command logging (`#3638 <https://github.com/readthedocs/readthedocs.org/pull/3638>`__)
 * `@humitos <https://github.com/humitos>`__: Ability to override the creation of the Celery App (`#3623 <https://github.com/readthedocs/readthedocs.org/pull/3623>`__)
 * `@humitos <https://github.com/humitos>`__: Update the operations team (`#3621 <https://github.com/readthedocs/readthedocs.org/pull/3621>`__)
 * `@mohitkyadav <https://github.com/mohitkyadav>`__: Add venv to .gitignore (`#3620 <https://github.com/readthedocs/readthedocs.org/pull/3620>`__)
 * `@stsewd <https://github.com/stsewd>`__: Remove hardcoded copyright year (`#3616 <https://github.com/readthedocs/readthedocs.org/pull/3616>`__)
 * `@stsewd <https://github.com/stsewd>`__: Improve installation steps (`#3614 <https://github.com/readthedocs/readthedocs.org/pull/3614>`__)
 * `@stsewd <https://github.com/stsewd>`__: Update GSOC (`#3607 <https://github.com/readthedocs/readthedocs.org/pull/3607>`__)
 * `@Jigar3 <https://github.com/Jigar3>`__: Updated AUTHORS.rst (`#3601 <https://github.com/readthedocs/readthedocs.org/pull/3601>`__)
 * `@stsewd <https://github.com/stsewd>`__: Pin less to latest compatible version (`#3597 <https://github.com/readthedocs/readthedocs.org/pull/3597>`__)
 * ``@Angeles4four``: Grammar correction (`#3596 <https://github.com/readthedocs/readthedocs.org/pull/3596>`__)
 * `@davidfischer <https://github.com/davidfischer>`__: Fix an unclosed tag (`#3592 <https://github.com/readthedocs/readthedocs.org/pull/3592>`__)
 * `@aaksarin <https://github.com/aaksarin>`__: add missed fontawesome-webfont.woff2 (`#3589 <https://github.com/readthedocs/readthedocs.org/pull/3589>`__)
 * `@davidfischer <https://github.com/davidfischer>`__: Force a specific ad to be displayed (`#3584 <https://github.com/readthedocs/readthedocs.org/pull/3584>`__)
 * `@stsewd <https://github.com/stsewd>`__: Docs about preference for tags over branches (`#3582 <https://github.com/readthedocs/readthedocs.org/pull/3582>`__)
 * `@davidfischer <https://github.com/davidfischer>`__: Rework homepage (`#3579 <https://github.com/readthedocs/readthedocs.org/pull/3579>`__)
 * `@stsewd <https://github.com/stsewd>`__: Don't allow to create a subproject of a project itself  (`#3571 <https://github.com/readthedocs/readthedocs.org/pull/3571>`__)
 * `@davidfischer <https://github.com/davidfischer>`__: Fix for build screen in firefox (`#3569 <https://github.com/readthedocs/readthedocs.org/pull/3569>`__)
 * `@humitos <https://github.com/humitos>`__: Style using pre-commit (`#3560 <https://github.com/readthedocs/readthedocs.org/pull/3560>`__)
 * `@humitos <https://github.com/humitos>`__: Use DRF 3.1 `pagination_class` (`#3559 <https://github.com/readthedocs/readthedocs.org/pull/3559>`__)
 * `@davidfischer <https://github.com/davidfischer>`__: Analytics fixes (`#3558 <https://github.com/readthedocs/readthedocs.org/pull/3558>`__)
 * `@davidfischer <https://github.com/davidfischer>`__: Upgrade requests version (`#3557 <https://github.com/readthedocs/readthedocs.org/pull/3557>`__)
 * `@humitos <https://github.com/humitos>`__: Mount `pip_cache_path` in Docker container (`#3556 <https://github.com/readthedocs/readthedocs.org/pull/3556>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Add a number of new ideas for GSOC (`#3552 <https://github.com/readthedocs/readthedocs.org/pull/3552>`__)
 * `@humitos <https://github.com/humitos>`__: Fix Travis lint issue (`#3551 <https://github.com/readthedocs/readthedocs.org/pull/3551>`__)
 * `@davidfischer <https://github.com/davidfischer>`__: Send custom dimensions for mkdocs (`#3550 <https://github.com/readthedocs/readthedocs.org/pull/3550>`__)
 * `@davidfischer <https://github.com/davidfischer>`__: Promo contrast improvements (`#3549 <https://github.com/readthedocs/readthedocs.org/pull/3549>`__)
 * `@humitos <https://github.com/humitos>`__: Allow git tags with `/` in the name and properly slugify (`#3545 <https://github.com/readthedocs/readthedocs.org/pull/3545>`__)
 * `@humitos <https://github.com/humitos>`__: Allow to import public repositories on corporate site (`#3537 <https://github.com/readthedocs/readthedocs.org/pull/3537>`__)
 * `@humitos <https://github.com/humitos>`__: Log `git checkout` and expose to users (`#3520 <https://github.com/readthedocs/readthedocs.org/pull/3520>`__)
 * `@stsewd <https://github.com/stsewd>`__: Update docs (`#3498 <https://github.com/readthedocs/readthedocs.org/pull/3498>`__)
 * `@davidfischer <https://github.com/davidfischer>`__: Switch to universal analytics (`#3495 <https://github.com/readthedocs/readthedocs.org/pull/3495>`__)
 * `@stsewd <https://github.com/stsewd>`__: Move Mercurial dependency to pip.txt (`#3488 <https://github.com/readthedocs/readthedocs.org/pull/3488>`__)
 * `@agjohnson <https://github.com/agjohnson>`__: Add docs on removing edit button (`#3479 <https://github.com/readthedocs/readthedocs.org/pull/3479>`__)
 * `@davidfischer <https://github.com/davidfischer>`__: Convert default dev cache to local memory (`#3477 <https://github.com/readthedocs/readthedocs.org/pull/3477>`__)
 * `@agjohnson <https://github.com/agjohnson>`__: Fix lint error (`#3402 <https://github.com/readthedocs/readthedocs.org/pull/3402>`__)
 * `@techtonik <https://github.com/techtonik>`__: Fix Edit links if version is referenced by annotated tag (`#3302 <https://github.com/readthedocs/readthedocs.org/pull/3302>`__)
 * `@jaraco <https://github.com/jaraco>`__: Fixed build results page on firefox (part two) (`#2630 <https://github.com/readthedocs/readthedocs.org/pull/2630>`__)

Version 2.1.6
-------------

 * `@davidfischer <https://github.com/davidfischer>`__: Promo contrast improvements (`#3549 <https://github.com/readthedocs/readthedocs.org/pull/3549>`__)
 * `@humitos <https://github.com/humitos>`__: Refactor run command outside a Build and Environment (`#3542 <https://github.com/readthedocs/readthedocs.org/issues/3542>`__)
 * `@AnatoliyURL <https://github.com/AnatoliyURL>`__: Project in the local read the docs don't see tags. (`#3534 <https://github.com/readthedocs/readthedocs.org/issues/3534>`__)
 * `@malarzm <https://github.com/malarzm>`__: searchtools.js missing init() call (`#3532 <https://github.com/readthedocs/readthedocs.org/issues/3532>`__)
 * `@johanneskoester <https://github.com/johanneskoester>`__: Build failed without details (`#3531 <https://github.com/readthedocs/readthedocs.org/issues/3531>`__)
 * `@danielmitterdorfer <https://github.com/danielmitterdorfer>`__: "Edit on Github" points to non-existing commit (`#3530 <https://github.com/readthedocs/readthedocs.org/issues/3530>`__)
 * `@lk-geimfari <https://github.com/lk-geimfari>`__: No such file or directory: 'docs/requirements.txt' (`#3529 <https://github.com/readthedocs/readthedocs.org/issues/3529>`__)
 * `@stsewd <https://github.com/stsewd>`__: Fix Good First Issue link (`#3522 <https://github.com/readthedocs/readthedocs.org/pull/3522>`__)
 * `@Blendify <https://github.com/Blendify>`__: Remove RTD Theme workaround (`#3519 <https://github.com/readthedocs/readthedocs.org/pull/3519>`__)
 * `@stsewd <https://github.com/stsewd>`__: Move project description to the top (`#3510 <https://github.com/readthedocs/readthedocs.org/pull/3510>`__)
 * `@davidfischer <https://github.com/davidfischer>`__: Switch to universal analytics (`#3495 <https://github.com/readthedocs/readthedocs.org/pull/3495>`__)
 * `@davidfischer <https://github.com/davidfischer>`__: Convert default dev cache to local memory (`#3477 <https://github.com/readthedocs/readthedocs.org/pull/3477>`__)
 * `@nlgranger <https://github.com/nlgranger>`__: Github service: cannot unlink after deleting account (`#3374 <https://github.com/readthedocs/readthedocs.org/issues/3374>`__)
 * `@andrewgodwin <https://github.com/andrewgodwin>`__: "stable" appearing to track future release branches (`#3268 <https://github.com/readthedocs/readthedocs.org/issues/3268>`__)
 * `@skddc <https://github.com/skddc>`__: Add JSDoc to docs build environment (`#3069 <https://github.com/readthedocs/readthedocs.org/issues/3069>`__)
 * `@chummels <https://github.com/chummels>`__: RTD building old "stable" docs instead of "latest" when auto-triggered from recent push (`#2351 <https://github.com/readthedocs/readthedocs.org/issues/2351>`__)
 * `@cajus <https://github.com/cajus>`__: Builds get stuck in "Cloning" state (`#2047 <https://github.com/readthedocs/readthedocs.org/issues/2047>`__)
 * `@gossi <https://github.com/gossi>`__: Cannot delete subproject (`#1341 <https://github.com/readthedocs/readthedocs.org/issues/1341>`__)
 * `@gigster99 <https://github.com/gigster99>`__: extension problem (`#1059 <https://github.com/readthedocs/readthedocs.org/issues/1059>`__)

Version 2.1.5
-------------

 * `@ericholscher <https://github.com/ericholscher>`__: Add GSOC 2018 page (`#3518 <https://github.com/readthedocs/readthedocs.org/pull/3518>`__)
 * `@stsewd <https://github.com/stsewd>`__: Move project description to the top (`#3510 <https://github.com/readthedocs/readthedocs.org/pull/3510>`__)
 * `@RichardLitt <https://github.com/RichardLitt>`__: Docs: Rename "Good First Bug" to "Good First Issue" (`#3505 <https://github.com/readthedocs/readthedocs.org/pull/3505>`__)
 * `@stsewd <https://github.com/stsewd>`__: Fix regex for getting project and user (`#3501 <https://github.com/readthedocs/readthedocs.org/pull/3501>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Check to make sure changes exist in Bitbucket pushes (`#3480 <https://github.com/readthedocs/readthedocs.org/pull/3480>`__)
 * `@andrewgodwin <https://github.com/andrewgodwin>`__: "stable" appearing to track future release branches (`#3268 <https://github.com/readthedocs/readthedocs.org/issues/3268>`__)
 * `@cdeil <https://github.com/cdeil>`__: No module named pip in conda build (`#2827 <https://github.com/readthedocs/readthedocs.org/issues/2827>`__)
 * `@Yaseenh <https://github.com/Yaseenh>`__: building project does not generate new pdf with changes in it (`#2758 <https://github.com/readthedocs/readthedocs.org/issues/2758>`__)
 * `@chummels <https://github.com/chummels>`__: RTD building old "stable" docs instead of "latest" when auto-triggered from recent push (`#2351 <https://github.com/readthedocs/readthedocs.org/issues/2351>`__)
 * `@KeithWoods <https://github.com/KeithWoods>`__: GitHub edit link is aggressively stripped (`#1788 <https://github.com/readthedocs/readthedocs.org/issues/1788>`__)

Version 2.1.4
-------------

 * `@davidfischer <https://github.com/davidfischer>`__: Add programming language to API/READTHEDOCS_DATA (`#3499 <https://github.com/readthedocs/readthedocs.org/pull/3499>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Remove our mkdocs search override (`#3496 <https://github.com/readthedocs/readthedocs.org/pull/3496>`__)
 * `@humitos <https://github.com/humitos>`__: Better style (`#3494 <https://github.com/readthedocs/readthedocs.org/pull/3494>`__)
 * `@humitos <https://github.com/humitos>`__: Update README.rst (`#3492 <https://github.com/readthedocs/readthedocs.org/pull/3492>`__)
 * `@davidfischer <https://github.com/davidfischer>`__: Small formatting change to the Alabaster footer (`#3491 <https://github.com/readthedocs/readthedocs.org/pull/3491>`__)
 * `@matsen <https://github.com/matsen>`__: Fixing "resetting" misspelling. (`#3487 <https://github.com/readthedocs/readthedocs.org/pull/3487>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Add David to dev team listing (`#3485 <https://github.com/readthedocs/readthedocs.org/pull/3485>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Check to make sure changes exist in Bitbucket pushes (`#3480 <https://github.com/readthedocs/readthedocs.org/pull/3480>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Use semvar for readthedocs-build to make bumping easier (`#3475 <https://github.com/readthedocs/readthedocs.org/pull/3475>`__)
 * `@davidfischer <https://github.com/davidfischer>`__: Add programming languages (`#3471 <https://github.com/readthedocs/readthedocs.org/pull/3471>`__)
 * `@humitos <https://github.com/humitos>`__: Remove TEMPLATE_LOADERS since it's the default (`#3469 <https://github.com/readthedocs/readthedocs.org/pull/3469>`__)
 * `@Code0x58 <https://github.com/Code0x58>`__: Minor virtualenv upgrade (`#3463 <https://github.com/readthedocs/readthedocs.org/pull/3463>`__)
 * `@humitos <https://github.com/humitos>`__: Remove invite only message (`#3456 <https://github.com/readthedocs/readthedocs.org/pull/3456>`__)
 * `@maxirus <https://github.com/maxirus>`__: Adding to Install Docs (`#3455 <https://github.com/readthedocs/readthedocs.org/pull/3455>`__)
 * `@stsewd <https://github.com/stsewd>`__: Fix a little typo (`#3448 <https://github.com/readthedocs/readthedocs.org/pull/3448>`__)
 * `@stsewd <https://github.com/stsewd>`__: Better autogenerated index file (`#3447 <https://github.com/readthedocs/readthedocs.org/pull/3447>`__)
 * `@stsewd <https://github.com/stsewd>`__: Better help text for privacy level (`#3444 <https://github.com/readthedocs/readthedocs.org/pull/3444>`__)
 * `@msyriac <https://github.com/msyriac>`__: Broken link URL changed fixes #3442 (`#3443 <https://github.com/readthedocs/readthedocs.org/pull/3443>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Fix git (`#3441 <https://github.com/readthedocs/readthedocs.org/pull/3441>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Properly slugify the alias on Project Relationships. (`#3440 <https://github.com/readthedocs/readthedocs.org/pull/3440>`__)
 * `@stsewd <https://github.com/stsewd>`__: Don't show "build ideas" to unprivileged users (`#3439 <https://github.com/readthedocs/readthedocs.org/pull/3439>`__)
 * `@Blendify <https://github.com/Blendify>`__: Docs: Point Theme docs to new website (`#3438 <https://github.com/readthedocs/readthedocs.org/pull/3438>`__)
 * `@humitos <https://github.com/humitos>`__: Do not use double quotes on git command with --format option (`#3437 <https://github.com/readthedocs/readthedocs.org/pull/3437>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Hack in a fix for missing version slug deploy that went out a while back (`#3433 <https://github.com/readthedocs/readthedocs.org/pull/3433>`__)
 * `@humitos <https://github.com/humitos>`__: Check versions used to create the venv and auto-wipe (`#3432 <https://github.com/readthedocs/readthedocs.org/pull/3432>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Upgrade psycopg2 (`#3429 <https://github.com/readthedocs/readthedocs.org/pull/3429>`__)
 * `@humitos <https://github.com/humitos>`__: Fix "Edit in Github" link (`#3427 <https://github.com/readthedocs/readthedocs.org/pull/3427>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Add celery theme to supported ad options (`#3425 <https://github.com/readthedocs/readthedocs.org/pull/3425>`__)
 * `@humitos <https://github.com/humitos>`__: Link to version detail page from build detail page (`#3418 <https://github.com/readthedocs/readthedocs.org/pull/3418>`__)
 * `@humitos <https://github.com/humitos>`__: Move wipe button to version detail page (`#3417 <https://github.com/readthedocs/readthedocs.org/pull/3417>`__)
 * `@humitos <https://github.com/humitos>`__: Show/Hide "See paid advertising" checkbox depending on USE_PROMOS (`#3412 <https://github.com/readthedocs/readthedocs.org/pull/3412>`__)
 * `@benjaoming <https://github.com/benjaoming>`__: Strip well-known version component origin/ from remote version (`#3377 <https://github.com/readthedocs/readthedocs.org/pull/3377>`__)
 * `@humitos <https://github.com/humitos>`__: Remove warnings from code (`#3372 <https://github.com/readthedocs/readthedocs.org/pull/3372>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Add docker image from the YAML config integration (`#3339 <https://github.com/readthedocs/readthedocs.org/pull/3339>`__)
 * `@humitos <https://github.com/humitos>`__: Show proper error to user when conf.py is not found (`#3326 <https://github.com/readthedocs/readthedocs.org/pull/3326>`__)
 * `@humitos <https://github.com/humitos>`__: Simple task to finish inactive builds (`#3312 <https://github.com/readthedocs/readthedocs.org/pull/3312>`__)
 * `@techtonik <https://github.com/techtonik>`__: Fix Edit links if version is referenced by annotated tag (`#3302 <https://github.com/readthedocs/readthedocs.org/pull/3302>`__)
 * `@Riyuzakii <https://github.com/Riyuzakii>`__: changed <strong> from html to css (`#2699 <https://github.com/readthedocs/readthedocs.org/pull/2699>`__)

Version 2.1.3
-------------

:date: Dec 21, 2017

 * `@ericholscher <https://github.com/ericholscher>`__: Upgrade psycopg2 (`#3429 <https://github.com/readthedocs/readthedocs.org/pull/3429>`__)
 * `@humitos <https://github.com/humitos>`__: Fix "Edit in Github" link (`#3427 <https://github.com/readthedocs/readthedocs.org/pull/3427>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Add celery theme to supported ad options (`#3425 <https://github.com/readthedocs/readthedocs.org/pull/3425>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Only build travis push builds on master. (`#3421 <https://github.com/readthedocs/readthedocs.org/pull/3421>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Add concept of dashboard analytics code (`#3420 <https://github.com/readthedocs/readthedocs.org/pull/3420>`__)
 * `@humitos <https://github.com/humitos>`__: Use default avatar for User/Orgs in OAuth services (`#3419 <https://github.com/readthedocs/readthedocs.org/pull/3419>`__)
 * `@humitos <https://github.com/humitos>`__: Link to version detail page from build detail page (`#3418 <https://github.com/readthedocs/readthedocs.org/pull/3418>`__)
 * `@humitos <https://github.com/humitos>`__: Move wipe button to version detail page (`#3417 <https://github.com/readthedocs/readthedocs.org/pull/3417>`__)
 * `@bieagrathara <https://github.com/bieagrathara>`__: 019 497 8360 (`#3416 <https://github.com/readthedocs/readthedocs.org/issues/3416>`__)
 * `@bieagrathara <https://github.com/bieagrathara>`__: rew (`#3415 <https://github.com/readthedocs/readthedocs.org/issues/3415>`__)
 * `@tony <https://github.com/tony>`__: lint prospector task failing (`#3414 <https://github.com/readthedocs/readthedocs.org/issues/3414>`__)
 * `@humitos <https://github.com/humitos>`__: Remove extra 's' (`#3413 <https://github.com/readthedocs/readthedocs.org/pull/3413>`__)
 * `@humitos <https://github.com/humitos>`__: Show/Hide "See paid advertising" checkbox depending on USE_PROMOS (`#3412 <https://github.com/readthedocs/readthedocs.org/pull/3412>`__)
 * `@accraze <https://github.com/accraze>`__: Removing talks about RTD page (`#3410 <https://github.com/readthedocs/readthedocs.org/pull/3410>`__)
 * `@humitos <https://github.com/humitos>`__: Pin pylint to 1.7.5 and fix docstring styling (`#3408 <https://github.com/readthedocs/readthedocs.org/pull/3408>`__)
 * `@agjohnson <https://github.com/agjohnson>`__: Update style and copy on abandonment docs (`#3406 <https://github.com/readthedocs/readthedocs.org/pull/3406>`__)
 * `@agjohnson <https://github.com/agjohnson>`__: Update changelog more consistently (`#3405 <https://github.com/readthedocs/readthedocs.org/pull/3405>`__)
 * `@agjohnson <https://github.com/agjohnson>`__: Update prerelease invoke command to call with explicit path (`#3404 <https://github.com/readthedocs/readthedocs.org/pull/3404>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Fix changelog command (`#3403 <https://github.com/readthedocs/readthedocs.org/pull/3403>`__)
 * `@agjohnson <https://github.com/agjohnson>`__: Fix lint error (`#3402 <https://github.com/readthedocs/readthedocs.org/pull/3402>`__)
 * `@julienmalard <https://github.com/julienmalard>`__: Recent builds are missing translated languages links (`#3401 <https://github.com/readthedocs/readthedocs.org/issues/3401>`__)
 * `@stsewd <https://github.com/stsewd>`__: Remove copyright application (`#3400 <https://github.com/readthedocs/readthedocs.org/pull/3400>`__)
 * `@humitos <https://github.com/humitos>`__: Show connect buttons for installed apps only (`#3394 <https://github.com/readthedocs/readthedocs.org/pull/3394>`__)
 * `@agjohnson <https://github.com/agjohnson>`__: Fix display of build advice (`#3390 <https://github.com/readthedocs/readthedocs.org/issues/3390>`__)
 * `@agjohnson <https://github.com/agjohnson>`__: Don't display the build suggestions div if there are no suggestions (`#3389 <https://github.com/readthedocs/readthedocs.org/pull/3389>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Pass more data into the redirects. (`#3388 <https://github.com/readthedocs/readthedocs.org/pull/3388>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Fix issue where you couldn't edit your canonical domain. (`#3387 <https://github.com/readthedocs/readthedocs.org/pull/3387>`__)
 * `@benjaoming <https://github.com/benjaoming>`__: Strip well-known version component origin/ from remote version (`#3377 <https://github.com/readthedocs/readthedocs.org/pull/3377>`__)
 * `@humitos <https://github.com/humitos>`__: Remove warnings from code (`#3372 <https://github.com/readthedocs/readthedocs.org/pull/3372>`__)
 * `@JavaDevVictoria <https://github.com/JavaDevVictoria>`__: Updated python.setup_py_install to be true (`#3357 <https://github.com/readthedocs/readthedocs.org/pull/3357>`__)
 * `@humitos <https://github.com/humitos>`__: Use default avatars for GitLab/GitHub/Bitbucket integrations (users/organizations) (`#3353 <https://github.com/readthedocs/readthedocs.org/issues/3353>`__)
 * `@jonrkarr <https://github.com/jonrkarr>`__: Error in YAML configuration docs: default value for `python.setup_py_install` should be `true` (`#3334 <https://github.com/readthedocs/readthedocs.org/issues/3334>`__)
 * `@humitos <https://github.com/humitos>`__: Show proper error to user when conf.py is not found (`#3326 <https://github.com/readthedocs/readthedocs.org/pull/3326>`__)
 * `@MikeHart85 <https://github.com/MikeHart85>`__: Badges aren't updating due to being cached on GitHub. (`#3323 <https://github.com/readthedocs/readthedocs.org/issues/3323>`__)
 * `@humitos <https://github.com/humitos>`__: Simple task to finish inactive builds (`#3312 <https://github.com/readthedocs/readthedocs.org/pull/3312>`__)
 * `@techtonik <https://github.com/techtonik>`__: Fix Edit links if version is referenced by annotated tag (`#3302 <https://github.com/readthedocs/readthedocs.org/pull/3302>`__)
 * `@humitos <https://github.com/humitos>`__: Remove/Update talks about RTD page (`#3283 <https://github.com/readthedocs/readthedocs.org/issues/3283>`__)
 * `@gawel <https://github.com/gawel>`__: Regain pyquery project ownership (`#3281 <https://github.com/readthedocs/readthedocs.org/issues/3281>`__)
 * `@dialex <https://github.com/dialex>`__: Build passed but I can't see the documentation (maze screen) (`#3246 <https://github.com/readthedocs/readthedocs.org/issues/3246>`__)
 * ``@makixx``: Account is inactive (`#3241 <https://github.com/readthedocs/readthedocs.org/issues/3241>`__)
 * `@agjohnson <https://github.com/agjohnson>`__: Cleanup misreported failed builds (`#3230 <https://github.com/readthedocs/readthedocs.org/issues/3230>`__)
 * `@cokelaer <https://github.com/cokelaer>`__: links to github are broken (`#3203 <https://github.com/readthedocs/readthedocs.org/issues/3203>`__)
 * `@agjohnson <https://github.com/agjohnson>`__: Remove copyright application (`#3199 <https://github.com/readthedocs/readthedocs.org/issues/3199>`__)
 * `@shacharoo <https://github.com/shacharoo>`__: Unable to register after deleting my account (`#3189 <https://github.com/readthedocs/readthedocs.org/issues/3189>`__)
 * `@gtalarico <https://github.com/gtalarico>`__: 3 week old Build Stuck Cloning  (`#3126 <https://github.com/readthedocs/readthedocs.org/issues/3126>`__)
 * `@agjohnson <https://github.com/agjohnson>`__: Regressions with conf.py and error reporting (`#2963 <https://github.com/readthedocs/readthedocs.org/issues/2963>`__)
 * `@agjohnson <https://github.com/agjohnson>`__: Can't edit canonical domain (`#2922 <https://github.com/readthedocs/readthedocs.org/issues/2922>`__)
 * `@virtuald <https://github.com/virtuald>`__: Documentation stuck in 'cloning' state (`#2795 <https://github.com/readthedocs/readthedocs.org/issues/2795>`__)
 * `@Riyuzakii <https://github.com/Riyuzakii>`__: changed <strong> from html to css (`#2699 <https://github.com/readthedocs/readthedocs.org/pull/2699>`__)
 * `@tjanez <https://github.com/tjanez>`__: Support specifying 'python setup.py build_sphinx' as an alternative build command (`#1857 <https://github.com/readthedocs/readthedocs.org/issues/1857>`__)
 * `@bdarnell <https://github.com/bdarnell>`__: Broken edit links (`#1637 <https://github.com/readthedocs/readthedocs.org/issues/1637>`__)

Version 2.1.2
-------------

 * `@agjohnson <https://github.com/agjohnson>`__: Update changelog more consistently (`#3405 <https://github.com/readthedocs/readthedocs.org/pull/3405>`__)
 * `@agjohnson <https://github.com/agjohnson>`__: Update prerelease invoke command to call with explicit path (`#3404 <https://github.com/readthedocs/readthedocs.org/pull/3404>`__)
 * `@agjohnson <https://github.com/agjohnson>`__: Fix lint error (`#3402 <https://github.com/readthedocs/readthedocs.org/pull/3402>`__)
 * `@stsewd <https://github.com/stsewd>`__: Remove copyright application (`#3400 <https://github.com/readthedocs/readthedocs.org/pull/3400>`__)
 * `@humitos <https://github.com/humitos>`__: Show connect buttons for installed apps only (`#3394 <https://github.com/readthedocs/readthedocs.org/pull/3394>`__)
 * `@agjohnson <https://github.com/agjohnson>`__: Don't display the build suggestions div if there are no suggestions (`#3389 <https://github.com/readthedocs/readthedocs.org/pull/3389>`__)
 * `@jonrkarr <https://github.com/jonrkarr>`__: Error in YAML configuration docs: default value for `python.setup_py_install` should be `true` (`#3334 <https://github.com/readthedocs/readthedocs.org/issues/3334>`__)
 * `@humitos <https://github.com/humitos>`__: Simple task to finish inactive builds (`#3312 <https://github.com/readthedocs/readthedocs.org/pull/3312>`__)
 * `@agjohnson <https://github.com/agjohnson>`__: Cleanup misreported failed builds (`#3230 <https://github.com/readthedocs/readthedocs.org/issues/3230>`__)
 * `@agjohnson <https://github.com/agjohnson>`__: Remove copyright application (`#3199 <https://github.com/readthedocs/readthedocs.org/issues/3199>`__)

Version 2.1.1
-------------

Release information missing

Version 2.1.0
-------------

 * `@ericholscher <https://github.com/ericholscher>`__: Revert "Merge pull request #3336 from readthedocs/use-active-for-stable" (`#3368 <https://github.com/readthedocs/readthedocs.org/pull/3368>`__)
 * `@agjohnson <https://github.com/agjohnson>`__: Revert "Do not split before first argument (#3333)" (`#3366 <https://github.com/readthedocs/readthedocs.org/pull/3366>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Remove pitch from ethical ads page, point folks to actual pitch page. (`#3365 <https://github.com/readthedocs/readthedocs.org/pull/3365>`__)
 * `@agjohnson <https://github.com/agjohnson>`__: Add changelog and changelog automation (`#3364 <https://github.com/readthedocs/readthedocs.org/pull/3364>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Fix mkdocs search. (`#3361 <https://github.com/readthedocs/readthedocs.org/pull/3361>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Email sending: Allow kwargs for other options (`#3355 <https://github.com/readthedocs/readthedocs.org/pull/3355>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Try and get folks to put more tags. (`#3350 <https://github.com/readthedocs/readthedocs.org/pull/3350>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Suggest wiping your environment to folks with bad build outcomes. (`#3347 <https://github.com/readthedocs/readthedocs.org/pull/3347>`__)
 * `@humitos <https://github.com/humitos>`__: GitLab Integration (`#3327 <https://github.com/readthedocs/readthedocs.org/pull/3327>`__)
 * `@jimfulton <https://github.com/jimfulton>`__: Draft policy for claiming existing project names. (`#3314 <https://github.com/readthedocs/readthedocs.org/pull/3314>`__)
 * `@agjohnson <https://github.com/agjohnson>`__: More logic changes to error reporting, cleanup (`#3310 <https://github.com/readthedocs/readthedocs.org/pull/3310>`__)
 * `@safwanrahman <https://github.com/safwanrahman>`__: [Fix #3182] Better user deletion (`#3214 <https://github.com/readthedocs/readthedocs.org/pull/3214>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Better User deletion (`#3182 <https://github.com/readthedocs/readthedocs.org/issues/3182>`__)
 * `@RichardLitt <https://github.com/RichardLitt>`__: Add `Needed: replication` label (`#3138 <https://github.com/readthedocs/readthedocs.org/pull/3138>`__)
 * `@josejrobles <https://github.com/josejrobles>`__: Replaced usage of deprecated function get_fields_with_model with new … (`#3052 <https://github.com/readthedocs/readthedocs.org/pull/3052>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Don't delete the subprojects directory on sync of superproject (`#3042 <https://github.com/readthedocs/readthedocs.org/pull/3042>`__)
 * `@andrew <https://github.com/andrew>`__: Pass query string when redirecting, fixes #2595 (`#3001 <https://github.com/readthedocs/readthedocs.org/pull/3001>`__)
 * `@saily <https://github.com/saily>`__: Add GitLab repo sync and webhook support (`#1870 <https://github.com/readthedocs/readthedocs.org/pull/1870>`__)
 * ``@destroyerofbuilds``: Setup GitLab Web Hook on Project Import (`#1443 <https://github.com/readthedocs/readthedocs.org/issues/1443>`__)
 * `@takotuesday <https://github.com/takotuesday>`__: Add GitLab Provider from django-allauth (`#1441 <https://github.com/readthedocs/readthedocs.org/issues/1441>`__)

Version 2.0
-----------

 * `@ericholscher <https://github.com/ericholscher>`__: Email sending: Allow kwargs for other options (`#3355 <https://github.com/readthedocs/readthedocs.org/pull/3355>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Try and get folks to put more tags. (`#3350 <https://github.com/readthedocs/readthedocs.org/pull/3350>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Small changes to email sending to enable from email (`#3349 <https://github.com/readthedocs/readthedocs.org/pull/3349>`__)
 * `@dplanella <https://github.com/dplanella>`__: Duplicate TOC entries (`#3345 <https://github.com/readthedocs/readthedocs.org/issues/3345>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Small tweaks to ethical ads page (`#3344 <https://github.com/readthedocs/readthedocs.org/pull/3344>`__)
 * `@agjohnson <https://github.com/agjohnson>`__: Fix python usage around oauth pagination (`#3342 <https://github.com/readthedocs/readthedocs.org/pull/3342>`__)
 * `@tony <https://github.com/tony>`__: Fix isort link (`#3340 <https://github.com/readthedocs/readthedocs.org/pull/3340>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Change stable version switching to respect `active` (`#3336 <https://github.com/readthedocs/readthedocs.org/pull/3336>`__)
 * `@ericholscher <https://github.com/ericholscher>`__: Allow superusers to pass admin & member tests for projects (`#3335 <https://github.com/readthedocs/readthedocs.org/pull/3335>`__)
 * `@humitos <https://github.com/humitos>`__: Do not split before first argument (`#3333 <https://github.com/readthedocs/readthedocs.org/pull/3333>`__)
 * `@humitos <https://github.com/humitos>`__: Update docs for pre-commit (auto linting) (`#3332 <https://github.com/readthedocs/readthedocs.org/pull/3332>`__)
 * `@humitos <https://github.com/humitos>`__: Take preferece of tags over branches when selecting the stable version (`#3331 <https://github.com/readthedocs/readthedocs.org/pull/3331>`__)
 * `@humitos <https://github.com/humitos>`__: Add prospector as a pre-commit hook (`#3328 <https://github.com/readthedocs/readthedocs.org/pull/3328>`__)
 * `@andrewgodwin <https://github.com/andrewgodwin>`__: "stable" appearing to track future release branches (`#3268 <https://github.com/readthedocs/readthedocs.org/issues/3268>`__)
 * `@humitos <https://github.com/humitos>`__: Config files for auto linting (`#3264 <https://github.com/readthedocs/readthedocs.org/pull/3264>`__)
 * `@mekrip <https://github.com/mekrip>`__: Build is not working (`#3223 <https://github.com/readthedocs/readthedocs.org/issues/3223>`__)
 * `@skddc <https://github.com/skddc>`__: Add JSDoc to docs build environment (`#3069 <https://github.com/readthedocs/readthedocs.org/issues/3069>`__)
 * `@jakirkham <https://github.com/jakirkham>`__: Specifying conda version used (`#2076 <https://github.com/readthedocs/readthedocs.org/issues/2076>`__)
 * `@agjohnson <https://github.com/agjohnson>`__: Document code style guidelines (`#1475 <https://github.com/readthedocs/readthedocs.org/issues/1475>`__)
