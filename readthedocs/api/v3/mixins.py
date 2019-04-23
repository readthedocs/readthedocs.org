class APIAuthMixin:

    def get_queryset(self):
        # ``super().get_queryset`` produces the filter by ``NestedViewSetMixin``
        # we need to have defined the class attribute as ``queryset = Model.objects.all()``
        queryset = super().get_queryset()

        return queryset.api(user=self.request.user, detail=self.detail)
