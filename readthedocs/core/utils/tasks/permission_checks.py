"""Permission checks for tasks"""

__all__ = ('user_id_matches',)


def user_id_matches(request, state, context):  # pylint: disable=unused-argument
    user_id = context.get('user_id', None)
    if user_id is not None and request.user.is_authenticated():
        if request.user.id == user_id:
            return True
    return False
