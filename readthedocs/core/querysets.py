class NoReprQuerySet:
    """
    Basic queryset to override `__repr__` function due to logging issues.

    This may be a temporary solution for now and it can be improved to detect
    if we are under DEBUG and/or on an interactive shell.

    https://github.com/readthedocs/readthedocs.org/issues/10954
    https://github.com/readthedocs/readthedocs.org/issues/10954#issuecomment-2057596044
    https://github.com/readthedocs/readthedocs.org/issues/10954#issuecomment-2057951300
    """

    def __repr__(self):
        return self.__class__.__name__
