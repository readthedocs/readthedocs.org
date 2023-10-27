"""Extended classes for django-filter."""

from django_filters import ModelChoiceFilter


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
            assert callable(fn)
            return fn()
        return super().get_queryset(request)
