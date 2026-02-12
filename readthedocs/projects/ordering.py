"""Utilities to manage the position of items in a project."""

from django.db.models import F


class ProjectItemPositionManager:
    def __init__(self, position_field_name):
        self.position_field_name = position_field_name

    def change_position_before_save(self, item):
        """
        Re-order the positions of the other items when the position of this item changes.

        If the item is new, we just need to move all other items down,
        so there is space for the one.

        If the item already exists, we need to move the other items up or down,
        depending on the new position, so we can insert the item at the new position.

        The save() method needs to be called after this.
        """
        model = item._meta.model
        total = model.objects.filter(project=item.project).count()

        # If the item was just created, we just need to insert it at the given position.
        # We do this by moving the other items down before saving.
        if not item.pk:
            # A new item can be created at the end as max.
            position = min(getattr(item, self.position_field_name), total)
            setattr(item, self.position_field_name, position)

            # A new item can't be created with a negative position. All items start at 0.
            position = max(getattr(item, self.position_field_name), 0)
            setattr(item, self.position_field_name, position)

            items = (
                model.objects.filter(project=item.project)
                .filter(**{self.position_field_name + "__gte": position})
                # We sort the queryset in desc order
                # to be updated in that order
                # to avoid hitting the unique constraint (project, position).
                .order_by(f"-{self.position_field_name}")
            )
            expression = F(self.position_field_name) + 1
        else:
            current_position = model.objects.values_list(
                self.position_field_name,
                flat=True,
            ).get(pk=item.pk)

            # An existing item can't be moved past the end.
            position = min(getattr(item, self.position_field_name), total - 1)
            setattr(item, self.position_field_name, position)

            # A new item can't be created with a negative position, all items start at 0.
            position = max(getattr(item, self.position_field_name), 0)
            setattr(item, self.position_field_name, position)

            # The item wasn't moved, so we don't need to do anything.
            if position == current_position:
                return

            if position > current_position:
                # It was moved down, so we need to move the other items up.
                items = (
                    model.objects.filter(project=item.project)
                    .filter(
                        **{
                            self.position_field_name + "__gt": current_position,
                            self.position_field_name + "__lte": position,
                        }
                    )
                    # We sort the queryset in asc order
                    # to be updated in that order
                    # to avoid hitting the unique constraint (project, position).
                    .order_by(self.position_field_name)
                )
                expression = F(self.position_field_name) - 1
            else:
                # It was moved up, so we need to move the other items down.
                items = (
                    model.objects.filter(project=item.project)
                    .filter(
                        **{
                            self.position_field_name + "__lt": current_position,
                            self.position_field_name + "__gte": position,
                        }
                    )
                    # We sort the queryset in desc order
                    # to be updated in that order
                    # to avoid hitting the unique constraint (project, position).
                    .order_by(f"-{self.position_field_name}")
                )
                expression = F(self.position_field_name) + 1

        # Put an impossible position to avoid
        # the unique constraint (project, position) while updating.
        # We use update() instead of save() to avoid calling the save() method again.
        if item.pk:
            model.objects.filter(pk=item.pk).update(**{self.position_field_name: total + 99})

        # NOTE: we can't use items.update(position=expression), because SQLite is used
        # in tests and hits a UNIQUE constraint error. PostgreSQL doesn't have this issue.
        # We use update() instead of save() to avoid calling the save() method.
        for item_to_update in items:
            model.objects.filter(pk=item_to_update.pk).update(
                **{self.position_field_name: expression}
            )

    def change_position_after_delete(self, item):
        """
        Update the order of the other items after deleting an item.

        After deleting an item, we move the items below it up by one position.

        The delete() method needs to be called before this.
        """
        model = item._meta.model
        previous_position = getattr(item, self.position_field_name)
        items = (
            model.objects.filter(project=item.project)
            .filter(**{self.position_field_name + "__gte": previous_position})
            # We sort the queryset in asc order
            # to be updated in that order
            # to avoid hitting the unique constraint (project, position).
            .order_by(self.position_field_name)
        )
        # We update each object one by one to
        # avoid hitting the unique constraint (project, position).
        # We use update() instead of save() to avoid calling the save() method.
        for item_to_update in items:
            model.objects.filter(pk=item_to_update.pk).update(
                **{self.position_field_name: F(self.position_field_name) - 1}
            )
