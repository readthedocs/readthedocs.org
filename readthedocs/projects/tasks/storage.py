from enum import StrEnum
from enum import auto

import structlog
from django.conf import settings
from django.utils.module_loading import import_string

from readthedocs.doc_builder.exceptions import BuildAppError
from readthedocs.projects.models import Feature


log = structlog.get_logger(__name__)


class StorageType(StrEnum):
    build_media = auto()
    build_tools = auto()


def get_storage(*, project, build_id, api_client, storage_type: StorageType):
    """
    Get a storage class instance to interact with storage from the build.

    .. note::

        We no longer use readthedocs.storage.build_media_storage/build_tools_storage directly,
        as we are now using per-build credentials for S3 storage,
        so we need to dynamically create the storage class instance
    """
    storage_class = _get_storage_class(storage_type)
    extra_kwargs = {}
    if settings.USING_AWS:
        extra_kwargs = _get_s3_scoped_credentials(
            project=project, build_id=build_id, api_client=api_client, storage_type=storage_type
        )
    return storage_class(**extra_kwargs)


def _get_storage_class(storage_type: StorageType):
    """
    Get a storage class to use for interacting with storage.

    .. note::

        We no longer use readthedocs.storage.build_media_storage/build_tools_storage directly,
        as we are now using per-build credentials for S3 storage,
        so we need to dynamically create the storage class instance
    """
    if storage_type == StorageType.build_media:
        return _get_build_media_storage_class()
    if storage_type == StorageType.build_tools:
        return _get_build_tools_storage_class()
    raise ValueError("Invalid storage type")


def _get_build_media_storage_class():
    """
    Get a storage class to use for syncing build artifacts.

    This is done in a separate method to make it easier to mock in tests.
    """
    return import_string(settings.RTD_BUILD_MEDIA_STORAGE)


def _get_build_tools_storage_class():
    """
    Get a storage class to use for downloading build tools.

    This is done in a separate method to make it easier to mock in tests.
    """
    return import_string(settings.RTD_BUILD_TOOLS_STORAGE)


def _get_s3_scoped_credentials(*, project, build_id, api_client, storage_type: StorageType):
    """Get the scoped credentials for the build using our internal API."""
    if not project.has_feature(Feature.USE_S3_SCOPED_CREDENTIALS_ON_BUILDERS):
        # Use the default credentials defined in the settings.
        return {}

    try:
        credentials = api_client.build(f"{build_id}/credentials/storage").post(
            {"type": storage_type.value}
        )
    except Exception:
        raise BuildAppError(
            BuildAppError.GENERIC_WITH_BUILD_ID,
            exception_message="Error getting scoped credentials.",
        )

    s3_credentials = credentials["s3"]
    return {
        "access_key": s3_credentials["access_key_id"],
        "secret_key": s3_credentials["secret_access_key"],
        "security_token": s3_credentials["session_token"],
        "bucket_name": s3_credentials["bucket_name"],
        "region_name": s3_credentials["region_name"],
    }
