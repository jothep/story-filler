"""Back up local Compose data and restore only into new, isolated Docker volumes."""

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import select
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import uuid

from recovery_archive import (
    MAX_BUNDLE_BYTES,
    RecoveryError,
    media_fingerprints,
    validate_bundle,
    write_manifest,
)

# Official postgres:16-alpine multi-platform index, checked 2 November 2026.
# Images must be pulled explicitly by the operator; recovery never pulls images.
POSTGRES_IMAGE = (
    "postgres:16-alpine@sha256:"
    "0cefaabd882e42bcb2a2f3dc56d3ce4770560ba62fd7f197f1a2e008fd5731ab"
)
OPERATION_LABEL = "org.story-filler.recovery.operation"
PROJECT_LABEL = "com.docker.compose.project"
SERVICE_LABEL = "com.docker.compose.service"
BUNDLE_FILES = ("database.dump", "media.tar", "manifest.json")
COMMAND_TIMEOUT = 600


def require_identifier(value, description, database=False):
    pattern = (
        r"[A-Za-z_][A-Za-z0-9_]{0,62}"
        if database
        else r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}"
    )
    if not re.fullmatch(pattern, value):
        raise RecoveryError(f"Invalid {description}; use a simple identifier.")
    return value


class Docker:
    """Run bounded commands against one explicit local Docker Unix socket."""

    def __init__(self, host):
        if (
            not host
            or not host.startswith("unix:///")
            or any(c in host for c in "\x00\n\r?#")
        ):
            raise RecoveryError("Choose an explicit local Docker Unix socket.")
        self.prefix = ["docker", "--host", host]

    def command(self, arguments, stage, *, source=None, destination=None, limit=None):
        environment = os.environ.copy()
        for key in (
            "DOCKER_HOST",
            "DOCKER_CONTEXT",
            "DOCKER_TLS_VERIFY",
            "DOCKER_CERT_PATH",
        ):
            environment.pop(key, None)
        limit = limit if limit is not None else 2 * 1024 * 1024
        captured = bytearray()
        deadline = time.monotonic() + COMMAND_TIMEOUT
        try:
            with subprocess.Popen(
                [*self.prefix, *arguments],
                stdin=source if source is not None else subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                env=environment,
            ) as process:
                try:
                    total = 0
                    while True:
                        remaining = deadline - time.monotonic()
                        if (
                            remaining <= 0
                            or not select.select([process.stdout], [], [], remaining)[0]
                        ):
                            raise RecoveryError(f"Timed out during {stage}.")
                        chunk = os.read(process.stdout.fileno(), 64 * 1024)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > limit:
                            raise RecoveryError(
                                f"Output limit exceeded during {stage}."
                            )
                        if destination is None:
                            captured.extend(chunk)
                        else:
                            destination.write(chunk)
                    if process.wait(timeout=max(0.1, deadline - time.monotonic())):
                        raise RecoveryError(f"Docker command failed during {stage}.")
                finally:
                    if process.poll() is None:
                        process.kill()
                        process.wait()
        except (OSError, subprocess.TimeoutExpired) as error:
            raise RecoveryError(f"Could not complete {stage}.") from error
        return bytes(captured)

    def text(self, arguments, stage):
        try:
            return self.command(arguments, stage).decode("utf-8").strip()
        except UnicodeError as error:
            raise RecoveryError(f"Invalid response during {stage}.") from error

    def inspect(self, kind, name, field):
        output = self.text(
            [kind, "inspect", "--format", "{{json " + field + "}}", name],
            "resource inspection",
        )
        try:
            return json.loads(output)
        except (ValueError, TypeError) as error:
            raise RecoveryError("Docker returned invalid resource metadata.") from error

    def require_image(self):
        self.text(
            ["image", "inspect", "--format", "{{.Id}}", POSTGRES_IMAGE],
            "image availability check",
        )

    def sql(self, container, database, user, query):
        return self.text(
            [
                "exec",
                container,
                "psql",
                "-X",
                "--no-password",
                "--host=/var/run/postgresql",
                "--port=5432",
                f"--username={user}",
                f"--dbname={database}",
                "--set=ON_ERROR_STOP=1",
                "--tuples-only",
                "--no-align",
                "--command",
                query,
            ],
            "database verification",
        )


def verify_source(docker, args):
    """Inspect metadata only; never start or stop an existing service."""
    if not args.writers_stopped:
        raise RecoveryError(
            "Stop application and external writers, then confirm --writers-stopped."
        )
    for name in ("project", "db_container", "media_volume"):
        require_identifier(getattr(args, name), name.replace("_", " "))
    for name in ("database", "db_user"):
        require_identifier(getattr(args, name), name.replace("_", " "), database=True)
    labels = docker.inspect("container", args.db_container, ".Config.Labels") or {}
    if labels.get(PROJECT_LABEL) != args.project or labels.get(SERVICE_LABEL) != "db":
        raise RecoveryError(
            "The database container does not belong to the selected Compose project."
        )
    if docker.inspect("container", args.db_container, ".State.Running") is not True:
        raise RecoveryError("The source database must already be running.")
    backends = docker.text(
        [
            "ps",
            "--all",
            "--quiet",
            "--filter",
            f"label={PROJECT_LABEL}={args.project}",
            "--filter",
            f"label={SERVICE_LABEL}=backend",
        ],
        "application state check",
    ).split()
    if not backends:
        raise RecoveryError("No backend container was found for the selected project.")
    if any(
        docker.inspect("container", name, ".State.Running") is not False
        for name in backends
    ):
        raise RecoveryError("Stop the project's backend containers before backing up.")
    for container in backends:
        media_mounts = [
            mount
            for mount in docker.inspect("container", container, ".Mounts")
            if mount.get("Destination") == "/app/media"
        ]
        if len(media_mounts) != 1 or any(
            mount.get("Type") != "volume" or mount.get("Name") != args.media_volume
            for mount in media_mounts
        ):
            raise RecoveryError(
                "The selected volume is not the backend's named media volume."
            )
    labels = docker.inspect("volume", args.media_volume, ".Labels") or {}
    if labels.get(PROJECT_LABEL) != args.project:
        raise RecoveryError(
            "The media volume does not belong to the selected Compose project."
        )
    for container in docker.text(["ps", "--quiet"], "media writer check").split():
        mounts = docker.inspect("container", container, ".Mounts")
        if any(
            mount.get("Name") == args.media_volume and mount.get("RW")
            for mount in mounts
        ):
            raise RecoveryError(
                "A running container still has write access to the media volume."
            )
    version = docker.sql(
        args.db_container, args.database, args.db_user, "SHOW server_version_num"
    )
    tool = docker.text(
        ["exec", args.db_container, "pg_dump", "--version"], "dump version check"
    )
    if (
        not version.isdecimal()
        or int(version) // 10000 != 16
        or not re.match(r"pg_dump \(PostgreSQL\) 16\.", tool)
    ):
        raise RecoveryError(
            "Local recovery requires PostgreSQL server and pg_dump major 16."
        )
    docker.require_image()


@contextmanager
def private_output(path):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as output:
        yield output


def backup(docker, args):
    verify_source(docker, args)
    output = Path(args.output)
    output.mkdir(mode=0o700)
    # An incomplete directory deliberately has no manifest and cannot be restored.
    with private_output(output / "database.dump") as dump:
        docker.command(
            [
                "exec",
                args.db_container,
                "pg_dump",
                "--format=custom",
                "--no-owner",
                "--no-acl",
                "--no-password",
                "--host=/var/run/postgresql",
                "--port=5432",
                f"--username={args.db_user}",
                f"--dbname={args.database}",
            ],
            "database backup",
            destination=dump,
            limit=MAX_BUNDLE_BYTES,
        )
    with private_output(output / "media.tar") as media:
        run_helper(
            docker,
            [
                "--cap-drop=ALL",
                "--mount",
                f"type=volume,src={args.media_volume},dst=/source,readonly",
                "--entrypoint=tar",
                POSTGRES_IMAGE,
                "-cf",
                "-",
                "-C",
                "/source",
                ".",
            ],
            "media backup",
            destination=media,
            limit=MAX_BUNDLE_BYTES - (output / "database.dump").stat().st_size,
        )
    # Recheck that a writer did not restart during the two exports.
    verify_source(docker, args)
    write_manifest(output, postgres_major=16)
    os.chmod(output / "manifest.json", 0o600)
    return {"backup_directory": str(output), "status": "complete"}


def snapshot_bundle(source, destination):
    """Copy only regular payload files into a private directory before validation."""
    directory = os.open(source, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    total = 0
    try:
        if set(os.listdir(directory)) != set(BUNDLE_FILES):
            raise RecoveryError("The recovery bundle has missing or unexpected files.")
        for name in BUNDLE_FILES:
            descriptor = os.open(
                name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory
            )
            with os.fdopen(descriptor, "rb") as original:
                metadata = os.fstat(original.fileno())
                if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                    raise RecoveryError(
                        "Backup payloads must be ordinary, unlinked files."
                    )
                limit = 64 * 1024 if name == "manifest.json" else MAX_BUNDLE_BYTES
                if metadata.st_size > limit:
                    raise RecoveryError("Backup payload exceeds the supported size.")
                with private_output(Path(destination) / name) as copied:
                    while chunk := original.read(64 * 1024):
                        total += len(chunk)
                        if total > MAX_BUNDLE_BYTES + 64 * 1024:
                            raise RecoveryError(
                                "Backup bundle exceeds the supported size."
                            )
                        copied.write(chunk)
    finally:
        os.close(directory)


def canonical_media_tar(source, destination):
    """Copy validated members without archived ownership or restrictive modes."""
    with tarfile.open(source, "r:") as original, private_output(destination) as output:
        with tarfile.open(fileobj=output, mode="w") as result:
            for member in original:
                clean = tarfile.TarInfo(member.name)
                clean.type = tarfile.DIRTYPE if member.isdir() else tarfile.REGTYPE
                clean.mode = 0o755 if member.isdir() else 0o644
                clean.size = 0 if member.isdir() else member.size
                payload = None if member.isdir() else original.extractfile(member)
                try:
                    result.addfile(clean, payload)
                finally:
                    if payload is not None:
                        payload.close()


def comparable_media(path):
    # Include implicit parents so a valid archive need not list every directory.
    entries = media_fingerprints(path)
    entries.pop(".", None)
    for name in list(entries):
        for parent in Path(name).parents:
            if str(parent) != ".":
                entries.setdefault(parent.as_posix(), {"type": "directory"})
    return entries


class RestoreResources:
    """Keep exact ownership of new resources; never accept caller-chosen targets."""

    def __init__(self, docker):
        self.docker = docker
        self.operation = uuid.uuid4().hex
        self.prefix = f"story-filler-recovery-{self.operation}"
        self.volumes = []
        self.containers = []

    def label(self):
        return f"{OPERATION_LABEL}={self.operation}"

    def create_volume(self, suffix):
        name = f"{self.prefix}-{suffix}"
        existing = self.docker.text(
            ["volume", "ls", "--quiet"], "target name check"
        ).split()
        if name in existing:
            raise RecoveryError(
                "A generated recovery volume already exists; "
                "existing volumes cannot be reused."
            )
        self.volumes.append(name)
        self.docker.text(
            ["volume", "create", "--label", self.label(), name], "new volume creation"
        )
        labels = self.docker.inspect("volume", name, ".Labels") or {}
        if labels.get(OPERATION_LABEL) != self.operation:
            raise RecoveryError("New volume ownership could not be confirmed.")
        return name

    def run(
        self, suffix, arguments, stage, *, source=None, destination=None, limit=None
    ):
        name = f"{self.prefix}-{suffix}"
        existing = self.docker.text(
            ["ps", "--all", "--format", "{{.Names}}"], "target name check"
        ).split()
        if name in existing:
            raise RecoveryError("A generated recovery container already exists.")
        # Track the name before run so a partially created container is cleaned up.
        self.containers.append(name)
        result = self.docker.command(
            [
                "run",
                "--name",
                name,
                "--label",
                self.label(),
                "--pull=never",
                "--network=none",
                "--security-opt=no-new-privileges",
                *arguments,
            ],
            stage,
            source=source,
            destination=destination,
            limit=limit,
        )
        labels = self.docker.inspect("container", name, ".Config.Labels") or {}
        if labels.get(OPERATION_LABEL) != self.operation:
            raise RecoveryError("New container ownership could not be confirmed.")
        return name, result

    def cleanup(self, *, volumes):
        failures = []
        for kind, names in (
            ("container", self.containers),
            ("volume", self.volumes if volumes else []),
        ):
            for name in reversed(names):
                field = ".Config.Labels" if kind == "container" else ".Labels"
                try:
                    list_arguments = (
                        ["ps", "--all", "--format", "{{.Names}}"]
                        if kind == "container"
                        else ["volume", "ls", "--quiet"]
                    )
                    if (
                        name
                        not in self.docker.text(
                            list_arguments, "recovery cleanup inspection"
                        ).split()
                    ):
                        continue
                    labels = self.docker.inspect(kind, name, field) or {}
                    if labels.get(OPERATION_LABEL) != self.operation:
                        failures.append(name)
                        continue
                    arguments = (
                        [kind, "rm", "--force", "--volumes", name]
                        if kind == "container"
                        else [kind, "rm", name]
                    )
                    self.docker.text(arguments, "recovery cleanup")
                except RecoveryError:
                    failures.append(name)
        return failures


def run_helper(docker, arguments, stage, **streams):
    """Clean up a named helper even when its attached Docker client is killed."""
    resources = RestoreResources(docker)
    try:
        _, result = resources.run("helper", arguments, stage, **streams)
        return result
    finally:
        if resources.cleanup(volumes=False):
            raise RecoveryError(
                "Helper cleanup needs review; operation " + resources.operation
            )


def wait_for_database(docker, container):
    for _ in range(30):
        try:
            # The official image first starts a temporary initialization server.
            # Wait until PID 1 is the final server before importing the dump.
            process = docker.text(
                ["exec", container, "cat", "/proc/1/comm"], "database readiness check"
            )
            if (
                process == "postgres"
                and docker.sql(container, "recovery", "recovery", "SELECT 1") == "1"
            ):
                return
        except RecoveryError:
            pass
        time.sleep(1)
    raise RecoveryError("The isolated recovery database did not become ready.")


def restore(docker, args):
    if not args.trusted_backup:
        raise RecoveryError(
            "Confirm --trusted-backup only for a backup from a trusted local database."
        )
    with tempfile.TemporaryDirectory(prefix="story-filler-recovery-") as temporary:
        bundle = Path(temporary)
        snapshot_bundle(args.bundle, bundle)
        validate_bundle(bundle)
        docker.require_image()
        with (bundle / "database.dump").open("rb") as dump:
            run_helper(
                docker,
                [
                    "--cap-drop=ALL",
                    "--interactive",
                    "--entrypoint=pg_restore",
                    POSTGRES_IMAGE,
                    "--list",
                ],
                "dump readability check",
                source=dump,
            )
        canonical_media_tar(bundle / "media.tar", bundle / "normalized-media.tar")
        resources = RestoreResources(docker)
        try:
            database_volume = resources.create_volume("database")
            media_volume = resources.create_volume("media")
            container, _ = resources.run(
                "database",
                [
                    "--detach",
                    "--env=POSTGRES_DB=recovery",
                    "--env=POSTGRES_USER=recovery",
                    "--env=POSTGRES_HOST_AUTH_METHOD=trust",
                    "--mount",
                    f"type=volume,src={database_volume},dst=/var/lib/postgresql/data",
                    POSTGRES_IMAGE,
                ],
                "isolated database startup",
            )
            # Trust authentication is confined to this network-less container.
            # No ports, host directories, production settings or secrets are shared.
            wait_for_database(docker, container)
            with (bundle / "database.dump").open("rb") as dump:
                docker.command(
                    [
                        "exec",
                        "--interactive",
                        container,
                        "pg_restore",
                        "--host=/var/run/postgresql",
                        "--port=5432",
                        "--username=recovery",
                        "--dbname=recovery",
                        "--no-password",
                        "--single-transaction",
                        "--exit-on-error",
                        "--no-owner",
                        "--no-privileges",
                    ],
                    "database restore",
                    source=dump,
                )
            resources.run(
                "media-owner",
                [
                    "--cap-drop=ALL",
                    "--cap-add=CHOWN",
                    "--mount",
                    f"type=volume,src={media_volume},dst=/media",
                    "--entrypoint=chown",
                    POSTGRES_IMAGE,
                    "1000:1000",
                    "/media",
                ],
                "new media ownership setup",
            )
            with (bundle / "normalized-media.tar").open("rb") as media:
                resources.run(
                    "media-extract",
                    [
                        "--interactive",
                        "--user=1000:1000",
                        "--cap-drop=ALL",
                        "--mount",
                        f"type=volume,src={media_volume},dst=/media",
                        "--entrypoint=tar",
                        POSTGRES_IMAGE,
                        "--no-same-owner",
                        "-xf",
                        "-",
                        "-C",
                        "/media",
                    ],
                    "media restore",
                    source=media,
                )
            table_count = docker.sql(
                container,
                "recovery",
                "recovery",
                "SELECT count(*) FROM information_schema.tables "
                "WHERE table_schema NOT IN ('pg_catalog', 'information_schema')",
            )
            if not table_count.isdecimal() or int(table_count) == 0:
                raise RecoveryError(
                    "The restored database contains no application tables."
                )
            with private_output(bundle / "restored-media.tar") as media:
                resources.run(
                    "media-verify",
                    [
                        "--cap-drop=ALL",
                        "--user=1000:1000",
                        "--mount",
                        f"type=volume,src={media_volume},dst=/media,readonly",
                        "--entrypoint=tar",
                        POSTGRES_IMAGE,
                        "-cf",
                        "-",
                        "-C",
                        "/media",
                        ".",
                    ],
                    "restored media verification",
                    destination=media,
                    limit=MAX_BUNDLE_BYTES,
                )
            if comparable_media(bundle / "media.tar") != comparable_media(
                bundle / "restored-media.tar"
            ):
                raise RecoveryError("Restored media does not match the backup.")
        except BaseException:
            failures = resources.cleanup(volumes=True)
            if failures:
                print(
                    "Isolated resources require manual cleanup; operation "
                    + resources.operation,
                    file=sys.stderr,
                )
            raise
        # Remove helpers only. The isolated database and both volumes remain for review.
        resources.containers.remove(container)
        failures = resources.cleanup(volumes=False)
        if failures:
            raise RecoveryError(
                "Recovery completed but helper cleanup needs review; operation "
                + resources.operation
            )
        return {
            "operation_id": resources.operation,
            "database_container": container,
            "database_volume": database_volume,
            "media_volume": media_volume,
            "database": "recovery",
            "database_user": "recovery",
            "status": "verified",
        }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    backup_parser = commands.add_parser(
        "backup", help="Export a stopped-writer local Compose application"
    )
    for option in (
        "docker-host",
        "project",
        "db-container",
        "database",
        "db-user",
        "media-volume",
        "output",
    ):
        backup_parser.add_argument("--" + option, required=True)
    backup_parser.add_argument("--writers-stopped", action="store_true")
    verify_parser = commands.add_parser(
        "verify", help="Validate backup files without Docker"
    )
    verify_parser.add_argument("--bundle", required=True)
    restore_parser = commands.add_parser(
        "restore", help="Restore a trusted backup into new isolated resources"
    )
    restore_parser.add_argument("--docker-host", required=True)
    restore_parser.add_argument("--bundle", required=True)
    restore_parser.add_argument("--trusted-backup", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            validate_bundle(args.bundle)
            result = {"status": "valid"}
        else:
            docker = Docker(args.docker_host)
            result = (
                backup(docker, args)
                if args.command == "backup"
                else restore(docker, args)
            )
        print(json.dumps(result, sort_keys=True))
        return 0
    except (RecoveryError, OSError, ValueError, tarfile.TarError):
        # Do not expose a database error, SQL text, host path or command stderr.
        error = sys.exception()
        message = (
            str(error)
            if isinstance(error, RecoveryError)
            else "Local recovery failed while handling backup files."
        )
        print("ERROR: " + message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
