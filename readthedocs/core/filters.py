"""Extended classes for django-filter."""

from django_filters import ModelChoiceFilter, views


class FilteredModelChoiceFilter(ModelChoiceFilter):

    """
    A model choice field for customizing choice querysets at initialization.

    This extends the model choice field queryset lookup to include executing a
    method from the parent filter set. Normally, ModelChoiceFilter will use the
    underlying model manager ``all()`` method to populate choices. This of
    course is not correct as we need to worry about permissions to organizations
    and teams.

    Using a method on the parent filterset, the queryset can be filtered using
    attributes on the FilterSet instance, which for now is view time parameters
    like ``organization``.

    Additional parameters from this class:

    :param queryset_method: Name of method on parent FilterSet to call to build
                            queryset for choice population.
    :type queryset_method: str
    """

    def __init__(self, *args, **kwargs):
        self.queryset_method = kwargs.pop("queryset_method", None)
        super().__init__(*args, **kwargs)

    def get_queryset(self, request):
        if self.queryset_method:
            fn = getattr(self.parent, self.queryset_method, None)
            if not callable(fn):
                raise ValueError(f"Method {self.queryset_method} is not callable")
            return fn()
        return super().get_queryset(request)


class FilterMixin(views.FilterMixin):

    """
    Django-filter filterset mixin class.

    Django-filter gives two classes for constructing views:

    - :py:class:`~django_filters.views.BaseFilterView`
    - :py:class:`~django_filters.views.FilterMixin`

    These aren't quite yet usable, as some of our views still support our legacy
    dashboard. For now, this class will aim to be an intermediate step, but
    maintain some level of compatibility with the native mixin/view classes.
    """

    def get_filterset(self, **kwargs):
        """
        Construct filterset for view.

        This does not automatically execute like it would with BaseFilterView.
        Instead, this should be called directly from ``get_context_data()``.
        Unlike the parent methods, this method can be used to pass arguments
        directly to the ``FilterSet.__init__``.

        :param kwargs: Arguments to pass to ``FilterSet.__init__``
        """
        # This method overrides the method from FilterMixin with differing
        # arguments. We can switch this later if we ever resturcture the view
        # pylint: disable=arguments-differ
        if not getattr(self, "filterset", None):
            filterset_class = self.get_filterset_class()
            all_kwargs = self.get_filterset_kwargs(filterset_class)
            all_kwargs.update(kwargs)
            self.filterset = filterset_class(**all_kwargs)
        return self.filterset

    def get_filtered_queryset(self):
        if self.filterset.is_valid() or not self.get_strict():
            return self.filterset.qs
        return self.filterset.queryset.none()
