"""Extended classes for django-filter."""

from django_filters import ModelChoiceFilter


class FilteredModelChoiceFilter(ModelChoiceFilter):

    """
    A model choice field for customizing choice querysets at initialization.

    This extends the model choice field queryset lookup to include executing a
    method from the parent filter set. This allows for use of ``self`` on the
    filterset, allowing better support for view time filtering.
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
