=========================
 Authentication Managers
=========================


This document explains the current behavior of our custom ``QuerySet``
used as managers on different objects:

* Project
  * ProjectRelationship (subprojects)
  * Domain
  * Notification

* Build
  * Version
  * BuildCommandResult

Currently, all our permission system is managed by these QuerySet on
both sites (community and corporate), where corporate overrides some
methods to enable the usage of ``Organization``, ``Team`` and
``TeamMember`` to check permissions.


Community
=========

``readthedocs.projects.querysets.ProjectQuerySetBase``


:.for_user_and_viewer:
   - PUBLIC (``privacy_level``) projects
   - + projects that the ``viewer`` is owner
   - filtered by projects the ``user`` owns

   .. note::

      This is useful to list projects under a user's profile for a
      particular viewer.

      It's currently used as a template tag on profile detail.


:.for_admin_user:
   - projects the user is maintainer (``users__in``)


:.public:
   - PUBLIC projects
   - + projects the user has access to (``_add_user_repos``)

     .. note::

        ``_add_user_repos`` adds to the queryset passed the
        ``Project`` objects (public, protected, private) where the
        user has access to.


:.protected:
   - PUBLIC or PROTECTED projects
   - + projects the user has access to (``_add_user_repos``)


:.private:
   - PRIVATE projects
   - + projects the user has access to (``_add_user_repos``)


:.dashboard:
   Is an alias to ``.for_admin_user``


:.api:
   Is an alias to ``.public``


Problems
--------

#. Inconsistency on privacy level methods (``.public``, ``.protected``, ``.private``).
   They return projects with the same privacy level as the method name plus *all the projects*
   for that user. This ends up in a mixture between privacy levels.

#. ``.api`` method is not prepared to support APIv3 permissions:

   * allow request for details on public projects
   * deny request for listing on all projects not owned by authed user

#. Easy to make mistakes if not immerse on this concept by using
   ``.objects.all`` or ``.objects.filter`` directly (overpassing our methods).

#. ``_add_user_repos``, which is the main method to know what objects the user has access to,
   depends on ``django-guardian`` and ``view_project`` permission.
   This one is added on ``Project.save`` and ``UserForm.save``.


Goals
-----

#. unify all auth checks in one place
#. make these checks compatible between community and corporate
#. allow contributors to follow the pattern
#. reduce mistakes when checking permissions
#. support APIv3 detail (public projects) and list (owned projects) permissions


Changes proposed (ideas)
------------------------


:.api:

   Introducing a new boolean argument ``detail`` allows us to return
   all public projects when ``True`` and only owned projects when
   ``False`` (listing).

   By defaulting in ``False`` we can keep the current behavior and
   make this backward compatible. Although, I don't like this default
   since a small mistake will give permissions to all the public
   projects.

   - projects the user has access to (``_add_users_repo``)

   .. code-block:: python

      def api(self, user=None, detail=True):
          if detail:
              # Allow accesing details for specific project
              return self.public(user)

          # Disallow listing on other's people projects
          queryset = self.none()
          if user:
              return self._add_user_repos(queryset, user)
          return queryset


   This allow us to specify the type of request the user is doing on the API (list, detail)
   and return the proper projects on each case.

   .. code-block:: python

      def get_queryset(self):
          queryset = super().get_queryset()
          return queryset.api(user=self.request.user, detail=self.detail)

   With this modification, if the user access

   * ``/api/v3/projects/`` will only see their projects
   * ``/api/v3/projects/pip/`` will see the detail resource of this public project (even if it's not owner)


:.api:

   Use a ``APIAuthMixin`` to create an abstraction for the needed
   queries on the API:

   * without modifying the managers

     .. code-block:: python

        class APIAuthMixin:
            def get_queryset(self):
               if self.detail:
                   return queryset.public
               else:
                   return queryset.private

   * modifying the manager to add ``detail`` argument

     .. code-block:: python

        class APIAuthMixin:
            def get_queryset(self):
                queryset = super().get_queryset()
                return queryset.api(user=self.request.user, detail=self.detail)


:.all, .filter, .annotate, etc:

   Currently, we are doing ``objects = ProjectQuerySet.as_manager()`` to override the default manager.
   We could use different approaches here to enforce the usage of our custom object permissions.

   #. Make ``Project.objects`` to raise an ``AttributeError`` and force to use another name:
      ``Projects.authed`` instead, for example
   #. Disallow calling ``.filter`` and ``.all`` and common Django methods on our custom manager
   #. Assign a manager named ``unauth`` to perform queries using common Django methods::

        >>> Projects.unauthed.all()
        >>> Projects.unauthed.filter(users=user)

   #. Override ``get_queryset`` in the manager to override the ``.objects.all()`` method.

   https://docs.djangoproject.com/en/2.2/topics/db/managers/


:.for_user, .for_member_user:

   These methods only exist in corporate.

   Add this method into community as well to get *all the projects
   this user has access to* (all public ones plus my own projects).

   .. note::

      Currently, this would be the same as ``.public(user=user)``,
      but it's confusing since not all the projects returned are public.

      Also, this will match the pattern in corporate, where we have
      this method already.

----

Extra notes
-----------

#. ``use_for_related_fields`` at QuerySet needs to be migrated since it's an old deprecated concept
   * it's marked as deprecated on 1.10 and replaced by ``Options.base_manager_name`` on 2.0
   * https://docs.djangoproject.com/en/2.2/releases/1.10/#manager-use-for-related-fields-and-inheritance-changes

#. ``assign`` (from django-guardian) for ``view_project`` is used immediately after adding the user to the Project (``project.users.add(user)``) which can probably be removed completely for Projects.

#. Corporate does not use django-guardian at all.


humitos' notes
~~~~~~~~~~~~~~

#. I like the idea of ``Project.authed.all`` and
   ``Project.unauthed.all`` since it's clear what we are accessing to

   * it would be good if we can disable the ``.objects`` completely
   * not using ``.objects`` will require a bigger refactor
   * forcing contributors to use our own methods looks safer
   * we can migrate gradually to only queries via ``.authed`` and ``.unauthed`` while keeping the ``.objects`` until we remove it completely
   * we can apply gradually migrate them and mark the other methods as deprecated by
     raising a deprecation warning. Then, it will be easy to identify where they are used
     and we can accept a refactor contribution for this.


#. Having an ``APIAuthMixin`` feels like splitting the permissions checks into another place.

   * doesn't seem like a bad idea to me, but I think we can't move all
     our custom queries to view Mixins since there are queries outside views (template, models, etc)
   * we will need to write another override structure for corporate site

#. Standarizing the methods on the manager (regarding privacy level) will give me more confident on using them.

   * adding the users' project on ``.public``, ``.private``, etc method looks confusing to me
   * ``.for_user`` sounds like a better name

#. The current implementation via Manager is not terrible. We can improve it to make the queries more clear, communicate it to contributors and reduce permissions mistakes.

#. Documenting the current methods with docstrings will help on follow the pattern.

   Second version of the Authentication document for Community with some problems listed, goals, and ideas proposed to discuss.



Corporate
=========

Follow the same conventions described for community.

``readthedocsinc.organizations.backend.OrganizationQuerySet``

:.for_user:
   - organizations that user owns
   - + organizations the user is member of


:.for_admin_user:
   - organizations the user owns


``readthedocsinc.projects.querysets.CorporateProjectQuerySet``

:.for_user_and_viewer:
   - projects where both, user and viewer, are member


:.for_admin_user:
   - projects where the user is admin (project admin --via ``admin`` Team, or organization admin)


:.for_member_user:
   - projects where the user is admin
   - + projects where the user is member


:.public:
   - all public projects
   - + projects the user owns
   - + projects the user is member of
   - filtered by organization (if passed)

   .. note::

      Has a ``include_all`` attribute that can be removed once builder does not hit API anymore.
      It's only used together with ``user.is_superuser`` to return *all projects* (not only PUBLIC ones)


:.for_user:
   Alias for ``.public``


:.protected:
   Alias for ``.public``


:.private:
   Alias for ``.for_member_user``


:.dashboard:
   Alias for ``.for_member_user``


:.api:
   Weird way to write an alias for ``.for_member_user``.

   Alias to ``.public`` if the user is superuser.


``readthedocsinc.organizations.backend.TeamManager``

:.teams_for_user:
   - teams where the user is admin (if passed)
   - teams where the user is member (if passed)
   - filtered by organization (if passed)


:.public:
   - all teams
   - filtered by ``active`` (if passed)
   - filtered by organization (if passed)

   .. note::

      I think this method does not make sense at all.

      * Team object has no attribute called ``active``.
      * if nothing is passed, all teams from all the organizations are returned

      I didn't find where this method is used, though. It may be removed.


:.api:
   - teams where the user is admin or member

   .. note::

      Uses ``.public`` when the user is a superuser, but can be replaced by ``self.all()``.


:.admin:
   - teams where the user is admin
   - filtered by organization (if passed)


:.member:
   - teams where the user is member or admin
   - filtered by organization (if passed)


Changes proposed (ideas)
------------------------

Basically, the same changes proposed for community should be adapted here.
Although, this project needs a little more refactoring around these methods since there are weird alias.

#. remove all ``include_all`` from all possible places since it's strictly tied to ``is_superuser``

#. once the builders don't hit the API, we can completely remove the ``is_superuser`` check.
   This will make these queries clearer and safer, as well.

#. rename some methods,

   * ``Organization.objects.for_user`` is not really clear what it will return.
     Although, ``.Organization.objects.member_of(user=user)`` is clearer to me.

   * follow the same rule for ``Organization.objects.for_admin_user``,
     renaming it to ``Organization.objects.owned_by(user=user)``.

   * use deprecation warning to gradually migrate these methods.


Extra notes
-----------

#. ``.public(include_all=)`` attribute seems it can be removed since it's only send as ``True``
   when the user is a superuser, which is already checked inside the ``.public`` method.

#. ``Organization.objects.for_admin_user(include_all=True)`` is really confusing.
   We are using it at ``readthedocsinc.restapi.views.OrganizationViewSet.key`` where we are including
   all the projects, but then inside the method, will only include them if the user is superuser.

   I thought that I was found a bug the first time I read it, because we were including all
   for just authenticated users.

#. The QuerySet objects live in ``readthedocsinc.organizations.backend`` instead of ``queryset``
   as in community repository.

   * Manager objects are mixed together with QuerySet ones in the same file.
