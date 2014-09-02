API V2
======

This will be the new verison of the Read the Docs API.
The goal will be to enable users a wide range of functionality for interacting with the site via program.

You should be able to use the API to accomplish all tasks within the project admin.
You shoudl be able to create new builds.

Tech
----

We will use Django REST Framework

Auth
----

* Basic Auth
* Token Auth (Oauth)

Tasks
-----

* Manage all Admin-style information via API
	* Settings
	* Versions
	* Maintainers
	* Access Tokens
	* Redirects
	* Translations
	* Subprojects
	* Notifications
* Get Public Project information
	* Active Versions
	* Build Information
	* Downloads
	* Search
* Get User information
	* User activity
* Trigger a new build
* Page-level information
	* Sections
	* Section HTML Content

* Operating Content
	* Footer
	* Version out of date
	* CNAME content
	* Sync versions
