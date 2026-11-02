"""Check the final application image offline, using its default runtime user.

The host supplies pins parsed by check_dependency_audit.read_lock and the lock's
SHA-256. No packages are installed, cloud requests made, or credentials read.
Feed this file to the candidate image's Python interpreter through stdin.
"""

import argparse
import bz2
import ctypes
import hashlib
import importlib
import importlib.metadata
import importlib.util
import io
import json
import lzma
import os
from pathlib import Path
import re
import secrets
import shutil
import sqlite3
import ssl
import subprocess
import sys
import zlib


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def check_packages(expected, lock_sha256):
    lock = Path("/app/requirements.txt").read_bytes()
    require(
        hashlib.sha256(lock).hexdigest() == lock_sha256,
        "Image lock differs from reviewed source",
    )
    installed = {}
    for distribution in importlib.metadata.distributions():
        name = re.sub(r"[-_.]+", "-", distribution.metadata["Name"]).lower()
        require(name not in installed, f"Duplicate installed package: {name}")
        installed[name] = distribution.version
    require(
        installed == expected,
        "Installed package names or versions differ from the runtime lock",
    )
    for name in ("pip", "ensurepip", "black", "flake8", "pylint", "pip_audit"):
        require(
            importlib.util.find_spec(name) is None,
            f"Unexpected development tool: {name}",
        )
    for name in ("cc", "gcc", "g++", "clang", "make"):
        require(shutil.which(name) is None, f"Unexpected build tool: {name}")
    print(f"PASS: exactly {len(expected)} locked packages; no installer or build tools")


def check_native_features():
    # Exercise the native modules used by the service, without relying on a
    # distribution-specific library directory or optional GUI components.
    sample = "Kia ora — 你好".encode()
    for module in (bz2, lzma, zlib):
        require(
            module.decompress(module.compress(sample)) == sample,
            "Compression round trip failed",
        )
    require(ctypes.sizeof(ctypes.c_void_p) > 0, "ctypes is unavailable")
    require(ssl.create_default_context().get_ca_certs(), "TLS trust store is empty")
    with sqlite3.connect(":memory:") as database:
        require(
            database.execute("SELECT 42").fetchone() == (42,), "SQLite query failed"
        )
        fts5 = database.execute(
            "SELECT sqlite_compileoption_used('ENABLE_FTS5')"
        ).fetchone()[0]
    print(f"Runtime SQLite {sqlite3.sqlite_version}; FTS5 enabled: {bool(fts5)}")

    import google_crc32c
    import psycopg2

    importlib.import_module("zope.interface._zope_interface_coptimizations")
    require(google_crc32c.implementation == "c", "CRC32C native implementation missing")
    require(google_crc32c.value(b"123456789") == 0xE3069283, "CRC32C result differs")
    from gunicorn.workers.ggevent import GeventWorker
    from PIL import Image

    require(psycopg2.extensions.libpq_version() > 0, "libpq is unavailable")
    require(GeventWorker.__name__ == "GeventWorker", "Gunicorn worker import failed")
    for format_name in ("PNG", "JPEG", "WEBP"):
        data = io.BytesIO()
        Image.new("RGB", (2, 2), "blue").save(data, format=format_name)
        data.seek(0)
        with Image.open(data) as image:
            image.load()
            require(image.size == (2, 2), f"Pillow {format_name} round trip failed")
    print(
        "PASS: native modules, TLS trust store, SQLite, Pillow, "
        "libpq, gevent and CRC32C"
    )
    print("TLS check is offline; it does not test a remote TLS handshake.")


def check_storage_configuration():
    from django.conf import settings
    from django.utils.module_loading import import_string
    from google.auth.credentials import AnonymousCredentials

    require(
        settings.STORAGES["default"]["BACKEND"]
        == "django.core.files.storage.FileSystemStorage",
        "Local storage selection failed",
    )
    require(settings.MEDIA_URL == "/media/", "Local media URL differs")

    # Reload only the settings module to exercise the existing GCS branch. This
    # isolated check does not fetch application-default credentials or objects.
    os.environ.update(USE_GCS="true", GS_BUCKET_NAME="runtime-check.invalid")
    module = importlib.reload(importlib.import_module("maori_story_project.settings"))
    backend = module.STORAGES["default"]["BACKEND"]
    require(
        backend == "storages.backends.gcloud.GoogleCloudStorage",
        "GCS storage selection failed",
    )
    storage = import_string(backend)(
        credentials=AnonymousCredentials(),
        bucket_name="runtime-check.invalid",
        querystring_auth=False,
    )
    require(
        storage.url("probe.png")
        == "https://storage.googleapis.com/runtime-check.invalid/probe.png",
        "GCS public URL generation failed",
    )
    require(
        module.MEDIA_URL == "https://storage.googleapis.com/runtime-check.invalid/",
        "GCS media URL differs",
    )
    os.environ["USE_GCS"] = "false"
    print("PASS: local and GCS configuration/imports; no cloud service was contacted")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-packages-json", required=True)
    parser.add_argument("--lock-sha256", required=True)
    args = parser.parse_args()
    require(
        (os.getuid(), os.getgid()) == (100, 101),
        "Runtime identity must remain app UID 100 / GID 101",
    )
    check_packages(json.loads(args.expected_packages_json), args.lock_sha256)
    check_native_features()
    os.environ.update(
        SECRET_KEY=secrets.token_urlsafe(48),
        DATABASE_URL="sqlite:///:memory:",
        USE_GCS="false",
        DEBUG="false",
        DJANGO_SETTINGS_MODULE="maori_story_project.settings",
    )
    for arguments in (
        ["test"],
        ["check"],
        ["makemigrations", "--check", "--dry-run"],
    ):
        result = subprocess.run(
            [sys.executable, "manage.py", *arguments], capture_output=True, timeout=120
        )
        require(
            result.returncode == 0, f"Django {arguments[0]} failed in the runtime image"
        )
        detail = " ".join(arguments)
        if arguments == ["test"]:
            match = re.search(r"Ran (\d+) tests?", result.stderr.decode())
            require(match is not None, "Django did not report its test count")
            detail += f" ({match[1]} tests)"
        print(f"PASS: Django {detail}")
    check_storage_configuration()
    print("PASS: final runtime image checks completed as a non-root user")


if __name__ == "__main__":
    main()
