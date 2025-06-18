import json
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django_dynamic_fixture import get

from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.models import Build
from readthedocs.projects.models import Project
from readthedocs.aws.security_token_service import (
    AWSS3TemporaryCredentials,
    get_s3_build_media_scoped_credentials,
    get_s3_build_tools_scoped_credentials,
)


@override_settings(
    AWS_ACCESS_KEY_ID="global_access_key_id",
    AWS_SECRET_ACCESS_KEY="global_secret_access_key",
    AWS_S3_REGION_NAME="us-east-1",
    AWS_STS_ASSUME_ROLE_ARN="arn:aws:iam::1234:role/RoleName",
    S3_MEDIA_STORAGE_BUCKET="readthedocs-media",
    S3_BUILD_TOOLS_STORAGE_BUCKET="readthedocs-build-tools",
)
class TestSecurityTokenService(TestCase):
    def setUp(self):
        self.user = get(User)
        self.project = get(
            Project,
            slug="project",
            users=[self.user],
        )
        self.version = self.project.versions.first()
        self.build = get(
            Build,
            version=self.version,
            project=self.project,
        )

    @override_settings(USING_AWS=False, DEBUG=True)
    def test_get_s3_build_media_global_credentials(self):
        credentials = get_s3_build_media_scoped_credentials(build=self.build)
        assert credentials == AWSS3TemporaryCredentials(
            access_key_id="global_access_key_id",
            secret_access_key="global_secret_access_key",
            session_token=None,
            region_name="us-east-1",
            bucket_name="readthedocs-media",
        )

    @mock.patch("readthedocs.aws.security_token_service.boto3.client")
    def test_get_s3_build_media_scoped_credentials(self, boto3_client):
        boto3_client().assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "access_key_id",
                "SecretAccessKey": "secret_access_key",
                "SessionToken": "session_token",
            }
        }
        credentials = get_s3_build_media_scoped_credentials(build=self.build)
        assert credentials == AWSS3TemporaryCredentials(
            access_key_id="access_key_id",
            secret_access_key="secret_access_key",
            session_token="session_token",
            region_name="us-east-1",
            bucket_name="readthedocs-media",
        )

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
                    "Resource": [
                        "arn:aws:s3:::readthedocs-media/html/project/latest/*",
                        "arn:aws:s3:::readthedocs-media/pdf/project/latest/*",
                        "arn:aws:s3:::readthedocs-media/epub/project/latest/*",
                        "arn:aws:s3:::readthedocs-media/htmlzip/project/latest/*",
                        "arn:aws:s3:::readthedocs-media/json/project/latest/*",
                        "arn:aws:s3:::readthedocs-media/diff/project/latest/*",
                    ],
                },
                {
                    "Effect": "Allow",
                    "Action": ["s3:ListBucket"],
                    "Resource": [
                        "arn:aws:s3:::readthedocs-media",
                    ],
                    "Condition": {
                        "StringLike": {
                            "s3:prefix": [
                                "html/project/latest/*",
                                "pdf/project/latest/*",
                                "epub/project/latest/*",
                                "htmlzip/project/latest/*",
                                "json/project/latest/*",
                                "diff/project/latest/*",
                            ]
                        }
                    },
                },
            ],
        }

        boto3_client().assume_role.assert_called_once_with(
            RoleArn="arn:aws:iam::1234:role/RoleName",
            RoleSessionName=f"rtd-{self.build.id}-project-latest",
            Policy=json.dumps(policy),
            DurationSeconds=15 * 60,
        )

    @mock.patch("readthedocs.aws.security_token_service.boto3.client")
    def test_get_s3_build_media_scoped_credentials_external_version(self, boto3_client):
        self.version.type = EXTERNAL
        self.version.save()

        boto3_client().assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "access_key_id",
                "SecretAccessKey": "secret_access_key",
                "SessionToken": "session_token",
            }
        }
        credentials = get_s3_build_media_scoped_credentials(build=self.build)
        assert credentials == AWSS3TemporaryCredentials(
            access_key_id="access_key_id",
            secret_access_key="secret_access_key",
            session_token="session_token",
            region_name="us-east-1",
            bucket_name="readthedocs-media",
        )

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
                    "Resource": [
                        "arn:aws:s3:::readthedocs-media/external/html/project/latest/*",
                        "arn:aws:s3:::readthedocs-media/external/pdf/project/latest/*",
                        "arn:aws:s3:::readthedocs-media/external/epub/project/latest/*",
                        "arn:aws:s3:::readthedocs-media/external/htmlzip/project/latest/*",
                        "arn:aws:s3:::readthedocs-media/external/json/project/latest/*",
                        "arn:aws:s3:::readthedocs-media/external/diff/project/latest/*",
                    ],
                },
                {
                    "Effect": "Allow",
                    "Action": ["s3:ListBucket"],
                    "Resource": [
                        "arn:aws:s3:::readthedocs-media",
                    ],
                    "Condition": {
                        "StringLike": {
                            "s3:prefix": [
                                "external/html/project/latest/*",
                                "external/pdf/project/latest/*",
                                "external/epub/project/latest/*",
                                "external/htmlzip/project/latest/*",
                                "external/json/project/latest/*",
                                "external/diff/project/latest/*",
                            ]
                        }
                    },
                },
            ],
        }

        boto3_client().assume_role.assert_called_once_with(
            RoleArn="arn:aws:iam::1234:role/RoleName",
            RoleSessionName=f"rtd-{self.build.id}-project-latest",
            Policy=json.dumps(policy),
            DurationSeconds=15 * 60,
        )

    @override_settings(USING_AWS=False, DEBUG=True)
    def test_get_s3_build_tools_global_credentials(self):
        credentials = get_s3_build_tools_scoped_credentials(build=self.build)
        assert credentials == AWSS3TemporaryCredentials(
            access_key_id="global_access_key_id",
            secret_access_key="global_secret_access_key",
            session_token=None,
            region_name="us-east-1",
            bucket_name="readthedocs-build-tools",
        )

    @mock.patch("readthedocs.aws.security_token_service.boto3.client")
    def test_get_s3_build_tools_scoped_credentials(self, boto3_client):
        boto3_client().assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "access_key_id",
                "SecretAccessKey": "secret_access_key",
                "SessionToken": "session_token",
            }
        }
        credentials = get_s3_build_tools_scoped_credentials(build=self.build)
        assert credentials == AWSS3TemporaryCredentials(
            access_key_id="access_key_id",
            secret_access_key="secret_access_key",
            session_token="session_token",
            region_name="us-east-1",
            bucket_name="readthedocs-build-tools",
        )

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
                        "arn:aws:s3:::readthedocs-build-tools",
                        "arn:aws:s3:::readthedocs-build-tools/*",
                    ],
                },
            ],
        }

        boto3_client().assume_role.assert_called_once_with(
            RoleArn="arn:aws:iam::1234:role/RoleName",
            RoleSessionName=f"rtd-{self.build.id}-project-latest",
            Policy=json.dumps(policy),
            DurationSeconds=15 * 60,
        )

    @mock.patch("readthedocs.aws.security_token_service.boto3.client")
    def test_get_s3_build_tools_scoped_credentials_external_version(self, boto3_client):
        self.version.type = EXTERNAL
        self.version.save()

        boto3_client().assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "access_key_id",
                "SecretAccessKey": "secret_access_key",
                "SessionToken": "session_token",
            }
        }
        credentials = get_s3_build_tools_scoped_credentials(build=self.build)
        assert credentials == AWSS3TemporaryCredentials(
            access_key_id="access_key_id",
            secret_access_key="secret_access_key",
            session_token="session_token",
            region_name="us-east-1",
            bucket_name="readthedocs-build-tools",
        )

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
                        "arn:aws:s3:::readthedocs-build-tools",
                        "arn:aws:s3:::readthedocs-build-tools/*",
                    ],
                },
            ],
        }

        boto3_client().assume_role.assert_called_once_with(
            RoleArn="arn:aws:iam::1234:role/RoleName",
            RoleSessionName=f"rtd-{self.build.id}-project-latest",
            Policy=json.dumps(policy),
            DurationSeconds=15 * 60,
        )
