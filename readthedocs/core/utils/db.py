from collections import Counter
from itertools import batched


def delete_in_batches(queryset, batch_size=50, limit: int | None =None) -> tuple[int, dict]:
    """
    Delete a queryset in batches to avoid long transactions or big queries.

    When deleting a large number of records at once, Django will try to update
    all the related objects in a single transaction (on_delete/cascade updates),
    which can lead to database locks, long-running/inefficient queries.
    Deleting in smaller batches helps mitigate these issues. Prefer using this
    to ``_raw_delete`` when the objects to delete have foreign keys.

    Similar to Django's ``QuerySet.delete()``, it returns a tuple with the number of
    deleted objects and a dictionary with the number of deletions per model type.

    This is also useful when you don't want to overload the DB by deleting
    a large number of records at once, since .delete() doesn't support limits/offsets.

    .. code-block:: python

       delete_in_batches(MyModel.objects.filter(...)[:10000])

    :param queryset: Django queryset to delete
    :param batch_size: Number of records to delete per batch
    """
    # Don't use batch deletion if the number of records
    # is smaller or equal to the batch size.
    count = queryset.count()
    if count == 0:
        return 0, {}
    if count <= batch_size:
        return queryset.delete()

    model = queryset.model
    total_deleted = 0
    deleted_counter = Counter()
    # We can't use a limit or offset with .delete,
    # so we first extract the IDs and perform the deletion in anothr query.
    all_pks = queryset.values_list("pk", flat=True)
    if limit:
        all_pks = all_pks[:limit]
    for batch in batched(all_pks, batch_size):
        total_deleted_batch, deleted_counter_batch = model.objects.filter(pk__in=batch).delete()
        total_deleted += total_deleted_batch
        deleted_counter.update(deleted_counter_batch)
    return total_deleted, dict(deleted_counter)


def raw_delete_in_batches(queryset, batch_size=50, limit: int | None =None):
    """
    Raw delete a queryset in batches to avoid long transactions or big queries.

    Similar to ``delete_in_batches``, but uses ``_raw_delete``.
    This is useful when you don't want to overload the DB by deleting
    a large number of records at once, since _raw_delete() doesn't support
    limits/offsets.

    .. warning::

       Since this uses ``_raw_delete``, it won't trigger any
       signals, and won't cascade delete related objects.
       Use it only if you are sure there are no related objects
       that need to be deleted/updated.
    """
    # Don't use batch deletion if the number of records
    # is smaller or equal to the batch size.
    count = queryset.count()
    if count == 0:
        return
    if count <= batch_size:
        queryset._raw_delete(queryset.db)
        return

    model = queryset.model
    # We can't use a limit or offset with .raw_delete,
    # so we first extract the IDs and perform the deletion in anothr query.
    all_pks = queryset.values_list("pk", flat=True)
    if limit:
        all_pks = all_pks[:limit]
    for batch in batched(all_pks, batch_size):
        qs = model.objects.filter(pk__in=batch)
        qs._raw_delete(qs.db)
