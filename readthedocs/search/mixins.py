from django.db import models
from django.core.paginator import Paginator


class RTDDocTypeMixin(object):

    """
    Override some methods of DocType of DED

    Changelog as following:
    - Do not index object that not exist in the provided queryset
    - Take additional argument in update method `index_name` to update specific index
    Issues:
    - https://github.com/sabricot/django-elasticsearch-dsl/issues/111
    """

    def _prepare_action(self, object_instance, action, index_name=None):
        """Overwrite to take `index_name` from parameters for setting index dynamically"""
        return {
            '_op_type': action,
            '_index': index_name or str(self._doc_type.index),
            '_type': self._doc_type.mapping.doc_type,
            '_id': object_instance.pk,
            '_source': (
                self.prepare(object_instance) if action != 'delete' else None
            ),
        }

    def _get_actions(self, object_list, action, index_name=None):
        """Overwrite to take `index_name` from parameters for setting index dynamically"""
        if self._doc_type.queryset_pagination is not None:
            paginator = Paginator(
                object_list, self._doc_type.queryset_pagination
            )
            for page in paginator.page_range:
                for object_instance in paginator.page(page).object_list:
                    yield self._prepare_action(object_instance, action, index_name)
        else:
            for object_instance in object_list:
                yield self._prepare_action(object_instance, action, index_name)

    def update(self, thing, refresh=None, action='index', index_name=None, **kwargs):
        """Update each document in ES for a model, iterable of models or queryset"""
        if refresh is True or (
            refresh is None and self._doc_type.auto_refresh
        ):
            kwargs['refresh'] = True

        # TODO: remove this overwrite when the issue has been fixed
        # https://github.com/sabricot/django-elasticsearch-dsl/issues/111
        if isinstance(thing, models.Model):
            # Its a model instance.

            # Do not need to check if its a delete action
            # Because while delete action, the object is already remove from database
            if action != 'delete':
                queryset = self.get_queryset()
                obj = queryset.filter(pk=thing.pk)
                if not obj.exists():
                    return None

            object_list = [thing]
        else:
            object_list = thing

        return self.bulk(
            self._get_actions(object_list, action, index_name=index_name), **kwargs
        )
