.. TODO: This page could be a great overview of our build philosophy, but it's not quite there yet.

:orphan:

===============================
Continuous Documentation Deployment
===============================

Read the Docs is a *Continuous Documentation Deployment* platform for your software project.  
Every time you update your documentation, Read the Docs automatically detects the change and rebuilds your site.

-----------------------
How Continuous Deployment Works
-----------------------

Read the Docs integrates with repository providers such as **GitHub**, **GitLab**, and **Bitbucket**.  
Each time you push a new commit, the configured *webhook* notifies Read the Docs, which then triggers a new build.

When we receive a webhook, we match it to the project’s *Integration* and perform the following steps:

* :doc:`Build </builds>` the latest commit.
* Synchronize your :doc:`versions </versions>` based on new tags and branches in Git.
* Run your :doc:`automation rules </automation-rules>`.
* Automatically cancel any currently running builds for the same version.
* Add a log entry to the integration’s :guilabel:`Recent Activity`.

-----------------------
Documentation as Code
-----------------------

Read the Docs follows the principle of *Documentation as Code (Docs-as-Code)* —  
treating documentation with the same tools, workflows, and discipline as your source code.

By managing your documentation alongside your codebase, you gain:

* **Unified reviews:** documentation changes go through the same pull request process.
* **Faster feedback:** preview new docs before merging using :doc:`pull request previews </pull-requests>`.
* **Automation:** documentation stays up-to-date automatically after each code change.

Keeping your documentation integrated with your CI/CD pipeline ensures it evolves with your project — no extra steps, no forgotten updates.

-----------------------
Automated Versioning
-----------------------

Read the Docs allows your documentation to stay perfectly aligned with your software’s release cycle.  
When you tag a new release in Git, Read the Docs can automatically:

* Create and publish a :doc:`new documentation version </versions>`.
* Trigger automation rules via :doc:`/automation-rules`.
* Archive and preserve previous versions for user access.

You can manage versioning automatically or manually depending on your release workflow.  
All published versions remain accessible through the :term:`flyout menu` and can be enhanced using :doc:`/addons`.

-----------------------
Troubleshooting & Verification
-----------------------

If your webhook isn’t triggering builds:

1. Verify that your repository is correctly connected under **Project > Integrations**.
2. Check your repository’s webhook settings — you should see a **Read the Docs** webhook.
3. Push a small commit and check your build logs on the Read the Docs dashboard.

Common issues:
- **Webhook not firing:** check OAuth connection or make sure your repo is public.
- **Incorrect version built:** verify your default branch setting.
- **Builds stuck:** use the “Cancel Build” option and re-trigger manually.

-----------------------
See Also
-----------------------

* :doc:`/guides/setup/git-repo-manual` — set up your Git repository for automatic builds.
* :doc:`/automation-rules` — configure automated build rules and triggers.
* :doc:`/flyout-menu` — customize your project’s version switcher.
* [Integration Overview](https://docs.readthedocs.io/en/stable/integrations.html)
