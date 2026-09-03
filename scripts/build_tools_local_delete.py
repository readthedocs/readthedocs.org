#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["boto3"]
# ///
"""
Prune build tools from the local development instance that are no longer allowed.

It reads ``constants_docker.py`` from readthedocs.org to know which OS, tools and
versions are still allowed, lists what's cached in the local ``build-tools``
bucket, and deletes any tarball that is no longer in the allowed set.

This is the inverse of ``build_tools_download.py``. It removes tarballs for:

- OS images that were dropped (e.g. ``ubuntu-20.04-python-3.12.13.tar.gz`` once
  ``ubuntu-20.04`` is gone from the settings).
- Tool versions that were dropped (e.g. ``ubuntu-24.04-python-3.10.20.tar.gz``
  once Python 3.10 is gone from the settings).

The cached tarballs are named ``<os>-<tool>-<version>.tar.gz`` (e.g.
``ubuntu-24.04-python-3.12.13.tar.gz``). A tarball is kept only when its
``<os>-<tool>-<version>`` stem exactly matches an allowed combination.

It operates on the local S3-compatible instance (rustfs/MinIO), using its
credentials (``admin``/``password`` against ``http://localhost:9000`` by
default). The development instance must be running. Start it with ``inv
docker.up`` from the readthedocs.org (org) or readthedocs-corporate (com)
checkout.

For safety it runs as a DRY RUN by default, only listing what it would delete.
Pass ``--delete`` to actually remove the objects.

Usage:

    uv run --script build_tools_local_delete.py            # dry run
    uv run --script build_tools_local_delete.py --delete   # actually delete
    uv run --script build_tools_local_delete.py --path /path/to/constants_docker.py
"""

import argparse
import importlib.util
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


def allowed_stems(settings):
    """Return the set of allowed ``<os>-<tool>-<version>`` stems."""
    # "ubuntu-lts-latest" is an alias pointing to a real OS, not a compiled
    # tarball, so it has no object in the bucket.
    os_names = [
        os_name for os_name in settings["os"] if os_name != "ubuntu-lts-latest"
    ]
    stems = set()
    for os_name in os_names:
        for tool, versions in settings["tools"].items():
            # ``versions`` maps aliases (e.g. "3.12", "latest") to full versions
            # (e.g. "3.12.13"); dedupe on the full version value since several
            # aliases point to the same compiled tarball.
            for version in set(versions.values()):
                stems.add(f"{os_name}-{tool}-{version}")
    return stems


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
    """Return the list of object keys present in the local bucket (empty if missing)."""
    keys = []
    paginator = client.get_paginator("list_objects_v2")
    try:
        for page in paginator.paginate(Bucket=bucket):
            for obj in page.get("Contents", []):
                keys.append(obj["Key"])
    except ClientError as exc:
        # Bucket does not exist yet: nothing to prune.
        if exc.response["Error"]["Code"] in ("NoSuchBucket", "404"):
            return []
        raise
    return keys


def is_allowed(key, stems):
    """Return True if ``key`` belongs to an allowed ``<os>-<tool>-<version>`` stem.

    The stem must be followed by a version boundary (``.`` for the ``.tar.gz``
    extension, or ``-`` for any variant suffix) so that e.g. ``3.12.13`` does not
    match a stray ``3.12.135`` key.
    """
    for stem in stems:
        if key.startswith(stem) and (key == stem or key[len(stem)] in ".-"):
            return True
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--path",
        type=Path,
        default=DEFAULT_CONSTANTS_PATH,
        help="Path to constants_docker.py (default: %(default)s)",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Actually delete the objects (default is a dry run).",
    )
    parser.add_argument("--endpoint-url", default=LOCAL_ENDPOINT)
    parser.add_argument("--access-key", default=LOCAL_ACCESS_KEY)
    parser.add_argument("--secret-key", default=LOCAL_SECRET_KEY)
    parser.add_argument("--local-bucket", default=LOCAL_BUCKET)
    args = parser.parse_args()

    settings = load_settings(args.path)
    stems = allowed_stems(settings)

    client = local_client(args.endpoint_url, args.access_key, args.secret_key)
    keys = local_keys(client, args.local_bucket)

    to_delete = [key for key in sorted(keys) if not is_allowed(key, stems)]

    if not to_delete:
        print(f"Nothing to prune: all {len(keys)} objects are allowed.")
        return

    for key in to_delete:
        if args.delete:
            client.delete_object(Bucket=args.local_bucket, Key=key)
            print(f"deleted {args.local_bucket}/{key}")
        else:
            print(f"would delete {args.local_bucket}/{key}")

    verb = "Deleted" if args.delete else "Would delete"
    print(f"\n{verb} {len(to_delete)} of {len(keys)} objects.")
    if not args.delete:
        print("Re-run with --delete to remove them.")


if __name__ == "__main__":
    main()
