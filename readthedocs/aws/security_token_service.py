"""
Module to interact with AWS STS (Security Token Service) to assume a role and get temporary scoped credentials.

This is mainly used to generate temporary credentials to interact with S3 buckets from the builders.

In order to make use of STS, we need:

- Create a role in IAM with a trusted entity type set to the AWS account that is going to be used to generate the temporary credentials.
- Create an inline policy for the role, the policy should allow access to all S3 buckets and paths that are going to be used.
- Create an inline policy to the user that is going to be used to generate the temporary credentials,
  the policy should allow the ``sts:AssumeRole`` action for the role created in the previous step.

The permissions of the temporary credentials are the result of the intersection of the role policy and the inline policy that is passed to the AssumeRole API.
This means that the inline policy can be used to limit the permissions of the temporary credentials, but not to expand them.

See:

- https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html
- https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_sts-comparison.html
- https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp_control-access_assumerole.html
- https://docs.readthedocs.com/dev/latest/aws-temporary-credentials.html
"""

import json
from dataclasses import dataclass

import boto3
import structlog
from django.conf import settings


log = structlog.get_logger(__name__)


class AWSTemporaryCredentialsError(Exception):
    """Exception raised when there is an error getting AWS S3 credentials."""


@dataclass
class AWSTemporaryCredentials:
    """Dataclass to hold AWS temporary credentials."""

    access_key_id: str
    secret_access_key: str
    session_token: str | None


@dataclass
class AWSS3TemporaryCredentials(AWSTemporaryCredentials):
    """Subclass of AWSTemporaryCredentials to include S3 specific fields."""

    bucket_name: str
    region_name: str


def get_sts_client():
    return boto3.client(
        "sts",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )


def _get_scoped_credentials(*, session_name, policy, duration) -> AWSTemporaryCredentials:
    """
    :param session_name: An identifier to attach to the generated credentials, useful to identify who requested them.
     AWS limits the session name to 64 characters, so if the session_name is too long, it will be truncated.
    :param duration: The duration of the credentials in seconds. Default is 15 minutes.
     Note that the minimum duration time is 15 minutes and the maximum is given by the role (defaults to 1 hour).
    :param policy: The inline policy to attach to the generated credentials.

    .. note::

       If USING_AWS is set to False, this function will return
       the values of the AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY settings.
       Useful for local development where we don't have a service like AWS STS.
    """
    if not settings.USING_AWS:
        if not settings.DEBUG:
            raise ValueError(
                "Not returning global credentials, AWS STS should always be used in production."
            )
        return AWSTemporaryCredentials(
            access_key_id=settings.AWS_ACCESS_KEY_ID,
            secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            # A session token is not needed for the default credentials.
            session_token=None,
        )

    # Limit to 64 characters, as per AWS limitations.
    session_name = session_name[:64]
    try:
        sts_client = get_sts_client()
        response = sts_client.assume_role(
            RoleArn=settings.AWS_STS_ASSUME_ROLE_ARN,
            RoleSessionName=session_name,
            Policy=json.dumps(policy),
            DurationSeconds=duration,
        )
    except Exception:
        log.exception(
            "Error while assuming role to generate temporary credentials",
            session_name=session_name,
            policy=policy,
            duration=duration,
        )
        raise AWSTemporaryCredentialsError

    credentials = response["Credentials"]
    return AWSTemporaryCredentials(
        access_key_id=credentials["AccessKeyId"],
        secret_access_key=credentials["SecretAccessKey"],
        session_token=credentials["SessionToken"],
    )


def get_s3_build_media_scoped_credentials(
    *,
    build,
    duration=60 * 15,
) -> AWSS3TemporaryCredentials:
    """
    Get temporary credentials with read/write access to the build media bucket.

    The credentials are scoped to the paths that the build needs to access.

    :duration: The duration of the credentials in seconds. Default is 15 minutes.
     Note that the minimum duration time is 15 minutes and the maximum is given by the role (defaults to 1 hour).
    """
    project = build.project
    version = build.version
    bucket_arn = f"arn:aws:s3:::{settings.S3_MEDIA_STORAGE_BUCKET}"
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

    # Inline policy document to limit the permissions of the temporary credentials.
    policy = {
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

    session_name = f"rtd-{build.id}-{project.slug}-{version.slug}"
    credentials = _get_scoped_credentials(
        session_name=session_name,
        policy=policy,
        duration=duration,
    )
    return AWSS3TemporaryCredentials(
        access_key_id=credentials.access_key_id,
        secret_access_key=credentials.secret_access_key,
        session_token=credentials.session_token,
        region_name=settings.AWS_S3_REGION_NAME,
        bucket_name=settings.S3_MEDIA_STORAGE_BUCKET,
    )


def get_s3_build_tools_scoped_credentials(
    *,
    build,
    duration=60 * 15,
) -> AWSS3TemporaryCredentials:
    """
    Get temporary credentials with read-only access to the build-tools bucket.

    :param build: The build to get the credentials for.
    :param duration: The duration of the credentials in seconds. Default is 15 minutes.
     Note that the minimum duration time is 15 minutes and the maximum is given by the role (defaults to 1 hour).
    """
    project = build.project
    version = build.version
    bucket = settings.S3_BUILD_TOOLS_STORAGE_BUCKET
    bucket_arn = f"arn:aws:s3:::{bucket}"

    # Inline policy to limit the permissions of the temporary credentials.
    # The build-tools bucket is publicly readable, so we don't need to limit the permissions to a specific path.
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:ListBucket",
                ],
                "Resource": [
                    bucket_arn,
                    f"{bucket_arn}/*",
                ],
            },
        ],
    }
    session_name = f"rtd-{build.id}-{project.slug}-{version.slug}"
    credentials = _get_scoped_credentials(
        session_name=session_name,
        policy=policy,
        duration=duration,
    )
    return AWSS3TemporaryCredentials(
        access_key_id=credentials.access_key_id,
        secret_access_key=credentials.secret_access_key,
        session_token=credentials.session_token,
        region_name=settings.AWS_S3_REGION_NAME,
        bucket_name=bucket,
    )
