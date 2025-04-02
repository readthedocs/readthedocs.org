"""
Module to interact with AWS STS (Security Token Service) to assume a role and get temporary scoped credentials.

This is mainly used to generate temporary credentials to interact with S3 buckets from the builders.

In order to make use of STS, we need:

- Create a role in IAM with a trusted entity type set to the AWS account that is going to be used to generate the temporary credentials.
- A policy that allows access to all S3 buckets and paths that are going to be used.
  Which should be attached to the role.
- The permissions of the temporary credentials are the result of the intersection of the role policy and the inline policy that is passed to the AssumeRole API.
  This means that the inline policy can be used to limit the permissions of the temporary credentials, but not to expand them.

See:

- https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html
- https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_sts-comparison.html
- https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp_control-access_assumerole.html
"""

import json
from dataclasses import dataclass

import boto3
import structlog
from django.conf import settings

from readthedocs.storage import build_media_storage


log = structlog.get_logger(__name__)


class AWSTemporaryCredentialsError(Exception):
    """Exception raised when there is an error getting AWS S3 credentials."""


@dataclass
class AWSTemporaryCredentials:
    """Dataclass to hold AWS temporary credentials."""

    access_key_id: str
    secret_access_key: str
    session_token: str | None


def get_sts_client():
    return boto3.client(
        "sts",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        # TODO: should this be its own setting?
        region_name=settings.AWS_S3_REGION_NAME,
    )


def get_s3_scoped_credentials(
    *, project, version, session_id=None, duration=60 * 15
) -> AWSTemporaryCredentials:
    """
    :param project: The project to get the credentials for.
    :param version: The version to get the credentials for.
    :param session_id: A unique identifier to add to the name of the role session.
     The name of the session always includes the project and version slug (rtd-{project}-{version}),
     if session_id is given, the name of the session would be "rtd-{session_id}-{project}-{version}".
     AWS limits the session name to 64 characters, so if the session_id is too long, it will be truncated.
     For example, for a token used in a build, a good session_id is the ID of the build.
    :duration: The duration of the credentials in seconds. Default is 15 minutes.
     Note that the minimum duration time is 15 minutes and the maximum is given by the role (defaults to 1 hour).

    .. note::

       If USING_AWS is set to False, this function will return
       the values of the AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY settings.
       Useful for local development where we use minio.
    """
    if not settings.USING_AWS:
        return AWSTemporaryCredentials(
            access_key_id=settings.AWS_ACCESS_KEY_ID,
            secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            # A session token is not needed for the default credentials.
            session_token=None,
        )

    bucket_name = build_media_storage.bucket_name
    bucket_arn = f"arn:aws:s3:::{bucket_name}"

    storage_paths = version.get_storage_paths()
    # Generate the list of allowed prefix resources
    # The resulting prefix looks like:
    # - html/project/latest/*
    # - pdf/project/latest/*
    allowed_prefixes = [f"{storage_path}/*" for storage_path in storage_paths]

    # Generate the list of allowed object resources in ARN format.
    # The resulting ARN looks like:
    # arn:aws:s3:::readthedocs-media/html/project/latest/*
    # arn:aws:s3:::readthedocs-media/pdf/project/latest/*
    allowed_objects_arn = [f"{bucket_arn}/{prefix}" for prefix in allowed_prefixes]

    # Define an inline policy document to limit the permissions of the temporary credentials.
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                ],
                "Resource": allowed_objects_arn,
            },
            # In order to list the objects in a path, we need to allow the ListBucket action.
            # But since that action is not scoped to a path, we need to limit it using a condition.
            {
                "Effect": "Allow",
                "Action": ["s3:ListBucket"],
                "Resource": [
                    bucket_arn,
                ],
                "Condition": {
                    "StringLike": {
                        "s3:prefix": allowed_prefixes,
                    }
                },
            },
        ],
    }

    session_prefix = f"rtd-{session_id}" if session_id else "rtd"
    role_session_name = f"{session_prefix}-{project.slug}-{version.slug}"
    # Limit to 64 characters, as per AWS limitations.
    role_session_name = role_session_name[:64]

    try:
        sts_client = get_sts_client()
        response = sts_client.assume_role(
            RoleArn=settings.AWS_STS_ASSUME_ROLE_ARN,
            RoleSessionName=role_session_name,
            Policy=json.dumps(policy_document),
            DurationSeconds=duration,
        )
    except Exception:
        log.exception(
            "Error while assuming role to generate temporary credentials",
            role_session_name=role_session_name,
            policy_document=policy_document,
            duration=duration,
        )
        raise AWSTemporaryCredentialsError

    credentials = response["Credentials"]
    return AWSTemporaryCredentials(
        access_key_id=credentials["AccessKeyId"],
        secret_access_key=credentials["SecretAccessKey"],
        session_token=credentials["SessionToken"],
    )
