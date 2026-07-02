#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["boto3"]
# ///
"""
Mirror pre-compiled build tools from the production S3 buckets into the local
development instance.

It reads ``constants_docker.py`` from readthedocs.org to know which OS, tools and
versions exist, figures out which ones are NOT yet cached in the local instance,
and (by default) downloads each missing tarball from production and uploads it to
the local ``build-tools`` bucket using boto3.

The cached tarballs are named ``<os>-<tool>-<version>.tar.gz`` (e.g.
``ubuntu-24.04-python-3.12.13.tar.gz``) and live in the
``readthedocs-build-tools-prod`` and ``readthedocsinc-build-tools-prod`` buckets.

Downloads from production read the prod buckets, so AWS credentials with access
to them must be provided via environment variables (``AWS_ACCESS_KEY_ID`` and
``AWS_SECRET_ACCESS_KEY``, plus ``AWS_SESSION_TOKEN``/``AWS_DEFAULT_REGION`` if
needed) before running the script. Uploads to the local instance use the
rustfs/MinIO credentials (``admin``/``password`` against
``http://localhost:9000`` by default), independent of those env vars.

The development instance must be running so the script can connect to it and list
what's already cached in the ``build-tools`` bucket. Start it with ``inv
docker.up`` from the readthedocs.org (org) or readthedocs-corporate (com)
checkout. If the instance is not running (or the bucket doesn't exist yet),
nothing is considered cached and every version is mirrored.

Use ``--only-print`` to skip the transfer and instead print the equivalent
``aws s3 cp`` commands. Use ``--no-check`` to ignore what's already cached and
process every version.

Usage:

    AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... \
        uv run --script build_tools_download.py --org
    uv run --script build_tools_download.py --only-print
    uv run --script build_tools_download.py --path /path/to/constants_docker.py
"""

import argparse
import importlib.util
import sys
import tempfile
from pathlib import Path

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

DEFAULT_CONSTANTS_PATH = (
    Path(__file__).resolve().parent.parent
    / "readthedocs"
    / "builds"
    / "constants_docker.py"
)

# The two prod S3 buckets, named "<bucket>-build-tools-prod".
BUCKETS = ["readthedocs", "readthedocsinc"]

# Local S3-compatible instance (rustfs/MinIO) defaults.
LOCAL_ENDPOINT = "http://localhost:9000"
LOCAL_ACCESS_KEY = "admin"
LOCAL_SECRET_KEY = "password"
LOCAL_BUCKET = "build-tools"


def load_settings(path):
    """Import ``constants_docker.py`` from an arbitrary path and return its settings."""
    spec = importlib.util.spec_from_file_location("constants_docker", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.RTD_DOCKER_BUILD_SETTINGS


def iter_versions(settings):
    """Yield ``(os_name, tool, version)`` for every combination in the settings."""
    # "ubuntu-lts-latest" is an alias pointing to a real OS, not a compiled
    # tarball, so it has no object in the bucket.
    os_names = sorted(
        os_name for os_name in settings["os"] if os_name != "ubuntu-lts-latest"
    )
    for os_name in os_names:
        for tool, versions in settings["tools"].items():
            # ``versions`` maps aliases (e.g. "3.12", "latest") to full versions
            # (e.g. "3.12.13"); dedupe on the full version value since several
            # aliases point to the same compiled tarball.
            for version in sorted(set(versions.values())):
                yield os_name, tool, version


def local_client(endpoint, access_key, secret_key):
    """Return a boto3 S3 client pointed at the local rustfs/MinIO instance."""
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4"),
    )


def local_keys(client, bucket):
    """Return the set of object keys present in the local bucket (empty if missing)."""
    keys = set()
    paginator = client.get_paginator("list_objects_v2")
    try:
        for page in paginator.paginate(Bucket=bucket):
            for obj in page.get("Contents", []):
                keys.add(obj["Key"])
    except ClientError as exc:
        # Bucket does not exist yet: nothing is cached locally.
        if exc.response["Error"]["Code"] in ("NoSuchBucket", "404"):
            return set()
        raise
    return keys


def prod_keys_for(client, bucket, prefix):
    """Return the object keys in the prod bucket matching ``<os>-<tool>-<version>``."""
    keys = []
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            keys.append(obj["Key"])
    return keys


def command_for(os_name, tool, version, buckets):
    """Build the ``aws s3 cp`` command for a single (os, tool, version)."""
    pattern = f"{os_name}-{tool}-{version}*"
    return [
        f"aws s3 cp s3://{bucket}-build-tools-prod . --recursive "
        f'--exclude="*" --include="{pattern}"'
        for bucket in buckets
    ]


def mirror_key(prod, local, prod_bucket, local_bucket, key):
    """Download ``key`` from ``prod_bucket`` and upload it to the local bucket."""
    with tempfile.NamedTemporaryFile() as tmp:
        prod.download_fileobj(prod_bucket, key, tmp)
        tmp.flush()
        tmp.seek(0)
        local.upload_fileobj(tmp, local_bucket, key)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--path",
        type=Path,
        default=DEFAULT_CONSTANTS_PATH,
        help="Path to constants_docker.py (default: %(default)s)",
    )
    parser.add_argument(
        "--only-print",
        action="store_true",
        help="Print the equivalent 'aws s3 cp' commands instead of transferring.",
    )
    parser.add_argument(
        "--no-check",
        action="store_true",
        help="Process every version, skipping the local existence check.",
    )
    parser.add_argument(
        "--org",
        action="store_true",
        help="Use the readthedocs (.org) prod bucket.",
    )
    parser.add_argument(
        "--com",
        action="store_true",
        help="Use the readthedocsinc (.com) prod bucket.",
    )
    parser.add_argument("--endpoint-url", default=LOCAL_ENDPOINT)
    parser.add_argument("--access-key", default=LOCAL_ACCESS_KEY)
    parser.add_argument("--secret-key", default=LOCAL_SECRET_KEY)
    parser.add_argument("--local-bucket", default=LOCAL_BUCKET)
    args = parser.parse_args()

    # Select buckets; default to both when neither flag is given.
    buckets = []
    if args.org:
        buckets.append("readthedocs")
    if args.com:
        buckets.append("readthedocsinc")
    if not buckets:
        buckets = BUCKETS

    settings = load_settings(args.path)

    local = local_client(args.endpoint_url, args.access_key, args.secret_key)

    existing = set()
    if not args.no_check:
        existing = local_keys(local, args.local_bucket)

    # Prod client only needed when actually transferring.
    prod = None if args.only_print else boto3.client("s3")

    for os_name, tool, version in iter_versions(settings):
        prefix = f"{os_name}-{tool}-{version}"
        if any(key.startswith(prefix) for key in existing):
            # Already cached locally, skip it.
            continue

        if args.only_print:
            for command in command_for(os_name, tool, version, buckets):
                print(command)
            continue

        for bucket in buckets:
            prod_bucket = f"{bucket}-build-tools-prod"
            keys = prod_keys_for(prod, prod_bucket, prefix)
            if not keys:
                print(f"  not found in {prod_bucket}: {prefix}*", file=sys.stderr)
                continue
            for key in keys:
                print(f"mirroring {prod_bucket}/{key} -> {args.local_bucket}/{key}")
                mirror_key(prod, local, prod_bucket, args.local_bucket, key)


if __name__ == "__main__":
    main()
