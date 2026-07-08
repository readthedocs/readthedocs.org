from pathlib import Path

import structlog
from django.conf import settings

from readthedocs.api.v2.client import setup_api
from readthedocs.builds.constants import ARTIFACT_TYPES
from readthedocs.builds.constants import BUILD_STATE_CLONING
from readthedocs.builds.constants import BUILD_STATE_FINISHED
from readthedocs.builds.constants import BUILD_STATE_UPLOADING
from readthedocs.builds.constants import UNDELETABLE_ARTIFACT_TYPES
from readthedocs.builds.models import APIVersion
from readthedocs.doc_builder.environments import DockerBuildEnvironment
from readthedocs.projects.tasks.storage import StorageType
from readthedocs.projects.tasks.storage import get_storage
from readthedocs.projects.tasks.utils import clean_build
from readthedocs.worker import app


logger = structlog.get_logger(__name__)


@app.task()
def process_uploaded_build(build_id, version_id, build_api_key):
    structlog.contextvars.bind_contextvars(
        build_id=build_id,
        version_id=version_id,
    )
    api_client = setup_api(build_api_key)
    build_data = api_client.build(build_id).get()
    version_data = api_client.version(version_id).get()
    logger.info("Version data retrieved.", version_data=version_data)
    version = APIVersion(**version_data)
    project = version.project
    logger.info("Project", project_id=project.id, project_slug=project.slug)
    build_uploads_storage = get_storage(
        build_id=build_id,
        api_client=api_client,
        storage_type=StorageType.build_uploads,
    )

    clean_build(version=version)

    build_data["state"] = BUILD_STATE_CLONING
    _update_build(api_client, build_data)

    # Download zip
    # TODO: create a fake command to mock the download process?
    # Or maybe we can request a signed URL to download the zip from docker?
    # TODO: use the build id instead? probably the docker env is hardcoded to use the version slug.
    output_dir = Path(project.checkout_path(version.slug))
    local_zip_artifacts_path = output_dir / "artifacts.zip"
    artifacts_storage_path = f"{project.id}/{build_id}/artifacts.zip"
    with build_uploads_storage.open(artifacts_storage_path, "rb") as artifacts_file:
        local_zip_artifacts_path.parent.mkdir(parents=True, exist_ok=True)
        with local_zip_artifacts_path.open("wb") as local_file:
            local_file.write(artifacts_file.read())

    environment = DockerBuildEnvironment(
        project=project,
        version=version,
        build=build_data,
        container_image=settings.RTD_DOCKER_CLONE_IMAGE,
        api_client=api_client,
    )
    local_artifacts_path = output_dir / "_readthedocs"
    with environment:
        # Exctract zip
        environment.run(
            "unzip",
            str(local_zip_artifacts_path),
            "-d",
            str(local_artifacts_path),
            cwd=str(output_dir),
        )

    # Validate files

    build_data["state"] = BUILD_STATE_UPLOADING
    _update_build(api_client, build_data)

    logger.info("Uploading artifacts to storage.")
    # Upload artifacts to the right place
    build_media_storage = get_storage(
        build_id=build_id,
        api_client=api_client,
        storage_type=StorageType.build_media,
    )
    for media_type in ARTIFACT_TYPES:
        from_path = project.artifact_path(
            version=version.slug,
            type_=media_type,
        )
        to_path = version.get_storage_path(media_type=media_type)
        if Path(from_path).exists():
            build_media_storage.rclone_sync_directory(from_path, to_path)
        elif media_type not in UNDELETABLE_ARTIFACT_TYPES:
            build_media_storage.delete_directory(to_path)

    logger.info("Artifacts uploaded.")
    build_data["state"] = BUILD_STATE_FINISHED
    _update_build(api_client, build_data)
    clean_build(version=version)


def _update_build(api_client, build_data):
    api_client.build(build_data["id"]).patch(build_data)
