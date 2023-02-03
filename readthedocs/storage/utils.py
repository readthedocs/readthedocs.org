"""Storage utilities."""

from storages.utils import clean_name
from storages.utils import safe_join as safe_join_storage


def safe_join(base, path):
    """
    Safely join paths, ensuring that the final path isn't outside the directory.

    We use clean_name before using safe_join,
    replicating the logic from django-storages:

    https://github.com/jschneier/django-storages/blob/94c30923c0e12fb73817167266024ae8efad1265/storages/backends/s3boto3.py#L422

    This ensures that out path traversal protections can't be bypassed,
    see GHSA-5w8m-r7jm-mhp9 for more information.
    """
    return safe_join_storage(base, clean_name(path))
