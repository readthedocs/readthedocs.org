"""
Views for creating, editing and viewing site-specific user profiles.

"""

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import Http404
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.generic.list import ListView

from profiles import utils


def create_profile(request, form_class=None, success_url=None,
                   template_name='profiles/private/create_profile.html',
                   extra_context=None):
    """
    Create a profile for the current user, if one doesn't already
    exist.

    If the user already has a profile, as determined by
    ``request.user.get_profile()``, a redirect will be issued to the
    :view:`profiles.views.edit_profile` view. If no profile model has
    been specified in the ``AUTH_PROFILE_MODULE`` setting,
    ``django.contrib.auth.models.SiteProfileNotAvailable`` will be
    raised.

    **Optional arguments:**

    ``extra_context``
        A dictionary of variables to add to the template context. Any
        callable object in this dictionary will be called to produce
        the end result which appears in the context.

    ``form_class``
        The form class to use for validating and creating the user
        profile. This form class must define a method named
        ``save()``, implementing the same argument signature as the
        ``save()`` method of a standard Django ``ModelForm`` (this
        view will call ``save(commit=False)`` to obtain the profile
        object, and fill in the user before the final save). If the
        profile object includes many-to-many relations, the convention
        established by ``ModelForm`` of using a method named
        ``save_m2m()`` will be used, and so your form class should
        also define this method.

        If this argument is not supplied, this view will use a
        ``ModelForm`` automatically generated from the model specified
        by ``AUTH_PROFILE_MODULE``.

    ``success_url``
        The URL to redirect to after successful profile creation. If
        this argument is not supplied, this will default to the URL of
        :view:`profiles.views.profile_detail` for the newly-created
        profile object.

    ``template_name``
        The template to use when displaying the profile-creation
        form. If not supplied, this will default to
        :template:`profiles/create_profile.html`.

    **Context:**

    ``form``
        The profile-creation form.

    **Template:**

    ``template_name`` keyword argument, or
    :template:`profiles/create_profile.html`.

    """
    try:
        profile_obj = request.user.get_profile()
        return HttpResponseRedirect(reverse('profiles_edit_profile'))
    except ObjectDoesNotExist:
        pass

    #
    # We set up success_url here, rather than as the default value for
    # the argument. Trying to do it as the argument's default would
    # mean evaluating the call to reverse() at the time this module is
    # first imported, which introduces a circular dependency: to
    # perform the reverse lookup we need access to profiles/urls.py,
    # but profiles/urls.py in turn imports this module.
    #

    if success_url is None:
        success_url = reverse('profiles_profile_detail',
                              kwargs={'username': request.user.username})
    if form_class is None:
        form_class = utils.get_profile_form()
    if request.method == 'POST':
        form = form_class(data=request.POST, files=request.FILES)
        if form.is_valid():
            profile_obj = form.save(commit=False)
            profile_obj.user = request.user
            profile_obj.save()
            if hasattr(form, 'save_m2m'):
                form.save_m2m()
            return HttpResponseRedirect(success_url)
    else:
        form = form_class()

    if extra_context is None:
        extra_context = {}
    context = RequestContext(request)
    for key, value in extra_context.items():
        context[key] = callable(value) and value() or value

    return render_to_response(template_name,
                              {'form': form},
                              context_instance=context)
create_profile = login_required(create_profile)


def edit_profile(request, form_class=None, success_url=None,
                 template_name='profiles/private/edit_profile.html',
                 extra_context=None):
    """
    Edit the current user's profile.

    If the user does not already have a profile (as determined by
    ``User.get_profile()``), a redirect will be issued to the
    :view:`profiles.views.create_profile` view; if no profile model
    has been specified in the ``AUTH_PROFILE_MODULE`` setting,
    ``django.contrib.auth.models.SiteProfileNotAvailable`` will be
    raised.

    **Optional arguments:**

    ``extra_context``
        A dictionary of variables to add to the template context. Any
        callable object in this dictionary will be called to produce
        the end result which appears in the context.

    ``form_class``
        The form class to use for validating and editing the user
        profile. This form class must operate similarly to a standard
        Django ``ModelForm`` in that it must accept an instance of the
        object to be edited as the keyword argument ``instance`` to
        its constructor, and it must implement a method named
        ``save()`` which will save the updates to the object. If this
        argument is not specified, this view will use a ``ModelForm``
        generated from the model specified in the
        ``AUTH_PROFILE_MODULE`` setting.

    ``success_url``
        The URL to redirect to following a successful edit. If not
        specified, this will default to the URL of
        :view:`profiles.views.profile_detail` for the profile object
        being edited.

    ``template_name``
        The template to use when displaying the profile-editing
        form. If not specified, this will default to
        :template:`profiles/edit_profile.html`.

    **Context:**

    ``form``
        The form for editing the profile.

    ``profile``
         The user's current profile.

    **Template:**

    ``template_name`` keyword argument or
    :template:`profiles/edit_profile.html`.

    """
    try:
        profile_obj = request.user.get_profile()
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse('profiles_profile_create'))

    #
    # See the comment in create_profile() for discussion of why
    # success_url is set up here, rather than as a default value for
    # the argument.
    #

    if success_url is None:
        success_url = reverse('profiles_profile_detail',
                              kwargs={'username': request.user.username})
    if form_class is None:
        form_class = utils.get_profile_form()
    if request.method == 'POST':
        form = form_class(data=request.POST, files=request.FILES, instance=profile_obj)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(success_url)
    else:
        form = form_class(instance=profile_obj)

    if extra_context is None:
        extra_context = {}
    context = RequestContext(request)
    for key, value in extra_context.items():
        context[key] = callable(value) and value() or value

    return render_to_response(template_name,
                              {'form': form,
                               'profile': profile_obj,
                               'user': profile_obj.user,
                              },
                              context_instance=context)
edit_profile = login_required(edit_profile)


def profile_detail(request, username, public_profile_field=None,
                   template_name='profiles/public/profile_detail.html',
                   extra_context=None):
    """
    Detail view of a user's profile.

    If no profile model has been specified in the
    ``AUTH_PROFILE_MODULE`` setting,
    ``django.contrib.auth.models.SiteProfileNotAvailable`` will be
    raised.

    If the user has not yet created a profile, ``Http404`` will be
    raised.

    **Required arguments:**

    ``username``
        The username of the user whose profile is being displayed.

    **Optional arguments:**

    ``extra_context``
        A dictionary of variables to add to the template context. Any
        callable object in this dictionary will be called to produce
        the end result which appears in the context.

    ``public_profile_field``
        The name of a ``BooleanField`` on the profile model; if the
        value of that field on the user's profile is ``False``, the
        ``profile`` variable in the template will be ``None``. Use
        this feature to allow users to mark their profiles as not
        being publicly viewable.

        If this argument is not specified, it will be assumed that all
        users' profiles are publicly viewable.

    ``template_name``
        The name of the template to use for displaying the profile. If
        not specified, this will default to
        :template:`profiles/profile_detail.html`.

    **Context:**

    ``profile``
        The user's profile, or ``None`` if the user's profile is not
        publicly viewable (see the description of
        ``public_profile_field`` above).

    **Template:**

    ``template_name`` keyword argument or
    :template:`profiles/profile_detail.html`.

    """
    user = get_object_or_404(User, username=username)
    try:
        profile_obj = user.get_profile()
    except ObjectDoesNotExist:
        raise Http404
    if public_profile_field is not None and \
       not getattr(profile_obj, public_profile_field):
        profile_obj = None

    if extra_context is None:
        extra_context = {}
    context = RequestContext(request)
    for key, value in extra_context.items():
        context[key] = callable(value) and value() or value

    return render_to_response(template_name,
                              {'profile': profile_obj},
                              context_instance=context)


class ProfileListView(ListView):

    """
    A list of user profiles.

    If no profile model has been specified in the
    ``AUTH_PROFILE_MODULE`` setting,
    ``django.contrib.auth.models.SiteProfileNotAvailable`` will be
    raised.

    **Optional arguments:**

    ``public_profile_field``
        The name of a ``BooleanField`` on the profile model; if the
        value of that field on a user's profile is ``False``, that
        profile will be excluded from the list. Use this feature to
        allow users to mark their profiles as not being publicly
        viewable.

        If this argument is not specified, it will be assumed that all
        users' profiles are publicly viewable.

    ``template_name``
        The name of the template to use for displaying the profiles. If
        not specified, this will default to
        :template:`profiles/profile_list.html`.

    Additionally, all arguments accepted by the
    :view:`django.views.generic.list_detail.object_list` generic view
    will be accepted here, and applied in the same fashion, with one
    exception: ``queryset`` will always be the ``QuerySet`` of the
    model specified by the ``AUTH_PROFILE_MODULE`` setting, optionally
    filtered to remove non-publicly-viewable proiles.

    **Context:**

    Same as the :view:`django.views.generic.list_detail.object_list`
    generic view.

    **Template:**

    ``template_name`` keyword argument or
    :template:`profiles/profile_list.html`.

    """

    public_profile_field = None
    template_name = 'profiles/profile_list.html'

    def get_model(self):
        return utils.get_profile_model()

    def get_queryset(self):
        queryset = self.get_model()._default_manager.all()
        if self.public_profile_field is not None:
            queryset = queryset.filter(**{self.public_profile_field: True})
        return queryset
