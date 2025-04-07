import json
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django_dynamic_fixture import get

from readthedocs.builds.constants import EXTERNAL
from readthedocs.projects.models import Project
from readthedocs.aws.security_token_service import (
    AWSTemporaryCredentials,
    get_s3_scoped_credentials,
)


@override_settings(
    AWS_ACCESS_KEY_ID="global_access_key_id",
    AWS_SECRET_ACCESS_KEY="global_secret_access_key",
    AWS_S3_REGION_NAME="us-east-1",
    AWS_STS_ASSUME_ROLE_ARN="arn:aws:iam::1234:role/RoleName",
    S3_MEDIA_STORAGE_BUCKET="readthedocs-media",
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

    @override_settings(USING_AWS=False)
    def test_get_s3_global_credentials(self):
        credentials = get_s3_scoped_credentials(
            project=self.project,
            version=self.version,
        )
        assert credentials == AWSTemporaryCredentials(
            access_key_id="global_access_key_id",
            secret_access_key="global_secret_access_key",
            session_token=None,
        )

    @mock.patch("readthedocs.aws.security_token_service.boto3.client")
    def test_get_s3_scoped_credentials(self, boto3_client):
        boto3_client().assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "access_key_id",
                "SecretAccessKey": "secret_access_key",
                "SessionToken": "session_token",
            }
        }
        credentials = get_s3_scoped_credentials(
            project=self.project,
            version=self.version,
            session_id="1234",
        )
        assert credentials == AWSTemporaryCredentials(
            access_key_id="access_key_id",
            secret_access_key="secret_access_key",
            session_token="session_token",
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
            RoleSessionName="rtd-1234-project-latest",
            Policy=json.dumps(policy),
            DurationSeconds=900,
        )

    @mock.patch("readthedocs.aws.security_token_service.boto3.client")
    def test_get_s3_scoped_credentials_external_version(self, boto3_client):
        self.version.type = EXTERNAL
        self.version.save()

        boto3_client().assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "access_key_id",
                "SecretAccessKey": "secret_access_key",
                "SessionToken": "session_token",
            }
        }
        credentials = get_s3_scoped_credentials(
            project=self.project,
            version=self.version,
            session_id="1234",
        )
        assert credentials == AWSTemporaryCredentials(
            access_key_id="access_key_id",
            secret_access_key="secret_access_key",
            session_token="session_token",
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
            RoleSessionName="rtd-1234-project-latest",
            Policy=json.dumps(policy),
            DurationSeconds=900,
        )
