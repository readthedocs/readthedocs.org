"""
Wrapper around the rclone command.

See https://rclone.org/docs.
"""

import os
import subprocess

import structlog

log = structlog.get_logger(__name__)


class RClone:

    """
    RClone base class.

    This class allows you to interact with an rclone remote without
    a configuration file, the remote declaration and its options
    are passed in the command itself.

    This base class allows you to use the local file system as remote.

    :param remote_type: You can see the full list of supported providers at
     https://rclone.org/#providers. Defaults to use the local filesystem
     (https://rclone.org/local/).
    :param rclone_bin: Binary name or path to the rclone binary.
     Defaults to ``rclone``.
    :param default_options: Options passed to the rclone command.
    :parm env_vars: Environment variables used when executing the rclone command.
     Useful to pass secrets to the command, since all arguments and options will be logged.
    """

    remote_type = "local"
    rclone_bin = "rclone"
    default_options = [
        #  Number of file transfers to run in parallel.
        "--transfers=8",
        "--verbose",
    ]
    env_vars = {}

    def build_target(self, path):
        """
        Build the proper target using the current remote type.

        We start the remote with `:` to create it on the fly,
        instead of having to create a configuration file.
        See https://rclone.org/docs/#backend-path-to-dir.

        :param path: Path to the remote target.
        """
        return f":{self.remote_type}:{path}"

    def execute(self, action, args, options=None):
        """
        Execute an rclone subcommand.

        :param action: Name of the subcommand.
        :param list args: List of positional arguments passed the to command.
        :param list options: List of options passed to the command.
        """
        options = options or []
        command = [
            self.rclone_bin,
            action,
            *self.default_options,
            *options,
            "--",
            *args,
        ]
        env = os.environ.copy()
        # env = {}
        env.update(self.env_vars)
        log.info("Executing rclone command.", command=command)
        log.debug("env", env=env)
        result = subprocess.run(
            command,
            capture_output=True,
            env=env,
            # TODO: Fail or let the called decide what to do?
            check=True,
        )
        log.debug(
            "Result.",
            stdout=result.stdout.decode(),
            stderr=result.stderr.decode(),
            exit_code=result.returncode,
        )
        return result

    def sync(self, source, destination):
        """
        Run the `rclone sync` command.

        See https://rclone.org/commands/rclone_sync/.

        :params source: Local path to the source directory.
        :params destination: Remote path to the destination directory.
        """
        # TODO: check if source can be a symlink.
        return self.execute("sync", args=[source, self.build_target(destination)])


class RCloneS3Remote(RClone):

    """
    RClone remote implementation for S3.

    All secrets will be passed as environ variables.

    See https://rclone.org/s3/.

    :params bucket_name: Name of the S3 bucket.
    :params access_key_id: AWS access key id.
    :params secret_acces_key: AWS secret access key.
    :params region: AWS region.
    :params provider: S3 provider, defaults to ``AWS``.
     Useful to use Minio during development.
     See https://rclone.org/s3/#s3-provider.
    :param acl: Canned ACL used when creating buckets and storing or copying objects.
     See https://rclone.org/s3/#s3-acl.
    :param endpoint: Custom S3 endpoint, useful for development.
    """

    remote_type = "s3"

    def __init__(
        self,
        bucket_name,
        access_key_id,
        secret_acces_key,
        region,
        provider="AWS",
        acl=None,
        endpoint=None,
    ):
        super().__init__()

        # When using minion, the region is set to None.
        region = region or ""

        # rclone S3 options passed as env vars.
        # https://rclone.org/s3/#standard-options.
        self.env_vars = {
            "RCLONE_S3_PROVIDER": provider,
            "RCLONE_S3_ACCESS_KEY_ID": access_key_id,
            "RCLONE_S3_SECRET_ACCESS_KEY": secret_acces_key,
            "RCLONE_S3_REGION": region,
            "RCLONE_S3_LOCATION_CONSTRAINT": region,
        }
        if acl:
            self.env_vars["RCLONE_S3_ACL"] = acl
        if endpoint:
            self.env_vars["RCLONE_S3_ENDPOINT"] = endpoint
        self.bucket_name = bucket_name

    def build_target(self, path):
        """Overridden to prepend the bucket name to the path."""
        path = f"{self.bucket_name}/{path}"
        return super().build_target(path)
