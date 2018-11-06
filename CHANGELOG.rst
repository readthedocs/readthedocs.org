Version 2.8.1
-------------

:Date: November 06, 2018

* `@ericholscher <http://github.com/ericholscher>`__: Fix migration name on modified date migration (`#4867 <https://github.com/rtfd/readthedocs.org/pull/4867>`__)
* `@dojutsu-user <http://github.com/dojutsu-user>`__: Change 'VerisionLockedTimeout' to 'VersionLockedError' in comment. (`#4859 <https://github.com/rtfd/readthedocs.org/pull/4859>`__)
* `@stsewd <http://github.com/stsewd>`__: Fix rtd config file (`#4857 <https://github.com/rtfd/readthedocs.org/pull/4857>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Shorten project name to match slug length (`#4856 <https://github.com/rtfd/readthedocs.org/pull/4856>`__)
* `@stsewd <http://github.com/stsewd>`__: Generic message for parser error of config file (`#4853 <https://github.com/rtfd/readthedocs.org/pull/4853>`__)
* `@stsewd <http://github.com/stsewd>`__: Use $HOME as CWD for virtualenv creation (`#4852 <https://github.com/rtfd/readthedocs.org/pull/4852>`__)
* `@stsewd <http://github.com/stsewd>`__: Hide "edit on" when the version is a tag (`#4851 <https://github.com/rtfd/readthedocs.org/pull/4851>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Add modified_date to ImportedFile. (`#4850 <https://github.com/rtfd/readthedocs.org/pull/4850>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Use raw_id_fields so that the Feature admin loads (`#4849 <https://github.com/rtfd/readthedocs.org/pull/4849>`__)
* `@stsewd <http://github.com/stsewd>`__: Allow to change project's VCS (`#4845 <https://github.com/rtfd/readthedocs.org/pull/4845>`__)
* `@benjaoming <http://github.com/benjaoming>`__: Version compare warning text (`#4842 <https://github.com/rtfd/readthedocs.org/pull/4842>`__)
* `@dojutsu-user <http://github.com/dojutsu-user>`__: Make form for adopting project a choice field (`#4841 <https://github.com/rtfd/readthedocs.org/pull/4841>`__)
* `@humitos <http://github.com/humitos>`__: Do not send notification on VersionLockedError (`#4839 <https://github.com/rtfd/readthedocs.org/pull/4839>`__)
* `@stsewd <http://github.com/stsewd>`__: Start testing config v2 on our project (`#4838 <https://github.com/rtfd/readthedocs.org/pull/4838>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Add all migrations that are missing from model changes (`#4837 <https://github.com/rtfd/readthedocs.org/pull/4837>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Add docstring to DrfJsonSerializer so we know why it's there (`#4836 <https://github.com/rtfd/readthedocs.org/pull/4836>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Show the project's slug in the dashboard (`#4834 <https://github.com/rtfd/readthedocs.org/pull/4834>`__)
* `@humitos <http://github.com/humitos>`__: Avoid infinite redirection (`#4833 <https://github.com/rtfd/readthedocs.org/pull/4833>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Allow filtering builds by commit. (`#4831 <https://github.com/rtfd/readthedocs.org/pull/4831>`__)
* `@dojutsu-user <http://github.com/dojutsu-user>`__: Add 'Branding' under the 'Business Info' section and 'Guidelines' on 'Design Docs' (`#4830 <https://github.com/rtfd/readthedocs.org/pull/4830>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Migrate old passwords without "set_unusable_password" (`#4829 <https://github.com/rtfd/readthedocs.org/pull/4829>`__)
* `@humitos <http://github.com/humitos>`__: Do not import the Celery worker when running the Django app (`#4824 <https://github.com/rtfd/readthedocs.org/pull/4824>`__)
* `@damianz5 <http://github.com/damianz5>`__: Fix for jQuery in doc-embed call (`#4819 <https://github.com/rtfd/readthedocs.org/pull/4819>`__)
* `@invinciblycool <http://github.com/invinciblycool>`__: Add MkDocsYAMLParseError (`#4814 <https://github.com/rtfd/readthedocs.org/pull/4814>`__)
* `@stsewd <http://github.com/stsewd>`__: Delete untracked tags on fetch (`#4811 <https://github.com/rtfd/readthedocs.org/pull/4811>`__)
* `@stsewd <http://github.com/stsewd>`__: Don't activate version on build (`#4810 <https://github.com/rtfd/readthedocs.org/pull/4810>`__)
* `@humitos <http://github.com/humitos>`__: Feature flag to make `readthedocs` theme default on MkDocs docs (`#4802 <https://github.com/rtfd/readthedocs.org/pull/4802>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Allow use of `file://` urls in repos during development. (`#4801 <https://github.com/rtfd/readthedocs.org/pull/4801>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Release 2.7.2 (`#4796 <https://github.com/rtfd/readthedocs.org/pull/4796>`__)
* `@dojutsu-user <http://github.com/dojutsu-user>`__: Raise 404 at SubdomainMiddleware if the project does not exist. (`#4795 <https://github.com/rtfd/readthedocs.org/pull/4795>`__)
* `@dojutsu-user <http://github.com/dojutsu-user>`__: Add help_text in the form for adopting a project (`#4781 <https://github.com/rtfd/readthedocs.org/pull/4781>`__)
* `@humitos <http://github.com/humitos>`__: Add VAT ID field for Gold User (`#4776 <https://github.com/rtfd/readthedocs.org/pull/4776>`__)
* `@sriks123 <http://github.com/sriks123>`__: Remove logic around finding config file inside directories (`#4755 <https://github.com/rtfd/readthedocs.org/pull/4755>`__)
* `@dojutsu-user <http://github.com/dojutsu-user>`__: Improve unexpected error message when build fails (`#4754 <https://github.com/rtfd/readthedocs.org/pull/4754>`__)
* `@stsewd <http://github.com/stsewd>`__: Don't build latest on webhook if it is deactivated (`#4733 <https://github.com/rtfd/readthedocs.org/pull/4733>`__)
* `@dojutsu-user <http://github.com/dojutsu-user>`__: Change the way of using login_required decorator (`#4723 <https://github.com/rtfd/readthedocs.org/pull/4723>`__)
* `@invinciblycool <http://github.com/invinciblycool>`__: Remove unused views and their translations. (`#4632 <https://github.com/rtfd/readthedocs.org/pull/4632>`__)
* `@invinciblycool <http://github.com/invinciblycool>`__: Redirect to build detail post manual build (`#4622 <https://github.com/rtfd/readthedocs.org/pull/4622>`__)
* `@anubhavsinha98 <http://github.com/anubhavsinha98>`__: Issue #4551 Changed mock docks to use sphinx (`#4569 <https://github.com/rtfd/readthedocs.org/pull/4569>`__)
* `@xrmx <http://github.com/xrmx>`__: search: mark more strings for translation (`#4438 <https://github.com/rtfd/readthedocs.org/pull/4438>`__)
* `@Alig1493 <http://github.com/Alig1493>`__: Fix for issue #4092: Remove unused field from Project model (`#4431 <https://github.com/rtfd/readthedocs.org/pull/4431>`__)
* `@mashrikt <http://github.com/mashrikt>`__: Remove pytest _describe (`#4429 <https://github.com/rtfd/readthedocs.org/pull/4429>`__)
* `@xrmx <http://github.com/xrmx>`__: static: use modern getJSON callbacks (`#4382 <https://github.com/rtfd/readthedocs.org/pull/4382>`__)
* `@jaraco <http://github.com/jaraco>`__: Script for creating a project (`#4370 <https://github.com/rtfd/readthedocs.org/pull/4370>`__)
* `@xrmx <http://github.com/xrmx>`__: make it easier to use a different default theme (`#4278 <https://github.com/rtfd/readthedocs.org/pull/4278>`__)
* `@humitos <http://github.com/humitos>`__: Document alternate domains for business site (`#4271 <https://github.com/rtfd/readthedocs.org/pull/4271>`__)
* `@xrmx <http://github.com/xrmx>`__: restapi/client: don't use DRF parser for parsing (`#4160 <https://github.com/rtfd/readthedocs.org/pull/4160>`__)
* `@julienmalard <http://github.com/julienmalard>`__: New languages (`#3759 <https://github.com/rtfd/readthedocs.org/pull/3759>`__)
* `@stsewd <http://github.com/stsewd>`__: Improve installation guide (`#3631 <https://github.com/rtfd/readthedocs.org/pull/3631>`__)
* `@stsewd <http://github.com/stsewd>`__: Allow to hide version warning (`#3595 <https://github.com/rtfd/readthedocs.org/pull/3595>`__)
* `@Alig1493 <http://github.com/Alig1493>`__: [Fixed #872] Filter Builds according to commit (`#3544 <https://github.com/rtfd/readthedocs.org/pull/3544>`__)
* `@stsewd <http://github.com/stsewd>`__: Make slug field a valid DNS label (`#3464 <https://github.com/rtfd/readthedocs.org/pull/3464>`__)

Version 2.8.0
-------------

:Date: October 30, 2018

Major change is an upgrade to Django 1.11. 

* `@humitos <http://github.com/humitos>`__: Cleanup old code (remove old_div) (`#4817 <https://github.com/rtfd/readthedocs.org/pull/4817>`__)
* `@humitos <http://github.com/humitos>`__: Remove unnecessary migration (`#4806 <https://github.com/rtfd/readthedocs.org/pull/4806>`__)
* `@humitos <http://github.com/humitos>`__: Feature flag to make `readthedocs` theme default on MkDocs docs (`#4802 <https://github.com/rtfd/readthedocs.org/pull/4802>`__)
* `@stsewd <http://github.com/stsewd>`__: Add codecov badge (`#4799 <https://github.com/rtfd/readthedocs.org/pull/4799>`__)
* `@humitos <http://github.com/humitos>`__: Pin missing dependency for the MkDocs guide compatibility (`#4798 <https://github.com/rtfd/readthedocs.org/pull/4798>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Release 2.7.2 (`#4796 <https://github.com/rtfd/readthedocs.org/pull/4796>`__)
* `@humitos <http://github.com/humitos>`__: Do not log as error a webhook with an invalid branch name (`#4779 <https://github.com/rtfd/readthedocs.org/pull/4779>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Run travis on release branches (`#4763 <https://github.com/rtfd/readthedocs.org/pull/4763>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Remove Eric & Anthony from ADMINS & MANAGERS settings (`#4762 <https://github.com/rtfd/readthedocs.org/pull/4762>`__)
* `@stsewd <http://github.com/stsewd>`__: Don't use RequestsContext (`#4759 <https://github.com/rtfd/readthedocs.org/pull/4759>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Django 1.11 upgrade (`#4750 <https://github.com/rtfd/readthedocs.org/pull/4750>`__)
* `@stsewd <http://github.com/stsewd>`__: Dropdown to select Advanced Settings (`#4710 <https://github.com/rtfd/readthedocs.org/pull/4710>`__)
* `@stsewd <http://github.com/stsewd>`__: Remove hardcoded constant from config module (`#4704 <https://github.com/rtfd/readthedocs.org/pull/4704>`__)
* `@stsewd <http://github.com/stsewd>`__: Update tastypie (`#4325 <https://github.com/rtfd/readthedocs.org/pull/4325>`__)
* `@stsewd <http://github.com/stsewd>`__: Update to Django 1.10 (`#4319 <https://github.com/rtfd/readthedocs.org/pull/4319>`__)

Version 2.7.2
-------------

:Date: October 23, 2018

* `@humitos <http://github.com/humitos>`__: Validate the slug generated is valid before importing a project (`#4780 <https://github.com/rtfd/readthedocs.org/pull/4780>`__)
* `@humitos <http://github.com/humitos>`__: Do not log as error a webhook with an invalid branch name (`#4779 <https://github.com/rtfd/readthedocs.org/pull/4779>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Add an index page to our design docs. (`#4775 <https://github.com/rtfd/readthedocs.org/pull/4775>`__)
* `@dojutsu-user <http://github.com/dojutsu-user>`__: Remove /embed API endpoint (`#4771 <https://github.com/rtfd/readthedocs.org/pull/4771>`__)
* `@stsewd <http://github.com/stsewd>`__: Upgrade logs from debug on middleware (`#4769 <https://github.com/rtfd/readthedocs.org/pull/4769>`__)
* `@humitos <http://github.com/humitos>`__: Link to SSL for Custom Domains fixed (`#4766 <https://github.com/rtfd/readthedocs.org/pull/4766>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Remove Eric & Anthony from ADMINS & MANAGERS settings (`#4762 <https://github.com/rtfd/readthedocs.org/pull/4762>`__)
* `@humitos <http://github.com/humitos>`__: Do not re-raise the exception if the one that we are checking (`#4761 <https://github.com/rtfd/readthedocs.org/pull/4761>`__)
* `@humitos <http://github.com/humitos>`__: Do not fail when unlinking an non-existing path (`#4760 <https://github.com/rtfd/readthedocs.org/pull/4760>`__)
* `@humitos <http://github.com/humitos>`__: Allow to extend the DomainForm from outside (`#4752 <https://github.com/rtfd/readthedocs.org/pull/4752>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Fixes an OSX issue with the test suite (`#4748 <https://github.com/rtfd/readthedocs.org/pull/4748>`__)
* `@humitos <http://github.com/humitos>`__: Use Docker time limit for max lock age (`#4747 <https://github.com/rtfd/readthedocs.org/pull/4747>`__)
* `@xyNNN <http://github.com/xyNNN>`__: Fixed link of PagerDuty (`#4744 <https://github.com/rtfd/readthedocs.org/pull/4744>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Make storage syncers extend from a base class (`#4742 <https://github.com/rtfd/readthedocs.org/pull/4742>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Revert "Upgrade theme media to 0.4.2" (`#4735 <https://github.com/rtfd/readthedocs.org/pull/4735>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Upgrade theme media to 0.4.2 (`#4734 <https://github.com/rtfd/readthedocs.org/pull/4734>`__)
* `@stsewd <http://github.com/stsewd>`__: Extend install option from config file (v2, schema only) (`#4732 <https://github.com/rtfd/readthedocs.org/pull/4732>`__)
* `@stsewd <http://github.com/stsewd>`__: Remove /cname endpoint (`#4731 <https://github.com/rtfd/readthedocs.org/pull/4731>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Fix get_vcs_repo by moving it to the Mixin (`#4727 <https://github.com/rtfd/readthedocs.org/pull/4727>`__)
* `@humitos <http://github.com/humitos>`__: Guide explaining how to keep compatibility with mkdocs (`#4726 <https://github.com/rtfd/readthedocs.org/pull/4726>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Release 2.7.1 (`#4725 <https://github.com/rtfd/readthedocs.org/pull/4725>`__)
* `@dojutsu-user <http://github.com/dojutsu-user>`__: Fix the form for adopting a project (`#4721 <https://github.com/rtfd/readthedocs.org/pull/4721>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Remove logging verbosity on syncer failure (`#4717 <https://github.com/rtfd/readthedocs.org/pull/4717>`__)
* `@humitos <http://github.com/humitos>`__: Lint requirement file for py2 (`#4712 <https://github.com/rtfd/readthedocs.org/pull/4712>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Improve the getting started docs (`#4676 <https://github.com/rtfd/readthedocs.org/pull/4676>`__)
* `@stsewd <http://github.com/stsewd>`__: Strict validation in configuration file (v2 only) (`#4607 <https://github.com/rtfd/readthedocs.org/pull/4607>`__)
* `@stsewd <http://github.com/stsewd>`__: Run coverage on travis (`#4605 <https://github.com/rtfd/readthedocs.org/pull/4605>`__)

Version 2.7.1
-------------

:Date: October 04, 2018

* `@ericholscher <http://github.com/ericholscher>`__: Revert "Merge pull request #4636 from rtfd/search_upgrade" (`#4716 <https://github.com/rtfd/readthedocs.org/pull/4716>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Reduce the logging we do on CNAME 404 (`#4715 <https://github.com/rtfd/readthedocs.org/pull/4715>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Minor redirect admin improvements (`#4709 <https://github.com/rtfd/readthedocs.org/pull/4709>`__)
* `@humitos <http://github.com/humitos>`__: Define the doc_search reverse URL from inside the __init__ on test (`#4703 <https://github.com/rtfd/readthedocs.org/pull/4703>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Revert "auto refresh false" (`#4701 <https://github.com/rtfd/readthedocs.org/pull/4701>`__)
* `@browniebroke <http://github.com/browniebroke>`__: Remove unused package nilsimsa (`#4697 <https://github.com/rtfd/readthedocs.org/pull/4697>`__)
* `@stsewd <http://github.com/stsewd>`__: Fix broken url on sphinx projects (`#4696 <https://github.com/rtfd/readthedocs.org/pull/4696>`__)
* `@safwanrahman <http://github.com/safwanrahman>`__: Tuning elasticsearch shard and replica (`#4689 <https://github.com/rtfd/readthedocs.org/pull/4689>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Fix bug where we were not indexing Sphinx HTMLDir projects (`#4685 <https://github.com/rtfd/readthedocs.org/pull/4685>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Fix the queryset used in chunking (`#4683 <https://github.com/rtfd/readthedocs.org/pull/4683>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Fix python 2 syntax for getting first key in search index update (`#4682 <https://github.com/rtfd/readthedocs.org/pull/4682>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Release 2.7.0 (`#4681 <https://github.com/rtfd/readthedocs.org/pull/4681>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Increase footer ad text size (`#4678 <https://github.com/rtfd/readthedocs.org/pull/4678>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Fix broken docs links (`#4677 <https://github.com/rtfd/readthedocs.org/pull/4677>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Remove search autosync from tests so local tests work (`#4675 <https://github.com/rtfd/readthedocs.org/pull/4675>`__)
* `@stsewd <http://github.com/stsewd>`__: Refactor tasks into decorators (`#4666 <https://github.com/rtfd/readthedocs.org/pull/4666>`__)
* `@stsewd <http://github.com/stsewd>`__: Clean up logging (`#4665 <https://github.com/rtfd/readthedocs.org/pull/4665>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Ad customization docs (`#4659 <https://github.com/rtfd/readthedocs.org/pull/4659>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Fix a typo in the privacy policy (`#4658 <https://github.com/rtfd/readthedocs.org/pull/4658>`__)
* `@stsewd <http://github.com/stsewd>`__: Refactor PublicTask into a decorator task (`#4656 <https://github.com/rtfd/readthedocs.org/pull/4656>`__)
* `@stsewd <http://github.com/stsewd>`__: Remove -r option from update_repos command (`#4653 <https://github.com/rtfd/readthedocs.org/pull/4653>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Create an explicit ad placement (`#4647 <https://github.com/rtfd/readthedocs.org/pull/4647>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Use collectstatic on `media/`, without collecting user files (`#4502 <https://github.com/rtfd/readthedocs.org/pull/4502>`__)
* `@stsewd <http://github.com/stsewd>`__: Implement submodules key from v2 config (`#4493 <https://github.com/rtfd/readthedocs.org/pull/4493>`__)
* `@stsewd <http://github.com/stsewd>`__: Implement mkdocs key from v2 config (`#4486 <https://github.com/rtfd/readthedocs.org/pull/4486>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Add docs on our roadmap process (`#4469 <https://github.com/rtfd/readthedocs.org/pull/4469>`__)
* `@humitos <http://github.com/humitos>`__: Send notifications when generic/unhandled failures (`#3864 <https://github.com/rtfd/readthedocs.org/pull/3864>`__)
* `@stsewd <http://github.com/stsewd>`__: Use relative path for docroot on mkdocs (`#3525 <https://github.com/rtfd/readthedocs.org/pull/3525>`__)

Version 2.7.0
-------------

:Date: September 29, 2018

**Reverted, do not use**

Version 2.6.6
-------------

:Date: September 25, 2018

* `@davidfischer <http://github.com/davidfischer>`__: Fix a markdown test error (`#4663 <https://github.com/rtfd/readthedocs.org/pull/4663>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Ad customization docs (`#4659 <https://github.com/rtfd/readthedocs.org/pull/4659>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Fix a typo in the privacy policy (`#4658 <https://github.com/rtfd/readthedocs.org/pull/4658>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Put search step back into project build task (`#4655 <https://github.com/rtfd/readthedocs.org/pull/4655>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Create an explicit ad placement (`#4647 <https://github.com/rtfd/readthedocs.org/pull/4647>`__)
* `@stsewd <http://github.com/stsewd>`__: Fix some typos in docs and code (`#4646 <https://github.com/rtfd/readthedocs.org/pull/4646>`__)
* `@stsewd <http://github.com/stsewd>`__: Downgrade celery (`#4644 <https://github.com/rtfd/readthedocs.org/pull/4644>`__)
* `@stsewd <http://github.com/stsewd>`__: Downgrade django-taggit (`#4639 <https://github.com/rtfd/readthedocs.org/pull/4639>`__)
* `@safwanrahman <http://github.com/safwanrahman>`__: [Fix #4247] deleting old search code (`#4635 <https://github.com/rtfd/readthedocs.org/pull/4635>`__)
* `@stsewd <http://github.com/stsewd>`__: Add change versions slug to faq (`#4633 <https://github.com/rtfd/readthedocs.org/pull/4633>`__)
* `@stsewd <http://github.com/stsewd>`__: Pin sphinx to a compatible version (`#4631 <https://github.com/rtfd/readthedocs.org/pull/4631>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Make ads more obvious that they are ads (`#4628 <https://github.com/rtfd/readthedocs.org/pull/4628>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Change mentions of "CNAME" -> custom domain (`#4627 <https://github.com/rtfd/readthedocs.org/pull/4627>`__)
* `@invinciblycool <http://github.com/invinciblycool>`__: Use validate_dict for more accurate error messages (`#4617 <https://github.com/rtfd/readthedocs.org/pull/4617>`__)
* `@safwanrahman <http://github.com/safwanrahman>`__: fixing the indexing (`#4615 <https://github.com/rtfd/readthedocs.org/pull/4615>`__)
* `@humitos <http://github.com/humitos>`__: Update our sponsors to mention Azure (`#4614 <https://github.com/rtfd/readthedocs.org/pull/4614>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Add cwd to subprocess calls (`#4611 <https://github.com/rtfd/readthedocs.org/pull/4611>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Make restapi URL additions conditional (`#4609 <https://github.com/rtfd/readthedocs.org/pull/4609>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Ability to use supervisor from python 2.7 and still run Python 3 (`#4606 <https://github.com/rtfd/readthedocs.org/pull/4606>`__)
* `@humitos <http://github.com/humitos>`__: Return 404 for inactive versions and allow redirects on them (`#4599 <https://github.com/rtfd/readthedocs.org/pull/4599>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Fixes an issue with duplicate gold subscriptions (`#4597 <https://github.com/rtfd/readthedocs.org/pull/4597>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Fix ad block nag project issue (`#4596 <https://github.com/rtfd/readthedocs.org/pull/4596>`__)
* `@humitos <http://github.com/humitos>`__: Run all our tests with Python 3.6 on Travis (`#4592 <https://github.com/rtfd/readthedocs.org/pull/4592>`__)
* `@humitos <http://github.com/humitos>`__: Sanitize command output when running under DockerBuildEnvironment (`#4591 <https://github.com/rtfd/readthedocs.org/pull/4591>`__)
* `@humitos <http://github.com/humitos>`__: Force resolver to use PUBLIC_DOMAIN over HTTPS if not Domain.https (`#4579 <https://github.com/rtfd/readthedocs.org/pull/4579>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Updates and simplification for mkdocs (`#4556 <https://github.com/rtfd/readthedocs.org/pull/4556>`__)
* `@humitos <http://github.com/humitos>`__: Docs for hidding "On ..." section from versions menu (`#4547 <https://github.com/rtfd/readthedocs.org/pull/4547>`__)
* `@stsewd <http://github.com/stsewd>`__: Implement sphinx key from v2 config (`#4482 <https://github.com/rtfd/readthedocs.org/pull/4482>`__)
* `@safwanrahman <http://github.com/safwanrahman>`__: [Fix #4268] Adding Documentation for upgraded Search (`#4467 <https://github.com/rtfd/readthedocs.org/pull/4467>`__)
* `@humitos <http://github.com/humitos>`__: Upgrade all packages using pur (`#4318 <https://github.com/rtfd/readthedocs.org/pull/4318>`__)
* `@humitos <http://github.com/humitos>`__: Clean CC sensible data on Gold subscriptions (`#4291 <https://github.com/rtfd/readthedocs.org/pull/4291>`__)
* `@stsewd <http://github.com/stsewd>`__: Update docs to match the new triague guidelines (`#4260 <https://github.com/rtfd/readthedocs.org/pull/4260>`__)
* `@xrmx <http://github.com/xrmx>`__: Make the STABLE and LATEST constants overridable (`#4099 <https://github.com/rtfd/readthedocs.org/pull/4099>`__)
* `@stsewd <http://github.com/stsewd>`__: Use str to get the exception message (`#3912 <https://github.com/rtfd/readthedocs.org/pull/3912>`__)

Version 2.6.5
-------------

:Date: August 29, 2018

* `@stsewd <http://github.com/stsewd>`__: Tests for yaml file regex (`#4587 <https://github.com/rtfd/readthedocs.org/pull/4587>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Respect user language when caching homepage (`#4585 <https://github.com/rtfd/readthedocs.org/pull/4585>`__)
* `@humitos <http://github.com/humitos>`__: Add start and termination to YAML file regex (`#4584 <https://github.com/rtfd/readthedocs.org/pull/4584>`__)
* `@safwanrahman <http://github.com/safwanrahman>`__: [Fix #4576] Do not delete projects which have multiple users (`#4577 <https://github.com/rtfd/readthedocs.org/pull/4577>`__)

Version 2.6.4
-------------

:Date: August 29, 2018

* `@stsewd <http://github.com/stsewd>`__: Update tests failing on master (`#4575 <https://github.com/rtfd/readthedocs.org/pull/4575>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Add a flag to disable docsearch (`#4570 <https://github.com/rtfd/readthedocs.org/pull/4570>`__)
* `@stsewd <http://github.com/stsewd>`__: Fix nested syntax in docs (`#4567 <https://github.com/rtfd/readthedocs.org/pull/4567>`__)
* `@stsewd <http://github.com/stsewd>`__: Fix incorrect reraise (`#4566 <https://github.com/rtfd/readthedocs.org/pull/4566>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Add a note about specifying the version of build tools (`#4562 <https://github.com/rtfd/readthedocs.org/pull/4562>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Serve badges directly from local filesystem (`#4561 <https://github.com/rtfd/readthedocs.org/pull/4561>`__)
* `@humitos <http://github.com/humitos>`__: Build JSON artifacts in HTML builder (`#4554 <https://github.com/rtfd/readthedocs.org/pull/4554>`__)
* `@humitos <http://github.com/humitos>`__: Route task to proper queue (`#4553 <https://github.com/rtfd/readthedocs.org/pull/4553>`__)
* `@humitos <http://github.com/humitos>`__: Sanitize BuildCommand.output by removing NULL characters (`#4552 <https://github.com/rtfd/readthedocs.org/pull/4552>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Fix changelog for 2.6.3 (`#4548 <https://github.com/rtfd/readthedocs.org/pull/4548>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Remove hiredis (`#4542 <https://github.com/rtfd/readthedocs.org/pull/4542>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Use the STATIC_URL for static files to avoid redirection (`#4522 <https://github.com/rtfd/readthedocs.org/pull/4522>`__)
* `@stsewd <http://github.com/stsewd>`__: Update docs about build process (`#4515 <https://github.com/rtfd/readthedocs.org/pull/4515>`__)
* `@StefanoChiodino <http://github.com/StefanoChiodino>`__: Allow for period as a prefix and yaml extension for config file (`#4512 <https://github.com/rtfd/readthedocs.org/pull/4512>`__)
* `@AumitLeon <http://github.com/AumitLeon>`__: Update information on mkdocs build process (`#4508 <https://github.com/rtfd/readthedocs.org/pull/4508>`__)
* `@humitos <http://github.com/humitos>`__: Fix Exact Redirect to work properly when using $rest keyword (`#4501 <https://github.com/rtfd/readthedocs.org/pull/4501>`__)
* `@humitos <http://github.com/humitos>`__: Mark some BuildEnvironmentError exceptions as Warning and do not log them (`#4495 <https://github.com/rtfd/readthedocs.org/pull/4495>`__)
* `@xrmx <http://github.com/xrmx>`__: projects: don't explode trying to update UpdateDocsTaskStep state (`#4485 <https://github.com/rtfd/readthedocs.org/pull/4485>`__)
* `@humitos <http://github.com/humitos>`__: Note with the developer flow to update our app translations (`#4481 <https://github.com/rtfd/readthedocs.org/pull/4481>`__)
* `@humitos <http://github.com/humitos>`__: Add `trimmed` to all multilines `blocktrans` tags (`#4480 <https://github.com/rtfd/readthedocs.org/pull/4480>`__)
* `@humitos <http://github.com/humitos>`__: Example and note with usage of trimmed option in blocktrans (`#4479 <https://github.com/rtfd/readthedocs.org/pull/4479>`__)
* `@humitos <http://github.com/humitos>`__: Update Transifex resources for our documentation (`#4478 <https://github.com/rtfd/readthedocs.org/pull/4478>`__)
* `@humitos <http://github.com/humitos>`__: Documentation for Manage Translations (`#4470 <https://github.com/rtfd/readthedocs.org/pull/4470>`__)
* `@stsewd <http://github.com/stsewd>`__: Port https://github.com/rtfd/readthedocs-build/pull/38/ (`#4461 <https://github.com/rtfd/readthedocs.org/pull/4461>`__)
* `@stsewd <http://github.com/stsewd>`__: Match v1 config interface to new one (`#4456 <https://github.com/rtfd/readthedocs.org/pull/4456>`__)
* `@humitos <http://github.com/humitos>`__: Skip tags that point to blob objects instead of commits (`#4442 <https://github.com/rtfd/readthedocs.org/pull/4442>`__)
* `@stsewd <http://github.com/stsewd>`__: Document python.use_system_site_packages option (`#4422 <https://github.com/rtfd/readthedocs.org/pull/4422>`__)
* `@humitos <http://github.com/humitos>`__: More tips about how to reduce resources usage (`#4419 <https://github.com/rtfd/readthedocs.org/pull/4419>`__)
* `@xrmx <http://github.com/xrmx>`__: projects: user in ProjectQuerySetBase.for_admin_user is mandatory (`#4417 <https://github.com/rtfd/readthedocs.org/pull/4417>`__)

Version 2.6.3
-------------

:Date: August 18, 2018

Release to Azure!

* `@davidfischer <http://github.com/davidfischer>`__: Add Sponsors list to footer (`#4424 <https://github.com/rtfd/readthedocs.org/pull/4424>`__)
* `@stsewd <http://github.com/stsewd>`__: Cache node_modules to speed up CI (`#4484 <https://github.com/rtfd/readthedocs.org/pull/4484>`__)
* `@xrmx <http://github.com/xrmx>`__: templates: mark missing string for translation on project edit (`#4518 <https://github.com/rtfd/readthedocs.org/pull/4518>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Performance improvement: cache version listing on the homepage (`#4526 <https://github.com/rtfd/readthedocs.org/pull/4526>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Remove mailgun from our dependencies (`#4531 <https://github.com/rtfd/readthedocs.org/pull/4531>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Improved ad block detection (`#4532 <https://github.com/rtfd/readthedocs.org/pull/4532>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Revert "Remove SelectiveFileSystemFolder finder workaround" (`#4533 <https://github.com/rtfd/readthedocs.org/pull/4533>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Slight clarification on turning off ads for a project (`#4534 <https://github.com/rtfd/readthedocs.org/pull/4534>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Fix the sponsor image paths (`#4535 <https://github.com/rtfd/readthedocs.org/pull/4535>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Update build assets (`#4537 <https://github.com/rtfd/readthedocs.org/pull/4537>`__)


Version 2.6.2
-------------

:Date: August 14, 2018

* `@davidfischer <http://github.com/davidfischer>`__: Custom domain clarifications (`#4514 <https://github.com/rtfd/readthedocs.org/pull/4514>`__)
* `@trein <http://github.com/trein>`__: Use single quote throughout the file (`#4513 <https://github.com/rtfd/readthedocs.org/pull/4513>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Support ads on pallets themes (`#4499 <https://github.com/rtfd/readthedocs.org/pull/4499>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Only use HostHeaderSSLAdapter for SSL/HTTPS connections (`#4498 <https://github.com/rtfd/readthedocs.org/pull/4498>`__)
* `@keflavich <http://github.com/keflavich>`__: Very minor English correction (`#4497 <https://github.com/rtfd/readthedocs.org/pull/4497>`__)
* `@davidfischer <http://github.com/davidfischer>`__: All static media is run through "collectstatic" (`#4489 <https://github.com/rtfd/readthedocs.org/pull/4489>`__)
* `@humitos <http://github.com/humitos>`__: Fix reST structure (`#4488 <https://github.com/rtfd/readthedocs.org/pull/4488>`__)
* `@nijel <http://github.com/nijel>`__: Document expected delay on CNAME change and need for CAA (`#4487 <https://github.com/rtfd/readthedocs.org/pull/4487>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Allow enforcing HTTPS for custom domains (`#4483 <https://github.com/rtfd/readthedocs.org/pull/4483>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Add some details around community ad qualifications (`#4436 <https://github.com/rtfd/readthedocs.org/pull/4436>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Updates to manifest storage (`#4430 <https://github.com/rtfd/readthedocs.org/pull/4430>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Update alt domains docs with SSL (`#4425 <https://github.com/rtfd/readthedocs.org/pull/4425>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Add SNI support for API HTTPS endpoint (`#4423 <https://github.com/rtfd/readthedocs.org/pull/4423>`__)
* `@davidfischer <http://github.com/davidfischer>`__: API v1 cleanup (`#4415 <https://github.com/rtfd/readthedocs.org/pull/4415>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Allow filtering versions by active (`#4414 <https://github.com/rtfd/readthedocs.org/pull/4414>`__)
* `@mlncn <http://github.com/mlncn>`__: Fix broken link (`#4410 <https://github.com/rtfd/readthedocs.org/pull/4410>`__)
* `@safwanrahman <http://github.com/safwanrahman>`__: [Fix #4407] Port Project Search for Elasticsearch 6.x (`#4408 <https://github.com/rtfd/readthedocs.org/pull/4408>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Add client ID to Google Analytics requests (`#4404 <https://github.com/rtfd/readthedocs.org/pull/4404>`__)
* `@xrmx <http://github.com/xrmx>`__: projects: fix filtering in projects_tag_detail (`#4398 <https://github.com/rtfd/readthedocs.org/pull/4398>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Fix a proxy model bug related to ad-free (`#4390 <https://github.com/rtfd/readthedocs.org/pull/4390>`__)
* `@humitos <http://github.com/humitos>`__: Release 2.6.1 (`#4389 <https://github.com/rtfd/readthedocs.org/pull/4389>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Do not access database from builds to check ad-free (`#4387 <https://github.com/rtfd/readthedocs.org/pull/4387>`__)
* `@humitos <http://github.com/humitos>`__: Adapt YAML config integration tests (`#4385 <https://github.com/rtfd/readthedocs.org/pull/4385>`__)
* `@stsewd <http://github.com/stsewd>`__: Set full `source_file` path for default configuration (`#4379 <https://github.com/rtfd/readthedocs.org/pull/4379>`__)
* `@humitos <http://github.com/humitos>`__: Make `get_version` usable from a specified path (`#4376 <https://github.com/rtfd/readthedocs.org/pull/4376>`__)
* `@humitos <http://github.com/humitos>`__: More tags when logging errors to Sentry (`#4375 <https://github.com/rtfd/readthedocs.org/pull/4375>`__)
* `@humitos <http://github.com/humitos>`__: Check for 'options' in update_repos command (`#4373 <https://github.com/rtfd/readthedocs.org/pull/4373>`__)
* `@safwanrahman <http://github.com/safwanrahman>`__: [Fix  #4333] Implement asynchronous search reindex functionality using celery (`#4368 <https://github.com/rtfd/readthedocs.org/pull/4368>`__)
* `@stsewd <http://github.com/stsewd>`__: V2 of the configuration file (`#4355 <https://github.com/rtfd/readthedocs.org/pull/4355>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Remove the UID from the GA measurement protocol (`#4347 <https://github.com/rtfd/readthedocs.org/pull/4347>`__)
* `@humitos <http://github.com/humitos>`__: Mount `pip_cache_path` in Docker container (`#3556 <https://github.com/rtfd/readthedocs.org/pull/3556>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Show subprojects in search results (`#1866 <https://github.com/rtfd/readthedocs.org/pull/1866>`__)

Version 2.6.1
-------------

:Date: July 17, 2018

* `@davidfischer <http://github.com/davidfischer>`__: Do not access database from builds to check ad-free (`#4387 <https://github.com/rtfd/readthedocs.org/pull/4387>`__)
* `@humitos <http://github.com/humitos>`__: Adapt YAML config integration tests (`#4385 <https://github.com/rtfd/readthedocs.org/pull/4385>`__)
* `@stsewd <http://github.com/stsewd>`__: Set full `source_file` path for default configuration (`#4379 <https://github.com/rtfd/readthedocs.org/pull/4379>`__)
* `@humitos <http://github.com/humitos>`__: More tags when logging errors to Sentry (`#4375 <https://github.com/rtfd/readthedocs.org/pull/4375>`__)

Version 2.6.0
-------------

:Date: July 16, 2018

* Adds initial support for HTTPS on custom domains
* `@stsewd <http://github.com/stsewd>`__: Revert "projects: serve badge with same protocol as site" (`#4353 <https://github.com/rtfd/readthedocs.org/pull/4353>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Do not overwrite sphinx context variables feature (`#4349 <https://github.com/rtfd/readthedocs.org/pull/4349>`__)
* `@stsewd <http://github.com/stsewd>`__: Calrify docs about how rtd select the stable version (`#4348 <https://github.com/rtfd/readthedocs.org/pull/4348>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Remove the UID from the GA measurement protocol (`#4347 <https://github.com/rtfd/readthedocs.org/pull/4347>`__)
* `@stsewd <http://github.com/stsewd>`__: Fix error in command (`#4345 <https://github.com/rtfd/readthedocs.org/pull/4345>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Improvements for the build/version admin (`#4344 <https://github.com/rtfd/readthedocs.org/pull/4344>`__)
* `@safwanrahman <http://github.com/safwanrahman>`__: [Fix #4265] Porting frontend docsearch to work with new API (`#4340 <https://github.com/rtfd/readthedocs.org/pull/4340>`__)
* `@ktdreyer <http://github.com/ktdreyer>`__: fix spelling of "demonstrating" (`#4336 <https://github.com/rtfd/readthedocs.org/pull/4336>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Warning about theme context implementation status (`#4335 <https://github.com/rtfd/readthedocs.org/pull/4335>`__)
* `@Blendify <http://github.com/Blendify>`__: Docs: Let Theme Choose Pygments Theme (`#4331 <https://github.com/rtfd/readthedocs.org/pull/4331>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Disable the ad block nag for ad-free projects (`#4329 <https://github.com/rtfd/readthedocs.org/pull/4329>`__)
* `@safwanrahman <http://github.com/safwanrahman>`__: [fix #4265] Port Document search API for Elasticsearch 6.x (`#4309 <https://github.com/rtfd/readthedocs.org/pull/4309>`__)
* `@stsewd <http://github.com/stsewd>`__: Refactor configuration object to class based (`#4298 <https://github.com/rtfd/readthedocs.org/pull/4298>`__)

Version 2.5.3
-------------

:Date: July 05, 2018

* `@xrmx <http://github.com/xrmx>`__: Do less work in querysets (`#4322 <https://github.com/rtfd/readthedocs.org/pull/4322>`__)
* `@stsewd <http://github.com/stsewd>`__: Fix deprecations in management commands (`#4321 <https://github.com/rtfd/readthedocs.org/pull/4321>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Add a flag for marking a project ad-free (`#4313 <https://github.com/rtfd/readthedocs.org/pull/4313>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Use "npm run lint" from tox (`#4312 <https://github.com/rtfd/readthedocs.org/pull/4312>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Fix issues building static assets (`#4311 <https://github.com/rtfd/readthedocs.org/pull/4311>`__)
* `@humitos <http://github.com/humitos>`__: Use PATHs to call clear_artifacts (`#4296 <https://github.com/rtfd/readthedocs.org/pull/4296>`__)
* `@safwanrahman <http://github.com/safwanrahman>`__: [Fix #2457] Implement exact match search (`#4292 <https://github.com/rtfd/readthedocs.org/pull/4292>`__)
* `@davidfischer <http://github.com/davidfischer>`__: API filtering improvements (`#4285 <https://github.com/rtfd/readthedocs.org/pull/4285>`__)
* `@annegentle <http://github.com/annegentle>`__: Remove self-referencing links for webhooks docs (`#4283 <https://github.com/rtfd/readthedocs.org/pull/4283>`__)
* `@safwanrahman <http://github.com/safwanrahman>`__: [Fix #2328 #2013] Refresh search index and test for case insensitive search (`#4277 <https://github.com/rtfd/readthedocs.org/pull/4277>`__)
* `@xrmx <http://github.com/xrmx>`__: doc_builder: clarify sphinx backend append_conf docstring (`#4276 <https://github.com/rtfd/readthedocs.org/pull/4276>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Add documentation for APIv2 (`#4274 <https://github.com/rtfd/readthedocs.org/pull/4274>`__)
* `@humitos <http://github.com/humitos>`__: Wrap notifications HTML code into a block (`#4273 <https://github.com/rtfd/readthedocs.org/pull/4273>`__)
* `@stsewd <http://github.com/stsewd>`__: Move config.py from rtd build (`#4272 <https://github.com/rtfd/readthedocs.org/pull/4272>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Fix our use of `--use-wheel` in pip. (`#4269 <https://github.com/rtfd/readthedocs.org/pull/4269>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Revert "Merge pull request #4206 from FlorianKuckelkorn/fix/pip-breaking-change" (`#4261 <https://github.com/rtfd/readthedocs.org/pull/4261>`__)
* `@humitos <http://github.com/humitos>`__: Fix triggering a build for a skipped project (`#4255 <https://github.com/rtfd/readthedocs.org/pull/4255>`__)
* `@stsewd <http://github.com/stsewd>`__: Update default sphinx version (`#4250 <https://github.com/rtfd/readthedocs.org/pull/4250>`__)
* `@stsewd <http://github.com/stsewd>`__: Move config module from rtd-build repo (`#4242 <https://github.com/rtfd/readthedocs.org/pull/4242>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Allow staying logged in for longer (`#4236 <https://github.com/rtfd/readthedocs.org/pull/4236>`__)
* `@safwanrahman <http://github.com/safwanrahman>`__: Upgrade Elasticsearch to version 6.x (`#4211 <https://github.com/rtfd/readthedocs.org/pull/4211>`__)
* `@humitos <http://github.com/humitos>`__: Make tests extensible from corporate site (`#4095 <https://github.com/rtfd/readthedocs.org/pull/4095>`__)
* `@stsewd <http://github.com/stsewd>`__: `stable` version stuck on a specific commit (`#3913 <https://github.com/rtfd/readthedocs.org/pull/3913>`__)

Version 2.5.2
-------------

:Date: June 18, 2018

* `@davidfischer <http://github.com/davidfischer>`_: Add a page detailing ad blocking (`#4244 <https://github.com/rtfd/readthedocs.org/pull/4244>`_)
* `@xrmx <http://github.com/xrmx>`_: projects: serve badge with same protocol as site (`#4228 <https://github.com/rtfd/readthedocs.org/pull/4228>`_)
* `@FlorianKuckelkorn <http://github.com/FlorianKuckelkorn>`_: Fixed breaking change in pip 10.0.0b1 (2018-03-31) (`#4206 <https://github.com/rtfd/readthedocs.org/pull/4206>`_)
* `@StefanoChiodino <http://github.com/StefanoChiodino>`_: Document that readthedocs file can now have yaml extension (`#4129 <https://github.com/rtfd/readthedocs.org/pull/4129>`_)
* `@humitos <http://github.com/humitos>`_: Downgrade docker to 3.1.3 because of timeouts in EXEC call (`#4241 <https://github.com/rtfd/readthedocs.org/pull/4241>`_)
* `@stsewd <http://github.com/stsewd>`_: Move parser tests from rtd-build repo (`#4225 <https://github.com/rtfd/readthedocs.org/pull/4225>`_)
* `@humitos <http://github.com/humitos>`_: Handle revoked oauth permissions by the user (`#4074 <https://github.com/rtfd/readthedocs.org/pull/4074>`_)
* `@humitos <http://github.com/humitos>`_: Allow to hook the initial build from outside (`#4033 <https://github.com/rtfd/readthedocs.org/pull/4033>`_)

Version 2.5.1
-------------

:Date: June 14, 2018

* `@stsewd <http://github.com/stsewd>`_: Add feature to build json with html in the same build (`#4229 <https://github.com/rtfd/readthedocs.org/pull/4229>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Prioritize ads based on content (`#4224 <https://github.com/rtfd/readthedocs.org/pull/4224>`_)
* `@mostaszewski <http://github.com/mostaszewski>`_: #4170 - Link the version in the footer to the changelog (`#4217 <https://github.com/rtfd/readthedocs.org/pull/4217>`_)
* `@Jmennius <http://github.com/Jmennius>`_: Add provision_elasticsearch command (`#4216 <https://github.com/rtfd/readthedocs.org/pull/4216>`_)
* `@SuriyaaKudoIsc <http://github.com/SuriyaaKudoIsc>`_: Use the latest YouTube share URL (`#4209 <https://github.com/rtfd/readthedocs.org/pull/4209>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Allow staff to trigger project builds (`#4207 <https://github.com/rtfd/readthedocs.org/pull/4207>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Use autosectionlabel in the privacy policy (`#4204 <https://github.com/rtfd/readthedocs.org/pull/4204>`_)
* `@davidfischer <http://github.com/davidfischer>`_: These links weren't correct after #3632 (`#4203 <https://github.com/rtfd/readthedocs.org/pull/4203>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Release 2.5.0 (`#4200 <https://github.com/rtfd/readthedocs.org/pull/4200>`_)
* `@ericholscher <http://github.com/ericholscher>`_: Fix Build: Convert md to rst in docs (`#4199 <https://github.com/rtfd/readthedocs.org/pull/4199>`_)
* `@ericholscher <http://github.com/ericholscher>`_: Updates to #3850 to fix merge conflict (`#4198 <https://github.com/rtfd/readthedocs.org/pull/4198>`_)
* `@ericholscher <http://github.com/ericholscher>`_: Build on top of #3881 and put docs in custom_installs. (`#4196 <https://github.com/rtfd/readthedocs.org/pull/4196>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Increase the max theme version (`#4195 <https://github.com/rtfd/readthedocs.org/pull/4195>`_)
* `@ericholscher <http://github.com/ericholscher>`_: Remove maxcdn reqs (`#4194 <https://github.com/rtfd/readthedocs.org/pull/4194>`_)
* `@ericholscher <http://github.com/ericholscher>`_: Add missing gitignore item for ES testing (`#4193 <https://github.com/rtfd/readthedocs.org/pull/4193>`_)
* `@xrmx <http://github.com/xrmx>`_: fabfile: update i18n helpers (`#4189 <https://github.com/rtfd/readthedocs.org/pull/4189>`_)
* `@xrmx <http://github.com/xrmx>`_: Update italian locale (`#4188 <https://github.com/rtfd/readthedocs.org/pull/4188>`_)
* `@xrmx <http://github.com/xrmx>`_: locale: update and build the english translation (`#4187 <https://github.com/rtfd/readthedocs.org/pull/4187>`_)
* `@humitos <http://github.com/humitos>`_: Upgrade celery to avoid AtributeError:async (`#4185 <https://github.com/rtfd/readthedocs.org/pull/4185>`_)
* `@stsewd <http://github.com/stsewd>`_: Prepare code for custo mkdocs.yaml location (`#4184 <https://github.com/rtfd/readthedocs.org/pull/4184>`_)
* `@agjohnson <http://github.com/agjohnson>`_: Updates to our triage guidelines (`#4180 <https://github.com/rtfd/readthedocs.org/pull/4180>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Server side analytics (`#4131 <https://github.com/rtfd/readthedocs.org/pull/4131>`_)
* `@humitos <http://github.com/humitos>`_: Upgrade packages with pur (`#4124 <https://github.com/rtfd/readthedocs.org/pull/4124>`_)
* `@stsewd <http://github.com/stsewd>`_: Fix resync remote repos (`#4113 <https://github.com/rtfd/readthedocs.org/pull/4113>`_)
* `@stsewd <http://github.com/stsewd>`_: Add schema for configuration file with yamale (`#4084 <https://github.com/rtfd/readthedocs.org/pull/4084>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Ad block nag to urge people to whitelist (`#4037 <https://github.com/rtfd/readthedocs.org/pull/4037>`_)
* `@benjaoming <http://github.com/benjaoming>`_: Add Mexican Spanish as a project language (`#3588 <https://github.com/rtfd/readthedocs.org/pull/3588>`_)

Version 2.5.0
-------------

:Date: June 06, 2018

* `@ericholscher <http://github.com/ericholscher>`_: Fix Build: Convert md to rst in docs (`#4199 <https://github.com/rtfd/readthedocs.org/pull/4199>`_)
* `@ericholscher <http://github.com/ericholscher>`_: Remove maxcdn reqs (`#4194 <https://github.com/rtfd/readthedocs.org/pull/4194>`_)
* `@ericholscher <http://github.com/ericholscher>`_: Add missing gitignore item for ES testing (`#4193 <https://github.com/rtfd/readthedocs.org/pull/4193>`_)
* `@xrmx <http://github.com/xrmx>`_: fabfile: update i18n helpers (`#4189 <https://github.com/rtfd/readthedocs.org/pull/4189>`_)
* `@xrmx <http://github.com/xrmx>`_: Update italian locale (`#4188 <https://github.com/rtfd/readthedocs.org/pull/4188>`_)
* `@xrmx <http://github.com/xrmx>`_: locale: update and build the english translation (`#4187 <https://github.com/rtfd/readthedocs.org/pull/4187>`_)
* `@safwanrahman <http://github.com/safwanrahman>`_: Test for search functionality (`#4116 <https://github.com/rtfd/readthedocs.org/pull/4116>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Update mkdocs to the latest (`#4041 <https://github.com/rtfd/readthedocs.org/pull/4041>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Ad block nag to urge people to whitelist (`#4037 <https://github.com/rtfd/readthedocs.org/pull/4037>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Decouple the theme JS from readthedocs.org (`#3968 <https://github.com/rtfd/readthedocs.org/pull/3968>`_)
* `@xrmx <http://github.com/xrmx>`_: tests: fixup url tests in test_privacy_urls (`#3966 <https://github.com/rtfd/readthedocs.org/pull/3966>`_)
* `@fenilgandhi <http://github.com/fenilgandhi>`_: Add support for different badge styles (`#3632 <https://github.com/rtfd/readthedocs.org/pull/3632>`_)
* `@benjaoming <http://github.com/benjaoming>`_: Add Mexican Spanish as a project language (`#3588 <https://github.com/rtfd/readthedocs.org/pull/3588>`_)
* `@stsewd <http://github.com/stsewd>`_: Wrap versions' list to look more consistent (`#3445 <https://github.com/rtfd/readthedocs.org/pull/3445>`_)
* `@agjohnson <http://github.com/agjohnson>`_: Move CDN code to external abstraction (`#2091 <https://github.com/rtfd/readthedocs.org/pull/2091>`_)

Version 2.4.0
-------------

:Date: May 31, 2018

* This fixes assets that were generated against old dependencies in 2.3.14
* `@agjohnson <http://github.com/agjohnson>`_: Fix issues with search javascript (`#4176 <https://github.com/rtfd/readthedocs.org/pull/4176>`_)
* `@stsewd <http://github.com/stsewd>`_: Use anonymous refs in CHANGELOG (`#4173 <https://github.com/rtfd/readthedocs.org/pull/4173>`_)
* `@stsewd <http://github.com/stsewd>`_: Fix some warnings on docs (`#4172 <https://github.com/rtfd/readthedocs.org/pull/4172>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Update the privacy policy date (`#4171 <https://github.com/rtfd/readthedocs.org/pull/4171>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Note about state and metro ad targeting (`#4169 <https://github.com/rtfd/readthedocs.org/pull/4169>`_)
* `@ericholscher <http://github.com/ericholscher>`_: Add another guide around fixing memory usage. (`#4168 <https://github.com/rtfd/readthedocs.org/pull/4168>`_)
* `@stsewd <http://github.com/stsewd>`_: Download raw build log (`#3585 <https://github.com/rtfd/readthedocs.org/pull/3585>`_)
* `@stsewd <http://github.com/stsewd>`_: Add "edit" and "view docs" buttons to subproject list (`#3572 <https://github.com/rtfd/readthedocs.org/pull/3572>`_)
* `@kennethlarsen <http://github.com/kennethlarsen>`_: Remove outline reset to bring back outline (`#3512 <https://github.com/rtfd/readthedocs.org/pull/3512>`_)

Version 2.3.14
--------------

:Date: May 30, 2018

* `@ericholscher <http://github.com/ericholscher>`__: Remove CSS override that doesn't exist. (`#4165 <https://github.com/rtfd/readthedocs.org/pull/4165>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Include a DMCA request template (`#4164 <https://github.com/rtfd/readthedocs.org/pull/4164>`__)
* `@davidfischer <http://github.com/davidfischer>`__: No CSRF cookie for docs pages (`#4153 <https://github.com/rtfd/readthedocs.org/pull/4153>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Small footer rework (`#4150 <https://github.com/rtfd/readthedocs.org/pull/4150>`__)
* `@stsewd <http://github.com/stsewd>`__: Fix prospector dependencies (`#4149 <https://github.com/rtfd/readthedocs.org/pull/4149>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Remove deploy directory which is unused. (`#4147 <https://github.com/rtfd/readthedocs.org/pull/4147>`__)
* `@stsewd <http://github.com/stsewd>`__: Use autosectionlabel extension (`#4146 <https://github.com/rtfd/readthedocs.org/pull/4146>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Add Intercom to the privacy policy (`#4145 <https://github.com/rtfd/readthedocs.org/pull/4145>`__)
* `@humitos <http://github.com/humitos>`__: Minimum refactor to decide_if_cors (`#4143 <https://github.com/rtfd/readthedocs.org/pull/4143>`__)
* `@stsewd <http://github.com/stsewd>`__: Ignore migrations from coverage report (`#4141 <https://github.com/rtfd/readthedocs.org/pull/4141>`__)
* `@stsewd <http://github.com/stsewd>`__: 5xx status in old webhooks (`#4139 <https://github.com/rtfd/readthedocs.org/pull/4139>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Fix with Lato Bold font (`#4138 <https://github.com/rtfd/readthedocs.org/pull/4138>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Release 2.3.13 (`#4137 <https://github.com/rtfd/readthedocs.org/pull/4137>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Build static assets (`#4136 <https://github.com/rtfd/readthedocs.org/pull/4136>`__)
* `@xrmx <http://github.com/xrmx>`__: oauth/services: correct error handling in paginate (`#4134 <https://github.com/rtfd/readthedocs.org/pull/4134>`__)
* `@xrmx <http://github.com/xrmx>`__: oauth/services: don't abuse log.exception (`#4133 <https://github.com/rtfd/readthedocs.org/pull/4133>`__)
* `@cedk <http://github.com/cedk>`__: Use quiet mode to retrieve branches from mercurial (`#4114 <https://github.com/rtfd/readthedocs.org/pull/4114>`__)
* `@humitos <http://github.com/humitos>`__: Add `has_valid_clone` and `has_valid_webhook` to ProjectAdminSerializer (`#4107 <https://github.com/rtfd/readthedocs.org/pull/4107>`__)
* `@stsewd <http://github.com/stsewd>`__: Put the rtd extension to the beginning of the list (`#4054 <https://github.com/rtfd/readthedocs.org/pull/4054>`__)
* `@stsewd <http://github.com/stsewd>`__: Use gitpython for tags (`#4052 <https://github.com/rtfd/readthedocs.org/pull/4052>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Do Not Track support (`#4046 <https://github.com/rtfd/readthedocs.org/pull/4046>`__)
* `@stsewd <http://github.com/stsewd>`__: Set urlconf to None after changing SUBDOMAIN setting (`#4032 <https://github.com/rtfd/readthedocs.org/pull/4032>`__)
* `@humitos <http://github.com/humitos>`__: Fix /404/ testing page (`#3976 <https://github.com/rtfd/readthedocs.org/pull/3976>`__)
* `@xrmx <http://github.com/xrmx>`__: Fix some tests with postgres (`#3958 <https://github.com/rtfd/readthedocs.org/pull/3958>`__)
* `@xrmx <http://github.com/xrmx>`__: Fixup DJANGO_SETTINGS_SKIP_LOCAL in tests (`#3899 <https://github.com/rtfd/readthedocs.org/pull/3899>`__)
* `@xrmx <http://github.com/xrmx>`__: templates: mark a few more strings for translations (`#3869 <https://github.com/rtfd/readthedocs.org/pull/3869>`__)
* `@ze <http://github.com/ze>`__: Make search bar in dashboard have a more clear message. (`#3844 <https://github.com/rtfd/readthedocs.org/pull/3844>`__)
* `@varunotelli <http://github.com/varunotelli>`__: Pointed users to Python3.6 (`#3817 <https://github.com/rtfd/readthedocs.org/pull/3817>`__)
* `@stsewd <http://github.com/stsewd>`__: [RDY] Fix tests for environment (`#3764 <https://github.com/rtfd/readthedocs.org/pull/3764>`__)
* `@ajatprabha <http://github.com/ajatprabha>`__: Ticket #3694: rename owners to maintainers (`#3703 <https://github.com/rtfd/readthedocs.org/pull/3703>`__)
* `@SanketDG <http://github.com/SanketDG>`__: Refactor to replace old logging to avoid mangling (`#3677 <https://github.com/rtfd/readthedocs.org/pull/3677>`__)
* `@stsewd <http://github.com/stsewd>`__: Add rstcheck to CI (`#3624 <https://github.com/rtfd/readthedocs.org/pull/3624>`__)
* `@techtonik <http://github.com/techtonik>`__: Update Git on prod (`#3615 <https://github.com/rtfd/readthedocs.org/pull/3615>`__)
* `@stsewd <http://github.com/stsewd>`__: Allow to hide version warning (`#3595 <https://github.com/rtfd/readthedocs.org/pull/3595>`__)
* `@cclauss <http://github.com/cclauss>`__: Modernize Python 2 code to get ready for Python 3 (`#3514 <https://github.com/rtfd/readthedocs.org/pull/3514>`__)
* `@stsewd <http://github.com/stsewd>`__: Consistent version format (`#3504 <https://github.com/rtfd/readthedocs.org/pull/3504>`__)

Version 2.3.13
--------------

:Date: May 23, 2018

* `@davidfischer <http://github.com/davidfischer>`__: Build static assets (`#4136 <https://github.com/rtfd/readthedocs.org/pull/4136>`__)
* `@stsewd <http://github.com/stsewd>`__: Don't sync _static dir for search builder (`#4120 <https://github.com/rtfd/readthedocs.org/pull/4120>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Use the latest Lato release (`#4093 <https://github.com/rtfd/readthedocs.org/pull/4093>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Update Gold Member marketing (`#4063 <https://github.com/rtfd/readthedocs.org/pull/4063>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Fix missing fonts (`#4060 <https://github.com/rtfd/readthedocs.org/pull/4060>`__)
* `@stsewd <http://github.com/stsewd>`__: Additional validation when changing the project language (`#3790 <https://github.com/rtfd/readthedocs.org/pull/3790>`__)
* `@stsewd <http://github.com/stsewd>`__: Improve yaml config docs (`#3685 <https://github.com/rtfd/readthedocs.org/pull/3685>`__)

Version 2.3.12
--------------

:Date: May 21, 2018

* `@stsewd <http://github.com/stsewd>`__: Remove Django deprecation warning (`#4112 <https://github.com/rtfd/readthedocs.org/pull/4112>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Display feature flags in the admin (`#4108 <https://github.com/rtfd/readthedocs.org/pull/4108>`__)
* `@humitos <http://github.com/humitos>`__: Set valid clone in project instance inside the version object also (`#4105 <https://github.com/rtfd/readthedocs.org/pull/4105>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Use the latest theme version in the default builder (`#4096 <https://github.com/rtfd/readthedocs.org/pull/4096>`__)
* `@humitos <http://github.com/humitos>`__: Use next field to redirect user when login is done by social (`#4083 <https://github.com/rtfd/readthedocs.org/pull/4083>`__)
* `@humitos <http://github.com/humitos>`__: Update the `documentation_type` when it's set to 'auto' (`#4080 <https://github.com/rtfd/readthedocs.org/pull/4080>`__)
* `@brainwane <http://github.com/brainwane>`__: Update link to license in philosophy document (`#4059 <https://github.com/rtfd/readthedocs.org/pull/4059>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Update local assets for theme to 0.3.1 tag (`#4047 <https://github.com/rtfd/readthedocs.org/pull/4047>`__)
* `@stsewd <http://github.com/stsewd>`__: Fix unbalanced div (`#4044 <https://github.com/rtfd/readthedocs.org/pull/4044>`__)
* `@stsewd <http://github.com/stsewd>`__: Remove haystack from code base (`#4039 <https://github.com/rtfd/readthedocs.org/pull/4039>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Subdomains use HTTPS if settings specify (`#3987 <https://github.com/rtfd/readthedocs.org/pull/3987>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Draft Privacy Policy (`#3978 <https://github.com/rtfd/readthedocs.org/pull/3978>`__)
* `@humitos <http://github.com/humitos>`__: Allow import Gitlab repo manually and set a webhook automatically (`#3934 <https://github.com/rtfd/readthedocs.org/pull/3934>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Enable ads on the readthedocs mkdocs theme (`#3922 <https://github.com/rtfd/readthedocs.org/pull/3922>`__)
* `@bansalnitish <http://github.com/bansalnitish>`__: Fixes #2953 - Url resolved with special characters (`#3725 <https://github.com/rtfd/readthedocs.org/pull/3725>`__)
* `@Jigar3 <http://github.com/Jigar3>`__: Deleted bookmarks app (`#3663 <https://github.com/rtfd/readthedocs.org/pull/3663>`__)

Version 2.3.11
--------------

:Date: May 01, 2018

* `@agjohnson <http://github.com/agjohnson>`__: Update local assets for theme to 0.3.1 tag (`#4047 <https://github.com/rtfd/readthedocs.org/pull/4047>`__)
* `@stsewd <http://github.com/stsewd>`__: Fix unbalanced div (`#4044 <https://github.com/rtfd/readthedocs.org/pull/4044>`__)
* `@stsewd <http://github.com/stsewd>`__: Remove haystack from code base (`#4039 <https://github.com/rtfd/readthedocs.org/pull/4039>`__)
* `@stsewd <http://github.com/stsewd>`__: Remove dead code from api v1 (`#4038 <https://github.com/rtfd/readthedocs.org/pull/4038>`__)
* `@humitos <http://github.com/humitos>`__: Bump sphinx default version to 1.7.4 (`#4035 <https://github.com/rtfd/readthedocs.org/pull/4035>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Detail where ads are shown (`#4031 <https://github.com/rtfd/readthedocs.org/pull/4031>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Make email verification optional for dev (`#4024 <https://github.com/rtfd/readthedocs.org/pull/4024>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Support sign in and sign up with GH/GL/BB (`#4022 <https://github.com/rtfd/readthedocs.org/pull/4022>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Remove old varnish purge utility function (`#4019 <https://github.com/rtfd/readthedocs.org/pull/4019>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Remove build queue length warning on build list page (`#4018 <https://github.com/rtfd/readthedocs.org/pull/4018>`__)
* `@stsewd <http://github.com/stsewd>`__: Don't check order on assertQuerysetEqual on tests for subprojects (`#4016 <https://github.com/rtfd/readthedocs.org/pull/4016>`__)
* `@stsewd <http://github.com/stsewd>`__: Tests for view docs api response (`#4014 <https://github.com/rtfd/readthedocs.org/pull/4014>`__)
* `@davidfischer <http://github.com/davidfischer>`__: MkDocs projects use RTD's analytics privacy improvements (`#4013 <https://github.com/rtfd/readthedocs.org/pull/4013>`__)
* `@humitos <http://github.com/humitos>`__: Release 2.3.10 (`#4009 <https://github.com/rtfd/readthedocs.org/pull/4009>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Remove typekit fonts (`#3982 <https://github.com/rtfd/readthedocs.org/pull/3982>`__)
* `@stsewd <http://github.com/stsewd>`__: Move dynamic-fixture to testing requirements (`#3956 <https://github.com/rtfd/readthedocs.org/pull/3956>`__)
* `@stsewd <http://github.com/stsewd>`__: Fix view docs link (`#3882 <https://github.com/rtfd/readthedocs.org/pull/3882>`__)
* `@stsewd <http://github.com/stsewd>`__: [WIP] Remove comments app (`#3802 <https://github.com/rtfd/readthedocs.org/pull/3802>`__)
* `@Jigar3 <http://github.com/Jigar3>`__: Deleted bookmarks app (`#3663 <https://github.com/rtfd/readthedocs.org/pull/3663>`__)

Version 2.3.10
--------------

:Date: April 24, 2018

* `@humitos <http://github.com/humitos>`__: Downgrade docker to 3.1.3 (`#4003 <https://github.com/rtfd/readthedocs.org/pull/4003>`__)

Version 2.3.9
-------------

:Date: April 20, 2018

* `@agjohnson <http://github.com/agjohnson>`__: Fix recursion problem more generally (`#3989 <https://github.com/rtfd/readthedocs.org/pull/3989>`__)

Version 2.3.8
-------------

:Date: April 20, 2018

* `@agjohnson <http://github.com/agjohnson>`__: Give TaskStep class knowledge of the underlying task (`#3983 <https://github.com/rtfd/readthedocs.org/pull/3983>`__)
* `@humitos <http://github.com/humitos>`__: Resolve domain when a project is a translation of itself (`#3981 <https://github.com/rtfd/readthedocs.org/pull/3981>`__)

Version 2.3.7
-------------

:Date: April 19, 2018

* `@humitos <http://github.com/humitos>`__: Fix server_error_500 path on single version (`#3975 <https://github.com/rtfd/readthedocs.org/pull/3975>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Fix bookmark app lint failures (`#3969 <https://github.com/rtfd/readthedocs.org/pull/3969>`__)
* `@humitos <http://github.com/humitos>`__: Use latest setuptools (39.0.1) by default on build process (`#3967 <https://github.com/rtfd/readthedocs.org/pull/3967>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Fix exact redirects. (`#3965 <https://github.com/rtfd/readthedocs.org/pull/3965>`__)
* `@humitos <http://github.com/humitos>`__: Make `resolve_domain` work when a project is subproject of itself (`#3962 <https://github.com/rtfd/readthedocs.org/pull/3962>`__)
* `@humitos <http://github.com/humitos>`__: Remove django-celery-beat and use the default scheduler (`#3959 <https://github.com/rtfd/readthedocs.org/pull/3959>`__)
* `@xrmx <http://github.com/xrmx>`__: Fix some tests with postgres (`#3958 <https://github.com/rtfd/readthedocs.org/pull/3958>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Add advertising details docs (`#3955 <https://github.com/rtfd/readthedocs.org/pull/3955>`__)
* `@humitos <http://github.com/humitos>`__: Use pur to upgrade python packages (`#3953 <https://github.com/rtfd/readthedocs.org/pull/3953>`__)
* `@ze <http://github.com/ze>`__: Make adjustments to Projects page (`#3948 <https://github.com/rtfd/readthedocs.org/pull/3948>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Small change to Chinese language names (`#3947 <https://github.com/rtfd/readthedocs.org/pull/3947>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Don't share state in build task (`#3946 <https://github.com/rtfd/readthedocs.org/pull/3946>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Fixed footer ad width fix (`#3944 <https://github.com/rtfd/readthedocs.org/pull/3944>`__)
* `@humitos <http://github.com/humitos>`__: Allow extend Translation and Subproject form logic from corporate (`#3937 <https://github.com/rtfd/readthedocs.org/pull/3937>`__)
* `@humitos <http://github.com/humitos>`__: Resync valid webhook for project manually imported (`#3935 <https://github.com/rtfd/readthedocs.org/pull/3935>`__)
* `@humitos <http://github.com/humitos>`__: Resync webhooks from Admin (`#3933 <https://github.com/rtfd/readthedocs.org/pull/3933>`__)
* `@humitos <http://github.com/humitos>`__: Fix attribute order call (`#3930 <https://github.com/rtfd/readthedocs.org/pull/3930>`__)
* `@humitos <http://github.com/humitos>`__: Mention RTD in the Project URL of the issue template (`#3928 <https://github.com/rtfd/readthedocs.org/pull/3928>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Correctly report mkdocs theme name (`#3920 <https://github.com/rtfd/readthedocs.org/pull/3920>`__)
* `@xrmx <http://github.com/xrmx>`__: Fixup DJANGO_SETTINGS_SKIP_LOCAL in tests (`#3899 <https://github.com/rtfd/readthedocs.org/pull/3899>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Show an adblock admonition in the dev console (`#3894 <https://github.com/rtfd/readthedocs.org/pull/3894>`__)
* `@stsewd <http://github.com/stsewd>`__: Fix view docs link (`#3882 <https://github.com/rtfd/readthedocs.org/pull/3882>`__)
* `@xrmx <http://github.com/xrmx>`__: templates: mark a few more strings for translations (`#3869 <https://github.com/rtfd/readthedocs.org/pull/3869>`__)
* `@ze <http://github.com/ze>`__: Update quickstart from README (`#3847 <https://github.com/rtfd/readthedocs.org/pull/3847>`__)
* `@vidartf <http://github.com/vidartf>`__: Fix page redirect preview (`#3811 <https://github.com/rtfd/readthedocs.org/pull/3811>`__)
* `@stsewd <http://github.com/stsewd>`__: [RDY] Fix requirements file lookup (`#3800 <https://github.com/rtfd/readthedocs.org/pull/3800>`__)
* `@aasis21 <http://github.com/aasis21>`__: Documentation for build notifications using webhooks. (`#3671 <https://github.com/rtfd/readthedocs.org/pull/3671>`__)
* `@mashrikt <http://github.com/mashrikt>`__: [#2967] Scheduled tasks for cleaning up messages (`#3604 <https://github.com/rtfd/readthedocs.org/pull/3604>`__)
* `@stsewd <http://github.com/stsewd>`__: Show URLS for exact redirect (`#3593 <https://github.com/rtfd/readthedocs.org/pull/3593>`__)
* `@marcelstoer <http://github.com/marcelstoer>`__: Doc builder template should check for mkdocs_page_input_path before using it (`#3536 <https://github.com/rtfd/readthedocs.org/pull/3536>`__)
* `@Code0x58 <http://github.com/Code0x58>`__: Document creation of slumber user (`#3461 <https://github.com/rtfd/readthedocs.org/pull/3461>`__)

Version 2.3.6
-------------

:Date: April 05, 2018

* `@agjohnson <http://github.com/agjohnson>`__: Drop readthedocs- prefix to submodule (`#3916 <https://github.com/rtfd/readthedocs.org/pull/3916>`__)
* `@agjohnson <http://github.com/agjohnson>`__: This fixes two bugs apparent in nesting of translations in subprojects (`#3909 <https://github.com/rtfd/readthedocs.org/pull/3909>`__)
* `@humitos <http://github.com/humitos>`__: Use new django celery beat scheduler (`#3908 <https://github.com/rtfd/readthedocs.org/pull/3908>`__)
* `@humitos <http://github.com/humitos>`__: Use a proper default for `docker` attribute on UpdateDocsTask (`#3907 <https://github.com/rtfd/readthedocs.org/pull/3907>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Handle errors from publish_parts (`#3905 <https://github.com/rtfd/readthedocs.org/pull/3905>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Drop pdbpp from testing requirements (`#3904 <https://github.com/rtfd/readthedocs.org/pull/3904>`__)
* `@stsewd <http://github.com/stsewd>`__: Little improve on sync_versions (`#3902 <https://github.com/rtfd/readthedocs.org/pull/3902>`__)
* `@humitos <http://github.com/humitos>`__: Save Docker image data in JSON file only for DockerBuildEnvironment (`#3897 <https://github.com/rtfd/readthedocs.org/pull/3897>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Single analytics file for all builders (`#3896 <https://github.com/rtfd/readthedocs.org/pull/3896>`__)
* `@humitos <http://github.com/humitos>`__: Organize logging levels (`#3893 <https://github.com/rtfd/readthedocs.org/pull/3893>`__)

Version 2.3.5
-------------

:Date: April 05, 2018

* `@agjohnson <http://github.com/agjohnson>`__: Drop pdbpp from testing requirements (`#3904 <https://github.com/rtfd/readthedocs.org/pull/3904>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Resolve subproject correctly in the case of single version (`#3901 <https://github.com/rtfd/readthedocs.org/pull/3901>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Fixed footer ads again (`#3895 <https://github.com/rtfd/readthedocs.org/pull/3895>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Fix an Alabaster ad positioning issue (`#3889 <https://github.com/rtfd/readthedocs.org/pull/3889>`__)
* `@humitos <http://github.com/humitos>`__: Save Docker image hash in RTD environment.json file (`#3880 <https://github.com/rtfd/readthedocs.org/pull/3880>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Add ref links for easier intersphinx on yaml config page (`#3877 <https://github.com/rtfd/readthedocs.org/pull/3877>`__)
* `@rajujha373 <http://github.com/rajujha373>`__: Typo correction in docs/features.rst (`#3872 <https://github.com/rtfd/readthedocs.org/pull/3872>`__)
* `@gaborbernat <http://github.com/gaborbernat>`__: add description for tox tasks (`#3868 <https://github.com/rtfd/readthedocs.org/pull/3868>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Another CORS hotfix for the sustainability API (`#3862 <https://github.com/rtfd/readthedocs.org/pull/3862>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Fix up some of the logic around repo and submodule URLs (`#3860 <https://github.com/rtfd/readthedocs.org/pull/3860>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Fix linting errors in tests (`#3855 <https://github.com/rtfd/readthedocs.org/pull/3855>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Use gitpython to find a commit reference (`#3843 <https://github.com/rtfd/readthedocs.org/pull/3843>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Remove pinned CSS Select version (`#3813 <https://github.com/rtfd/readthedocs.org/pull/3813>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Use JSONP for sustainability API (`#3789 <https://github.com/rtfd/readthedocs.org/pull/3789>`__)
* `@rajujha373 <http://github.com/rajujha373>`__: #3718: Added date to changelog (`#3788 <https://github.com/rtfd/readthedocs.org/pull/3788>`__)
* `@xrmx <http://github.com/xrmx>`__: tests: mock test_conf_file_not_found filesystem access (`#3740 <https://github.com/rtfd/readthedocs.org/pull/3740>`__)

.. _version-2.3.4:

Version 2.3.4
-------------

* Release for static assets

Version 2.3.3
-------------

* `@davidfischer <http://github.com/davidfischer>`__: Fix linting errors in tests (`#3855 <https://github.com/rtfd/readthedocs.org/pull/3855>`__)
* `@humitos <http://github.com/humitos>`__: Fix linting issues (`#3838 <https://github.com/rtfd/readthedocs.org/pull/3838>`__)
* `@humitos <http://github.com/humitos>`__: Update instance and model when `record_as_success` (`#3831 <https://github.com/rtfd/readthedocs.org/pull/3831>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Reorder GSOC projects, and note priority order (`#3823 <https://github.com/rtfd/readthedocs.org/pull/3823>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Add temporary method for skipping submodule checkout (`#3821 <https://github.com/rtfd/readthedocs.org/pull/3821>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Remove pinned CSS Select version (`#3813 <https://github.com/rtfd/readthedocs.org/pull/3813>`__)
* `@humitos <http://github.com/humitos>`__: Use readthedocs-common to share linting files accross different repos (`#3808 <https://github.com/rtfd/readthedocs.org/pull/3808>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Use JSONP for sustainability API (`#3789 <https://github.com/rtfd/readthedocs.org/pull/3789>`__)
* `@humitos <http://github.com/humitos>`__: Define useful celery beat task for development (`#3762 <https://github.com/rtfd/readthedocs.org/pull/3762>`__)
* `@humitos <http://github.com/humitos>`__: Auto-generate conf.py compatible with Py2 and Py3 (`#3745 <https://github.com/rtfd/readthedocs.org/pull/3745>`__)
* `@humitos <http://github.com/humitos>`__: Task to remove orphan symlinks (`#3543 <https://github.com/rtfd/readthedocs.org/pull/3543>`__)
* `@stsewd <http://github.com/stsewd>`__: Fix regex for public bitbucket repo (`#3533 <https://github.com/rtfd/readthedocs.org/pull/3533>`__)
* `@humitos <http://github.com/humitos>`__: Documentation for RTD context sent to the Sphinx theme (`#3490 <https://github.com/rtfd/readthedocs.org/pull/3490>`__)
* `@stsewd <http://github.com/stsewd>`__: Show link to docs on a build (`#3446 <https://github.com/rtfd/readthedocs.org/pull/3446>`__)

Version 2.3.2
-------------

This version adds a hotfix branch that adds model validation to the repository
URL to ensure strange URL patterns can't be used.

Version 2.3.1
-------------

* `@humitos <http://github.com/humitos>`__: Update instance and model when `record_as_success` (`#3831 <https://github.com/rtfd/readthedocs.org/pull/3831>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Bump docker -> 3.1.3 (`#3828 <https://github.com/rtfd/readthedocs.org/pull/3828>`__)
* `@Doug-AWS <http://github.com/Doug-AWS>`__: Pip install note for Windows (`#3827 <https://github.com/rtfd/readthedocs.org/pull/3827>`__)
* `@himanshutejwani12 <http://github.com/himanshutejwani12>`__: Update index.rst (`#3824 <https://github.com/rtfd/readthedocs.org/pull/3824>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Reorder GSOC projects, and note priority order (`#3823 <https://github.com/rtfd/readthedocs.org/pull/3823>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Autolint cleanup for #3821 (`#3822 <https://github.com/rtfd/readthedocs.org/pull/3822>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Add temporary method for skipping submodule checkout (`#3821 <https://github.com/rtfd/readthedocs.org/pull/3821>`__)
* `@stsewd <http://github.com/stsewd>`__: Pin astroid to fix linter issue on travis (`#3816 <https://github.com/rtfd/readthedocs.org/pull/3816>`__)
* `@varunotelli <http://github.com/varunotelli>`__: Update install.rst dropped the Python 2.7 only part (`#3814 <https://github.com/rtfd/readthedocs.org/pull/3814>`__)
* `@xrmx <http://github.com/xrmx>`__: Update machine field when activating a version from project_version_detail (`#3797 <https://github.com/rtfd/readthedocs.org/pull/3797>`__)
* `@humitos <http://github.com/humitos>`__: Allow members of "Admin" Team to wipe version envs (`#3791 <https://github.com/rtfd/readthedocs.org/pull/3791>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Add sustainability api to CORS (`#3782 <https://github.com/rtfd/readthedocs.org/pull/3782>`__)
* `@durwasa-chakraborty <http://github.com/durwasa-chakraborty>`__: Fixed a grammatical error (`#3780 <https://github.com/rtfd/readthedocs.org/pull/3780>`__)
* `@humitos <http://github.com/humitos>`__: Trying to solve the end line character for a font file (`#3776 <https://github.com/rtfd/readthedocs.org/pull/3776>`__)
* `@stsewd <http://github.com/stsewd>`__: Fix tox env for coverage (`#3772 <https://github.com/rtfd/readthedocs.org/pull/3772>`__)
* `@bansalnitish <http://github.com/bansalnitish>`__: Added eslint rules (`#3768 <https://github.com/rtfd/readthedocs.org/pull/3768>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Use sustainability api for advertising (`#3747 <https://github.com/rtfd/readthedocs.org/pull/3747>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Add a sustainability API (`#3672 <https://github.com/rtfd/readthedocs.org/pull/3672>`__)
* `@humitos <http://github.com/humitos>`__: Upgrade django-pagination to a "maintained" fork (`#3666 <https://github.com/rtfd/readthedocs.org/pull/3666>`__)
* `@humitos <http://github.com/humitos>`__: Project updated when subproject modified (`#3649 <https://github.com/rtfd/readthedocs.org/pull/3649>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Anonymize IP addresses for Google Analytics (`#3626 <https://github.com/rtfd/readthedocs.org/pull/3626>`__)
* `@humitos <http://github.com/humitos>`__: Improve "Sharing" docs (`#3472 <https://github.com/rtfd/readthedocs.org/pull/3472>`__)
* `@humitos <http://github.com/humitos>`__: Upgrade docker-py to its latest version (docker==3.1.1) (`#3243 <https://github.com/rtfd/readthedocs.org/pull/3243>`__)
* `@humitos <http://github.com/humitos>`__: Upgrade all packages using `pur` tool (`#2916 <https://github.com/rtfd/readthedocs.org/pull/2916>`__)
* `@rixx <http://github.com/rixx>`__: Fix page redirect preview (`#2711 <https://github.com/rtfd/readthedocs.org/pull/2711>`__)

.. _version-2.3.0:

Version 2.3.0
-------------

.. warning::
    Version 2.3.0 includes a security fix for project translations. See
    :ref:`security-2.3.0` for more information

* `@stsewd <http://github.com/stsewd>`__: Fix tox env for coverage (`#3772 <https://github.com/rtfd/readthedocs.org/pull/3772>`__)
* `@humitos <http://github.com/humitos>`__: Try to fix end of file (`#3761 <https://github.com/rtfd/readthedocs.org/pull/3761>`__)
* `@berkerpeksag <http://github.com/berkerpeksag>`__: Fix indentation in docs/faq.rst (`#3758 <https://github.com/rtfd/readthedocs.org/pull/3758>`__)
* `@stsewd <http://github.com/stsewd>`__: Check for http protocol before urlize (`#3755 <https://github.com/rtfd/readthedocs.org/pull/3755>`__)
* `@rajujha373 <http://github.com/rajujha373>`__: #3741: replaced Go Crazy text with Search (`#3752 <https://github.com/rtfd/readthedocs.org/pull/3752>`__)
* `@humitos <http://github.com/humitos>`__: Log in the proper place and add the image name used (`#3750 <https://github.com/rtfd/readthedocs.org/pull/3750>`__)
* `@shubham76 <http://github.com/shubham76>`__: Changed 'Submit' text on buttons with something more meaningful (`#3749 <https://github.com/rtfd/readthedocs.org/pull/3749>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Fix tests for Git submodule (`#3737 <https://github.com/rtfd/readthedocs.org/pull/3737>`__)
* `@bansalnitish <http://github.com/bansalnitish>`__: Add eslint rules and fix errors (`#3726 <https://github.com/rtfd/readthedocs.org/pull/3726>`__)
* `@davidfischer <http://github.com/davidfischer>`__: Prevent bots indexing promos (`#3719 <https://github.com/rtfd/readthedocs.org/pull/3719>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Add argument to skip errorlist through knockout on common form (`#3704 <https://github.com/rtfd/readthedocs.org/pull/3704>`__)
* `@ajatprabha <http://github.com/ajatprabha>`__: Fixed #3701: added closing tag for div element (`#3702 <https://github.com/rtfd/readthedocs.org/pull/3702>`__)
* `@bansalnitish <http://github.com/bansalnitish>`__: Fixes internal reference (`#3695 <https://github.com/rtfd/readthedocs.org/pull/3695>`__)
* `@humitos <http://github.com/humitos>`__: Always record the git branch command as success (`#3693 <https://github.com/rtfd/readthedocs.org/pull/3693>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Show the project slug in the project admin (to make it more explicit what project is what) (`#3681 <https://github.com/rtfd/readthedocs.org/pull/3681>`__)
* `@humitos <http://github.com/humitos>`__: Upgrade django-taggit to 0.22.2 (`#3667 <https://github.com/rtfd/readthedocs.org/pull/3667>`__)
* `@stsewd <http://github.com/stsewd>`__: Check for submodules (`#3661 <https://github.com/rtfd/readthedocs.org/pull/3661>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Hotfix for adding logging call back into project sync task (`#3657 <https://github.com/rtfd/readthedocs.org/pull/3657>`__)
* `@agjohnson <http://github.com/agjohnson>`__: Fix issue with missing setting in oauth SyncRepo task (`#3656 <https://github.com/rtfd/readthedocs.org/pull/3656>`__)
* `@ericholscher <http://github.com/ericholscher>`__: Remove error logging that isn't an error. (`#3650 <https://github.com/rtfd/readthedocs.org/pull/3650>`__)
* `@humitos <http://github.com/humitos>`__: Project updated when subproject modified (`#3649 <https://github.com/rtfd/readthedocs.org/pull/3649>`__)
* `@aasis21 <http://github.com/aasis21>`__: formatting buttons in edit project text editor (`#3633 <https://github.com/rtfd/readthedocs.org/pull/3633>`__)
* `@humitos <http://github.com/humitos>`__: Filter by my own repositories at Import Remote Project (`#3548 <https://github.com/rtfd/readthedocs.org/pull/3548>`__)
* `@funkyHat <http://github.com/funkyHat>`__: check for matching alias before subproject slug (`#2787 <https://github.com/rtfd/readthedocs.org/pull/2787>`__)

Version 2.2.1
-------------

Version ``2.2.1`` is a bug fix release for the several issues found in
production during the ``2.2.0`` release.

 * `@agjohnson <http://github.com/agjohnson>`__: Hotfix for adding logging call back into project sync task (`#3657 <https://github.com/rtfd/readthedocs.org/pull/3657>`__)
 * `@agjohnson <http://github.com/agjohnson>`__: Fix issue with missing setting in oauth SyncRepo task (`#3656 <https://github.com/rtfd/readthedocs.org/pull/3656>`__)
 * `@humitos <http://github.com/humitos>`__: Tests for build notifications (`#3654 <https://github.com/rtfd/readthedocs.org/pull/3654>`__)
 * `@humitos <http://github.com/humitos>`__: Send proper context to celery email notification task (`#3653 <https://github.com/rtfd/readthedocs.org/pull/3653>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Remove error logging that isn't an error. (`#3650 <https://github.com/rtfd/readthedocs.org/pull/3650>`__)
 * `@davidfischer <http://github.com/davidfischer>`__: Update RTD security docs (`#3641 <https://github.com/rtfd/readthedocs.org/pull/3641>`__)
 * `@humitos <http://github.com/humitos>`__: Ability to override the creation of the Celery App (`#3623 <https://github.com/rtfd/readthedocs.org/pull/3623>`__)

Version 2.2.0
-------------

 * `@humitos <http://github.com/humitos>`__: Tests for build notifications (`#3654 <https://github.com/rtfd/readthedocs.org/pull/3654>`__)
 * `@humitos <http://github.com/humitos>`__: Send proper context to celery email notification task (`#3653 <https://github.com/rtfd/readthedocs.org/pull/3653>`__)
 * `@xrmx <http://github.com/xrmx>`__: Update django-formtools to 2.1 (`#3648 <https://github.com/rtfd/readthedocs.org/pull/3648>`__)
 * `@xrmx <http://github.com/xrmx>`__: Update Django to 1.9.13 (`#3647 <https://github.com/rtfd/readthedocs.org/pull/3647>`__)
 * `@davidfischer <http://github.com/davidfischer>`__: Fix a 500 when searching for files with API v1 (`#3645 <https://github.com/rtfd/readthedocs.org/pull/3645>`__)
 * `@davidfischer <http://github.com/davidfischer>`__: Update RTD security docs (`#3641 <https://github.com/rtfd/readthedocs.org/pull/3641>`__)
 * `@humitos <http://github.com/humitos>`__: Fix SVN initialization for command logging (`#3638 <https://github.com/rtfd/readthedocs.org/pull/3638>`__)
 * `@humitos <http://github.com/humitos>`__: Ability to override the creation of the Celery App (`#3623 <https://github.com/rtfd/readthedocs.org/pull/3623>`__)
 * `@humitos <http://github.com/humitos>`__: Update the operations team (`#3621 <https://github.com/rtfd/readthedocs.org/pull/3621>`__)
 * `@mohitkyadav <http://github.com/mohitkyadav>`__: Add venv to .gitignore (`#3620 <https://github.com/rtfd/readthedocs.org/pull/3620>`__)
 * `@stsewd <http://github.com/stsewd>`__: Remove hardcoded copyright year (`#3616 <https://github.com/rtfd/readthedocs.org/pull/3616>`__)
 * `@stsewd <http://github.com/stsewd>`__: Improve installation steps (`#3614 <https://github.com/rtfd/readthedocs.org/pull/3614>`__)
 * `@stsewd <http://github.com/stsewd>`__: Update GSOC (`#3607 <https://github.com/rtfd/readthedocs.org/pull/3607>`__)
 * `@Jigar3 <http://github.com/Jigar3>`__: Updated AUTHORS.rst (`#3601 <https://github.com/rtfd/readthedocs.org/pull/3601>`__)
 * `@stsewd <http://github.com/stsewd>`__: Pin less to latest compatible version (`#3597 <https://github.com/rtfd/readthedocs.org/pull/3597>`__)
 * `@Angeles4four <http://github.com/Angeles4four>`__: Grammar correction (`#3596 <https://github.com/rtfd/readthedocs.org/pull/3596>`__)
 * `@davidfischer <http://github.com/davidfischer>`__: Fix an unclosed tag (`#3592 <https://github.com/rtfd/readthedocs.org/pull/3592>`__)
 * `@aaksarin <http://github.com/aaksarin>`__: add missed fontawesome-webfont.woff2 (`#3589 <https://github.com/rtfd/readthedocs.org/pull/3589>`__)
 * `@davidfischer <http://github.com/davidfischer>`__: Force a specific ad to be displayed (`#3584 <https://github.com/rtfd/readthedocs.org/pull/3584>`__)
 * `@stsewd <http://github.com/stsewd>`__: Docs about preference for tags over branches (`#3582 <https://github.com/rtfd/readthedocs.org/pull/3582>`__)
 * `@davidfischer <http://github.com/davidfischer>`__: Rework homepage (`#3579 <https://github.com/rtfd/readthedocs.org/pull/3579>`__)
 * `@stsewd <http://github.com/stsewd>`__: Don't allow to create a subproject of a project itself  (`#3571 <https://github.com/rtfd/readthedocs.org/pull/3571>`__)
 * `@davidfischer <http://github.com/davidfischer>`__: Fix for build screen in firefox (`#3569 <https://github.com/rtfd/readthedocs.org/pull/3569>`__)
 * `@humitos <http://github.com/humitos>`__: Style using pre-commit (`#3560 <https://github.com/rtfd/readthedocs.org/pull/3560>`__)
 * `@humitos <http://github.com/humitos>`__: Use DRF 3.1 `pagination_class` (`#3559 <https://github.com/rtfd/readthedocs.org/pull/3559>`__)
 * `@davidfischer <http://github.com/davidfischer>`__: Analytics fixes (`#3558 <https://github.com/rtfd/readthedocs.org/pull/3558>`__)
 * `@davidfischer <http://github.com/davidfischer>`__: Upgrade requests version (`#3557 <https://github.com/rtfd/readthedocs.org/pull/3557>`__)
 * `@humitos <http://github.com/humitos>`__: Mount `pip_cache_path` in Docker container (`#3556 <https://github.com/rtfd/readthedocs.org/pull/3556>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Add a number of new ideas for GSOC (`#3552 <https://github.com/rtfd/readthedocs.org/pull/3552>`__)
 * `@humitos <http://github.com/humitos>`__: Fix Travis lint issue (`#3551 <https://github.com/rtfd/readthedocs.org/pull/3551>`__)
 * `@davidfischer <http://github.com/davidfischer>`__: Send custom dimensions for mkdocs (`#3550 <https://github.com/rtfd/readthedocs.org/pull/3550>`__)
 * `@davidfischer <http://github.com/davidfischer>`__: Promo contrast improvements (`#3549 <https://github.com/rtfd/readthedocs.org/pull/3549>`__)
 * `@humitos <http://github.com/humitos>`__: Allow git tags with `/` in the name and properly slugify (`#3545 <https://github.com/rtfd/readthedocs.org/pull/3545>`__)
 * `@humitos <http://github.com/humitos>`__: Allow to import public repositories on corporate site (`#3537 <https://github.com/rtfd/readthedocs.org/pull/3537>`__)
 * `@humitos <http://github.com/humitos>`__: Log `git checkout` and expose to users (`#3520 <https://github.com/rtfd/readthedocs.org/pull/3520>`__)
 * `@stsewd <http://github.com/stsewd>`__: Update docs (`#3498 <https://github.com/rtfd/readthedocs.org/pull/3498>`__)
 * `@davidfischer <http://github.com/davidfischer>`__: Switch to universal analytics (`#3495 <https://github.com/rtfd/readthedocs.org/pull/3495>`__)
 * `@stsewd <http://github.com/stsewd>`__: Move Mercurial dependency to pip.txt (`#3488 <https://github.com/rtfd/readthedocs.org/pull/3488>`__)
 * `@agjohnson <http://github.com/agjohnson>`__: Add docs on removing edit button (`#3479 <https://github.com/rtfd/readthedocs.org/pull/3479>`__)
 * `@davidfischer <http://github.com/davidfischer>`__: Convert default dev cache to local memory (`#3477 <https://github.com/rtfd/readthedocs.org/pull/3477>`__)
 * `@agjohnson <http://github.com/agjohnson>`__: Fix lint error (`#3402 <https://github.com/rtfd/readthedocs.org/pull/3402>`__)
 * `@techtonik <http://github.com/techtonik>`__: Fix Edit links if version is referenced by annotated tag (`#3302 <https://github.com/rtfd/readthedocs.org/pull/3302>`__)
 * `@jaraco <http://github.com/jaraco>`__: Fixed build results page on firefox (part two) (`#2630 <https://github.com/rtfd/readthedocs.org/pull/2630>`__)

Version 2.1.6
-------------

 * `@davidfischer <http://github.com/davidfischer>`__: Promo contrast improvements (`#3549 <https://github.com/rtfd/readthedocs.org/pull/3549>`__)
 * `@humitos <http://github.com/humitos>`__: Refactor run command outside a Build and Environment (`#3542 <https://github.com/rtfd/readthedocs.org/issues/3542>`__)
 * `@AnatoliyURL <http://github.com/AnatoliyURL>`__: Project in the local read the docs don't see tags. (`#3534 <https://github.com/rtfd/readthedocs.org/issues/3534>`__)
 * `@malarzm <http://github.com/malarzm>`__: searchtools.js missing init() call (`#3532 <https://github.com/rtfd/readthedocs.org/issues/3532>`__)
 * `@johanneskoester <http://github.com/johanneskoester>`__: Build failed without details (`#3531 <https://github.com/rtfd/readthedocs.org/issues/3531>`__)
 * `@danielmitterdorfer <http://github.com/danielmitterdorfer>`__: "Edit on Github" points to non-existing commit (`#3530 <https://github.com/rtfd/readthedocs.org/issues/3530>`__)
 * `@lk-geimfari <http://github.com/lk-geimfari>`__: No such file or directory: 'docs/requirements.txt' (`#3529 <https://github.com/rtfd/readthedocs.org/issues/3529>`__)
 * `@stsewd <http://github.com/stsewd>`__: Fix Good First Issue link (`#3522 <https://github.com/rtfd/readthedocs.org/pull/3522>`__)
 * `@Blendify <http://github.com/Blendify>`__: Remove RTD Theme workaround (`#3519 <https://github.com/rtfd/readthedocs.org/pull/3519>`__)
 * `@stsewd <http://github.com/stsewd>`__: Move project description to the top (`#3510 <https://github.com/rtfd/readthedocs.org/pull/3510>`__)
 * `@davidfischer <http://github.com/davidfischer>`__: Switch to universal analytics (`#3495 <https://github.com/rtfd/readthedocs.org/pull/3495>`__)
 * `@davidfischer <http://github.com/davidfischer>`__: Convert default dev cache to local memory (`#3477 <https://github.com/rtfd/readthedocs.org/pull/3477>`__)
 * `@nlgranger <http://github.com/nlgranger>`__: Github service: cannot unlink after deleting account (`#3374 <https://github.com/rtfd/readthedocs.org/issues/3374>`__)
 * `@andrewgodwin <http://github.com/andrewgodwin>`__: "stable" appearing to track future release branches (`#3268 <https://github.com/rtfd/readthedocs.org/issues/3268>`__)
 * `@skddc <http://github.com/skddc>`__: Add JSDoc to docs build environment (`#3069 <https://github.com/rtfd/readthedocs.org/issues/3069>`__)
 * `@chummels <http://github.com/chummels>`__: RTD building old "stable" docs instead of "latest" when auto-triggered from recent push (`#2351 <https://github.com/rtfd/readthedocs.org/issues/2351>`__)
 * `@cajus <http://github.com/cajus>`__: Builds get stuck in "Cloning" state (`#2047 <https://github.com/rtfd/readthedocs.org/issues/2047>`__)
 * `@gossi <http://github.com/gossi>`__: Cannot delete subproject (`#1341 <https://github.com/rtfd/readthedocs.org/issues/1341>`__)
 * `@gigster99 <http://github.com/gigster99>`__: extension problem (`#1059 <https://github.com/rtfd/readthedocs.org/issues/1059>`__)

Version 2.1.5
-------------

 * `@ericholscher <http://github.com/ericholscher>`__: Add GSOC 2018 page (`#3518 <https://github.com/rtfd/readthedocs.org/pull/3518>`__)
 * `@stsewd <http://github.com/stsewd>`__: Move project description to the top (`#3510 <https://github.com/rtfd/readthedocs.org/pull/3510>`__)
 * `@RichardLitt <http://github.com/RichardLitt>`__: Docs: Rename "Good First Bug" to "Good First Issue" (`#3505 <https://github.com/rtfd/readthedocs.org/pull/3505>`__)
 * `@stsewd <http://github.com/stsewd>`__: Fix regex for getting project and user (`#3501 <https://github.com/rtfd/readthedocs.org/pull/3501>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Check to make sure changes exist in BitBucket pushes (`#3480 <https://github.com/rtfd/readthedocs.org/pull/3480>`__)
 * `@andrewgodwin <http://github.com/andrewgodwin>`__: "stable" appearing to track future release branches (`#3268 <https://github.com/rtfd/readthedocs.org/issues/3268>`__)
 * `@cdeil <http://github.com/cdeil>`__: No module named pip in conda build (`#2827 <https://github.com/rtfd/readthedocs.org/issues/2827>`__)
 * `@Yaseenh <http://github.com/Yaseenh>`__: building project does not generate new pdf with changes in it (`#2758 <https://github.com/rtfd/readthedocs.org/issues/2758>`__)
 * `@chummels <http://github.com/chummels>`__: RTD building old "stable" docs instead of "latest" when auto-triggered from recent push (`#2351 <https://github.com/rtfd/readthedocs.org/issues/2351>`__)
 * `@KeithWoods <http://github.com/KeithWoods>`__: GitHub edit link is aggressively stripped (`#1788 <https://github.com/rtfd/readthedocs.org/issues/1788>`__)

Version 2.1.4
-------------

 * `@davidfischer <http://github.com/davidfischer>`__: Add programming language to API/READTHEDOCS_DATA (`#3499 <https://github.com/rtfd/readthedocs.org/pull/3499>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Remove our mkdocs search override (`#3496 <https://github.com/rtfd/readthedocs.org/pull/3496>`__)
 * `@humitos <http://github.com/humitos>`__: Better style (`#3494 <https://github.com/rtfd/readthedocs.org/pull/3494>`__)
 * `@humitos <http://github.com/humitos>`__: Update README.rst (`#3492 <https://github.com/rtfd/readthedocs.org/pull/3492>`__)
 * `@davidfischer <http://github.com/davidfischer>`__: Small formatting change to the Alabaster footer (`#3491 <https://github.com/rtfd/readthedocs.org/pull/3491>`__)
 * `@matsen <http://github.com/matsen>`__: Fixing "reseting" misspelling. (`#3487 <https://github.com/rtfd/readthedocs.org/pull/3487>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Add David to dev team listing (`#3485 <https://github.com/rtfd/readthedocs.org/pull/3485>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Check to make sure changes exist in BitBucket pushes (`#3480 <https://github.com/rtfd/readthedocs.org/pull/3480>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Use semvar for readthedocs-build to make bumping easier (`#3475 <https://github.com/rtfd/readthedocs.org/pull/3475>`__)
 * `@davidfischer <http://github.com/davidfischer>`__: Add programming languages (`#3471 <https://github.com/rtfd/readthedocs.org/pull/3471>`__)
 * `@humitos <http://github.com/humitos>`__: Remove TEMPLATE_LOADERS since it's the default (`#3469 <https://github.com/rtfd/readthedocs.org/pull/3469>`__)
 * `@Code0x58 <http://github.com/Code0x58>`__: Minor virtualenv upgrade (`#3463 <https://github.com/rtfd/readthedocs.org/pull/3463>`__)
 * `@humitos <http://github.com/humitos>`__: Remove invite only message (`#3456 <https://github.com/rtfd/readthedocs.org/pull/3456>`__)
 * `@maxirus <http://github.com/maxirus>`__: Adding to Install Docs (`#3455 <https://github.com/rtfd/readthedocs.org/pull/3455>`__)
 * `@stsewd <http://github.com/stsewd>`__: Fix a little typo (`#3448 <https://github.com/rtfd/readthedocs.org/pull/3448>`__)
 * `@stsewd <http://github.com/stsewd>`__: Better autogenerated index file (`#3447 <https://github.com/rtfd/readthedocs.org/pull/3447>`__)
 * `@stsewd <http://github.com/stsewd>`__: Better help text for privacy level (`#3444 <https://github.com/rtfd/readthedocs.org/pull/3444>`__)
 * `@msyriac <http://github.com/msyriac>`__: Broken link URL changed fixes #3442 (`#3443 <https://github.com/rtfd/readthedocs.org/pull/3443>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Fix git (`#3441 <https://github.com/rtfd/readthedocs.org/pull/3441>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Properly slugify the alias on Project Relationships. (`#3440 <https://github.com/rtfd/readthedocs.org/pull/3440>`__)
 * `@stsewd <http://github.com/stsewd>`__: Don't show "build ideas" to unprivileged users (`#3439 <https://github.com/rtfd/readthedocs.org/pull/3439>`__)
 * `@Blendify <http://github.com/Blendify>`__: Docs: Point Theme docs to new website (`#3438 <https://github.com/rtfd/readthedocs.org/pull/3438>`__)
 * `@humitos <http://github.com/humitos>`__: Do not use double quotes on git command with --format option (`#3437 <https://github.com/rtfd/readthedocs.org/pull/3437>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Hack in a fix for missing version slug deploy that went out a while back (`#3433 <https://github.com/rtfd/readthedocs.org/pull/3433>`__)
 * `@humitos <http://github.com/humitos>`__: Check versions used to create the venv and auto-wipe (`#3432 <https://github.com/rtfd/readthedocs.org/pull/3432>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Upgrade psycopg2 (`#3429 <https://github.com/rtfd/readthedocs.org/pull/3429>`__)
 * `@humitos <http://github.com/humitos>`__: Fix "Edit in Github" link (`#3427 <https://github.com/rtfd/readthedocs.org/pull/3427>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Add celery theme to supported ad options (`#3425 <https://github.com/rtfd/readthedocs.org/pull/3425>`__)
 * `@humitos <http://github.com/humitos>`__: Link to version detail page from build detail page (`#3418 <https://github.com/rtfd/readthedocs.org/pull/3418>`__)
 * `@humitos <http://github.com/humitos>`__: Move wipe button to version detail page (`#3417 <https://github.com/rtfd/readthedocs.org/pull/3417>`__)
 * `@humitos <http://github.com/humitos>`__: Show/Hide "See paid advertising" checkbox depending on USE_PROMOS (`#3412 <https://github.com/rtfd/readthedocs.org/pull/3412>`__)
 * `@benjaoming <http://github.com/benjaoming>`__: Strip well-known version component origin/ from remote version (`#3377 <https://github.com/rtfd/readthedocs.org/pull/3377>`__)
 * `@humitos <http://github.com/humitos>`__: Remove warnings from code (`#3372 <https://github.com/rtfd/readthedocs.org/pull/3372>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Add docker image from the YAML config integration (`#3339 <https://github.com/rtfd/readthedocs.org/pull/3339>`__)
 * `@humitos <http://github.com/humitos>`__: Show proper error to user when conf.py is not found (`#3326 <https://github.com/rtfd/readthedocs.org/pull/3326>`__)
 * `@humitos <http://github.com/humitos>`__: Simple task to finish inactive builds (`#3312 <https://github.com/rtfd/readthedocs.org/pull/3312>`__)
 * `@techtonik <http://github.com/techtonik>`__: Fix Edit links if version is referenced by annotated tag (`#3302 <https://github.com/rtfd/readthedocs.org/pull/3302>`__)
 * `@Riyuzakii <http://github.com/Riyuzakii>`__: changed <strong> from html to css (`#2699 <https://github.com/rtfd/readthedocs.org/pull/2699>`__)

Version 2.1.3
-------------

:date: Dec 21, 2017

 * `@ericholscher <http://github.com/ericholscher>`__: Upgrade psycopg2 (`#3429 <https://github.com/rtfd/readthedocs.org/pull/3429>`__)
 * `@humitos <http://github.com/humitos>`__: Fix "Edit in Github" link (`#3427 <https://github.com/rtfd/readthedocs.org/pull/3427>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Add celery theme to supported ad options (`#3425 <https://github.com/rtfd/readthedocs.org/pull/3425>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Only build travis push builds on master. (`#3421 <https://github.com/rtfd/readthedocs.org/pull/3421>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Add concept of dashboard analytics code (`#3420 <https://github.com/rtfd/readthedocs.org/pull/3420>`__)
 * `@humitos <http://github.com/humitos>`__: Use default avatar for User/Orgs in OAuth services (`#3419 <https://github.com/rtfd/readthedocs.org/pull/3419>`__)
 * `@humitos <http://github.com/humitos>`__: Link to version detail page from build detail page (`#3418 <https://github.com/rtfd/readthedocs.org/pull/3418>`__)
 * `@humitos <http://github.com/humitos>`__: Move wipe button to version detail page (`#3417 <https://github.com/rtfd/readthedocs.org/pull/3417>`__)
 * `@bieagrathara <http://github.com/bieagrathara>`__: 019 497 8360 (`#3416 <https://github.com/rtfd/readthedocs.org/issues/3416>`__)
 * `@bieagrathara <http://github.com/bieagrathara>`__: rew (`#3415 <https://github.com/rtfd/readthedocs.org/issues/3415>`__)
 * `@tony <http://github.com/tony>`__: lint prospector task failing (`#3414 <https://github.com/rtfd/readthedocs.org/issues/3414>`__)
 * `@humitos <http://github.com/humitos>`__: Remove extra 's' (`#3413 <https://github.com/rtfd/readthedocs.org/pull/3413>`__)
 * `@humitos <http://github.com/humitos>`__: Show/Hide "See paid advertising" checkbox depending on USE_PROMOS (`#3412 <https://github.com/rtfd/readthedocs.org/pull/3412>`__)
 * `@accraze <http://github.com/accraze>`__: Removing talks about RTD page (`#3410 <https://github.com/rtfd/readthedocs.org/pull/3410>`__)
 * `@humitos <http://github.com/humitos>`__: Pin pylint to 1.7.5 and fix docstring styling (`#3408 <https://github.com/rtfd/readthedocs.org/pull/3408>`__)
 * `@agjohnson <http://github.com/agjohnson>`__: Update style and copy on abandonment docs (`#3406 <https://github.com/rtfd/readthedocs.org/pull/3406>`__)
 * `@agjohnson <http://github.com/agjohnson>`__: Update changelog more consistently (`#3405 <https://github.com/rtfd/readthedocs.org/pull/3405>`__)
 * `@agjohnson <http://github.com/agjohnson>`__: Update prerelease invoke command to call with explicit path (`#3404 <https://github.com/rtfd/readthedocs.org/pull/3404>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Fix changelog command (`#3403 <https://github.com/rtfd/readthedocs.org/pull/3403>`__)
 * `@agjohnson <http://github.com/agjohnson>`__: Fix lint error (`#3402 <https://github.com/rtfd/readthedocs.org/pull/3402>`__)
 * `@julienmalard <http://github.com/julienmalard>`__: Recent builds are missing translated languages links (`#3401 <https://github.com/rtfd/readthedocs.org/issues/3401>`__)
 * `@stsewd <http://github.com/stsewd>`__: Remove copyright application (`#3400 <https://github.com/rtfd/readthedocs.org/pull/3400>`__)
 * `@humitos <http://github.com/humitos>`__: Show connect buttons for installed apps only (`#3394 <https://github.com/rtfd/readthedocs.org/pull/3394>`__)
 * `@agjohnson <http://github.com/agjohnson>`__: Fix display of build advice (`#3390 <https://github.com/rtfd/readthedocs.org/issues/3390>`__)
 * `@agjohnson <http://github.com/agjohnson>`__: Don't display the build suggestions div if there are no suggestions (`#3389 <https://github.com/rtfd/readthedocs.org/pull/3389>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Pass more data into the redirects. (`#3388 <https://github.com/rtfd/readthedocs.org/pull/3388>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Fix issue where you couldn't edit your canonical domain. (`#3387 <https://github.com/rtfd/readthedocs.org/pull/3387>`__)
 * `@benjaoming <http://github.com/benjaoming>`__: Strip well-known version component origin/ from remote version (`#3377 <https://github.com/rtfd/readthedocs.org/pull/3377>`__)
 * `@humitos <http://github.com/humitos>`__: Remove warnings from code (`#3372 <https://github.com/rtfd/readthedocs.org/pull/3372>`__)
 * `@JavaDevVictoria <http://github.com/JavaDevVictoria>`__: Updated python.setup_py_install to be true (`#3357 <https://github.com/rtfd/readthedocs.org/pull/3357>`__)
 * `@humitos <http://github.com/humitos>`__: Use default avatars for GitLab/GitHub/Bitbucket integrations (users/organizations) (`#3353 <https://github.com/rtfd/readthedocs.org/issues/3353>`__)
 * `@jonrkarr <http://github.com/jonrkarr>`__: Error in YAML configuration docs: default value for `python.setup_py_install` should be `true` (`#3334 <https://github.com/rtfd/readthedocs.org/issues/3334>`__)
 * `@humitos <http://github.com/humitos>`__: Show proper error to user when conf.py is not found (`#3326 <https://github.com/rtfd/readthedocs.org/pull/3326>`__)
 * `@MikeHart85 <http://github.com/MikeHart85>`__: Badges aren't updating due to being cached on GitHub. (`#3323 <https://github.com/rtfd/readthedocs.org/issues/3323>`__)
 * `@humitos <http://github.com/humitos>`__: Simple task to finish inactive builds (`#3312 <https://github.com/rtfd/readthedocs.org/pull/3312>`__)
 * `@techtonik <http://github.com/techtonik>`__: Fix Edit links if version is referenced by annotated tag (`#3302 <https://github.com/rtfd/readthedocs.org/pull/3302>`__)
 * `@humitos <http://github.com/humitos>`__: Remove/Update talks about RTD page (`#3283 <https://github.com/rtfd/readthedocs.org/issues/3283>`__)
 * `@gawel <http://github.com/gawel>`__: Regain pyquery project ownership (`#3281 <https://github.com/rtfd/readthedocs.org/issues/3281>`__)
 * `@dialex <http://github.com/dialex>`__: Build passed but I can't see the documentation (maze screen) (`#3246 <https://github.com/rtfd/readthedocs.org/issues/3246>`__)
 * `@makixx <http://github.com/makixx>`__: Account is inactive (`#3241 <https://github.com/rtfd/readthedocs.org/issues/3241>`__)
 * `@agjohnson <http://github.com/agjohnson>`__: Cleanup misreported failed builds (`#3230 <https://github.com/rtfd/readthedocs.org/issues/3230>`__)
 * `@cokelaer <http://github.com/cokelaer>`__: links to github are broken (`#3203 <https://github.com/rtfd/readthedocs.org/issues/3203>`__)
 * `@agjohnson <http://github.com/agjohnson>`__: Remove copyright application (`#3199 <https://github.com/rtfd/readthedocs.org/issues/3199>`__)
 * `@shacharoo <http://github.com/shacharoo>`__: Unable to register after deleting my account (`#3189 <https://github.com/rtfd/readthedocs.org/issues/3189>`__)
 * `@gtalarico <http://github.com/gtalarico>`__: 3 week old Build Stuck Cloning  (`#3126 <https://github.com/rtfd/readthedocs.org/issues/3126>`__)
 * `@agjohnson <http://github.com/agjohnson>`__: Regressions with conf.py and error reporting (`#2963 <https://github.com/rtfd/readthedocs.org/issues/2963>`__)
 * `@agjohnson <http://github.com/agjohnson>`__: Can't edit canonical domain (`#2922 <https://github.com/rtfd/readthedocs.org/issues/2922>`__)
 * `@virtuald <http://github.com/virtuald>`__: Documentation stuck in 'cloning' state (`#2795 <https://github.com/rtfd/readthedocs.org/issues/2795>`__)
 * `@Riyuzakii <http://github.com/Riyuzakii>`__: changed <strong> from html to css (`#2699 <https://github.com/rtfd/readthedocs.org/pull/2699>`__)
 * `@tjanez <http://github.com/tjanez>`__: Support specifying 'python setup.py build_sphinx' as an alternative build command (`#1857 <https://github.com/rtfd/readthedocs.org/issues/1857>`__)
 * `@bdarnell <http://github.com/bdarnell>`__: Broken edit links (`#1637 <https://github.com/rtfd/readthedocs.org/issues/1637>`__)

Version 2.1.2
-------------

 * `@agjohnson <http://github.com/agjohnson>`__: Update changelog more consistently (`#3405 <https://github.com/rtfd/readthedocs.org/pull/3405>`__)
 * `@agjohnson <http://github.com/agjohnson>`__: Update prerelease invoke command to call with explicit path (`#3404 <https://github.com/rtfd/readthedocs.org/pull/3404>`__)
 * `@agjohnson <http://github.com/agjohnson>`__: Fix lint error (`#3402 <https://github.com/rtfd/readthedocs.org/pull/3402>`__)
 * `@stsewd <http://github.com/stsewd>`__: Remove copyright application (`#3400 <https://github.com/rtfd/readthedocs.org/pull/3400>`__)
 * `@humitos <http://github.com/humitos>`__: Show connect buttons for installed apps only (`#3394 <https://github.com/rtfd/readthedocs.org/pull/3394>`__)
 * `@agjohnson <http://github.com/agjohnson>`__: Don't display the build suggestions div if there are no suggestions (`#3389 <https://github.com/rtfd/readthedocs.org/pull/3389>`__)
 * `@jonrkarr <http://github.com/jonrkarr>`__: Error in YAML configuration docs: default value for `python.setup_py_install` should be `true` (`#3334 <https://github.com/rtfd/readthedocs.org/issues/3334>`__)
 * `@humitos <http://github.com/humitos>`__: Simple task to finish inactive builds (`#3312 <https://github.com/rtfd/readthedocs.org/pull/3312>`__)
 * `@agjohnson <http://github.com/agjohnson>`__: Cleanup misreported failed builds (`#3230 <https://github.com/rtfd/readthedocs.org/issues/3230>`__)
 * `@agjohnson <http://github.com/agjohnson>`__: Remove copyright application (`#3199 <https://github.com/rtfd/readthedocs.org/issues/3199>`__)

Version 2.1.1
-------------

Release information missing

Version 2.1.0
-------------

 * `@ericholscher <http://github.com/ericholscher>`__: Revert "Merge pull request #3336 from rtfd/use-active-for-stable" (`#3368 <https://github.com/rtfd/readthedocs.org/pull/3368>`__)
 * `@agjohnson <http://github.com/agjohnson>`__: Revert "Do not split before first argument (#3333)" (`#3366 <https://github.com/rtfd/readthedocs.org/pull/3366>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Remove pitch from ethical ads page, point folks to actual pitch page. (`#3365 <https://github.com/rtfd/readthedocs.org/pull/3365>`__)
 * `@agjohnson <http://github.com/agjohnson>`__: Add changelog and changelog automation (`#3364 <https://github.com/rtfd/readthedocs.org/pull/3364>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Fix mkdocs search. (`#3361 <https://github.com/rtfd/readthedocs.org/pull/3361>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Email sending: Allow kwargs for other options (`#3355 <https://github.com/rtfd/readthedocs.org/pull/3355>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Try and get folks to put more tags. (`#3350 <https://github.com/rtfd/readthedocs.org/pull/3350>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Suggest wiping your environment to folks with bad build outcomes. (`#3347 <https://github.com/rtfd/readthedocs.org/pull/3347>`__)
 * `@humitos <http://github.com/humitos>`__: GitLab Integration (`#3327 <https://github.com/rtfd/readthedocs.org/pull/3327>`__)
 * `@jimfulton <http://github.com/jimfulton>`__: Draft policy for claiming existing project names. (`#3314 <https://github.com/rtfd/readthedocs.org/pull/3314>`__)
 * `@agjohnson <http://github.com/agjohnson>`__: More logic changes to error reporting, cleanup (`#3310 <https://github.com/rtfd/readthedocs.org/pull/3310>`__)
 * `@safwanrahman <http://github.com/safwanrahman>`__: [Fix #3182] Better user deletion (`#3214 <https://github.com/rtfd/readthedocs.org/pull/3214>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Better User deletion (`#3182 <https://github.com/rtfd/readthedocs.org/issues/3182>`__)
 * `@RichardLitt <http://github.com/RichardLitt>`__: Add `Needed: replication` label (`#3138 <https://github.com/rtfd/readthedocs.org/pull/3138>`__)
 * `@josejrobles <http://github.com/josejrobles>`__: Replaced usage of deprecated function get_fields_with_model with new … (`#3052 <https://github.com/rtfd/readthedocs.org/pull/3052>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Don't delete the subprojects directory on sync of superproject (`#3042 <https://github.com/rtfd/readthedocs.org/pull/3042>`__)
 * `@andrew <http://github.com/andrew>`__: Pass query string when redirecting, fixes #2595 (`#3001 <https://github.com/rtfd/readthedocs.org/pull/3001>`__)
 * `@saily <http://github.com/saily>`__: Add GitLab repo sync and webhook support (`#1870 <https://github.com/rtfd/readthedocs.org/pull/1870>`__)
 * `@destroyerofbuilds <http://github.com/destroyerofbuilds>`__: Setup GitLab Web Hook on Project Import (`#1443 <https://github.com/rtfd/readthedocs.org/issues/1443>`__)
 * `@takotuesday <http://github.com/takotuesday>`__: Add GitLab Provider from django-allauth (`#1441 <https://github.com/rtfd/readthedocs.org/issues/1441>`__)

Version 2.0
-----------

 * `@ericholscher <http://github.com/ericholscher>`__: Email sending: Allow kwargs for other options (`#3355 <https://github.com/rtfd/readthedocs.org/pull/3355>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Try and get folks to put more tags. (`#3350 <https://github.com/rtfd/readthedocs.org/pull/3350>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Small changes to email sending to enable from email (`#3349 <https://github.com/rtfd/readthedocs.org/pull/3349>`__)
 * `@dplanella <http://github.com/dplanella>`__: Duplicate TOC entries (`#3345 <https://github.com/rtfd/readthedocs.org/issues/3345>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Small tweaks to ethical ads page (`#3344 <https://github.com/rtfd/readthedocs.org/pull/3344>`__)
 * `@agjohnson <http://github.com/agjohnson>`__: Fix python usage around oauth pagination (`#3342 <https://github.com/rtfd/readthedocs.org/pull/3342>`__)
 * `@tony <http://github.com/tony>`__: Fix isort link (`#3340 <https://github.com/rtfd/readthedocs.org/pull/3340>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Change stable version switching to respect `active` (`#3336 <https://github.com/rtfd/readthedocs.org/pull/3336>`__)
 * `@ericholscher <http://github.com/ericholscher>`__: Allow superusers to pass admin & member tests for projects (`#3335 <https://github.com/rtfd/readthedocs.org/pull/3335>`__)
 * `@humitos <http://github.com/humitos>`__: Do not split before first argument (`#3333 <https://github.com/rtfd/readthedocs.org/pull/3333>`__)
 * `@humitos <http://github.com/humitos>`__: Update docs for pre-commit (auto linting) (`#3332 <https://github.com/rtfd/readthedocs.org/pull/3332>`__)
 * `@humitos <http://github.com/humitos>`__: Take preferece of tags over branches when selecting the stable version (`#3331 <https://github.com/rtfd/readthedocs.org/pull/3331>`__)
 * `@humitos <http://github.com/humitos>`__: Add prospector as a pre-commit hook (`#3328 <https://github.com/rtfd/readthedocs.org/pull/3328>`__)
 * `@andrewgodwin <http://github.com/andrewgodwin>`__: "stable" appearing to track future release branches (`#3268 <https://github.com/rtfd/readthedocs.org/issues/3268>`__)
 * `@humitos <http://github.com/humitos>`__: Config files for auto linting (`#3264 <https://github.com/rtfd/readthedocs.org/pull/3264>`__)
 * `@mekrip <http://github.com/mekrip>`__: Build is not working (`#3223 <https://github.com/rtfd/readthedocs.org/issues/3223>`__)
 * `@skddc <http://github.com/skddc>`__: Add JSDoc to docs build environment (`#3069 <https://github.com/rtfd/readthedocs.org/issues/3069>`__)
 * `@jakirkham <http://github.com/jakirkham>`__: Specifying conda version used (`#2076 <https://github.com/rtfd/readthedocs.org/issues/2076>`__)
 * `@agjohnson <http://github.com/agjohnson>`__: Document code style guidelines (`#1475 <https://github.com/rtfd/readthedocs.org/issues/1475>`__)
