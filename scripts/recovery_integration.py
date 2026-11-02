"""Exercise local recovery with synthetic PostgreSQL data and Docker volumes.

Run this entry point explicitly against a local Docker Unix socket. The pinned
PostgreSQL image must already be present. No cloud account, host port, application
container, host-directory mount, or existing Compose project is needed.
"""

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tarfile
import tempfile
import time
from unittest.mock import patch
import uuid

import local_recovery
from local_recovery import POSTGRES_IMAGE

SCRIPT = Path(__file__).with_name("local_recovery.py")
OPERATION_LABEL = "org.story-filler.recovery.operation"
PROJECT_LABEL = "com.docker.compose.project"
SERVICE_LABEL = "com.docker.compose.service"
SOURCE_DATABASE = "source_fixture"
SOURCE_USER = "fixture"

MEDIA_FILES = {
    "source sentinel.txt": b"Keep the original media volume unchanged.\n",
    "story pictures/Māori and 中文.txt": "Kia ora — 你好\n".encode(),
    "word audio/a file with spaces.bin": bytes(range(256)),
}

SEED_SQL = """
CREATE TABLE stories (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL UNIQUE
);
CREATE TABLE paragraphs (
    id BIGSERIAL PRIMARY KEY,
    story_id BIGINT NOT NULL REFERENCES stories(id),
    position INTEGER NOT NULL CHECK (position > 0),
    content TEXT NOT NULL,
    UNIQUE (story_id, position)
);
CREATE TABLE words (
    id BIGSERIAL PRIMARY KEY,
    text TEXT NOT NULL UNIQUE
);
CREATE TABLE story_words (
    story_id BIGINT REFERENCES stories(id),
    word_id BIGINT REFERENCES words(id),
    PRIMARY KEY (story_id, word_id)
);
INSERT INTO stories(title) VALUES ('Māori story — 你好'), ('Source sentinel');
INSERT INTO paragraphs(story_id, position, content) VALUES
    (1, 1, 'Kia ora, te ao.'), (1, 2, 'A second paragraph with 中文.'),
    (2, 1, 'Keep this source record unchanged.');
INSERT INTO words(text) VALUES ('whānau'), ('ocean'), ('家');
INSERT INTO story_words VALUES (1, 1), (1, 3), (2, 2);
SELECT setval('stories_id_seq', 40);
SELECT setval('paragraphs_id_seq', 70);
SELECT setval('words_id_seq', 90);
"""


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


class Integration:
    def __init__(self, docker_host, temporary_directory):
        require(
            docker_host.startswith("unix:///"), "Use an explicit local Unix socket."
        )
        self.root = Path(temporary_directory)
        self.docker_host = docker_host
        self.operation_id = uuid.uuid4().hex
        self.operations = {self.operation_id}
        self.project = f"recovery-test-{self.operation_id}"
        self.database_container = f"{self.project}-db"
        self.media_volume = f"{self.project}-media"
        self.database_volume = f"{self.project}-postgres"
        self.backend_container = f"{self.project}-backend"
        self.environment = {
            key: os.environ[key]
            for key in ("PATH", "HOME", "TMPDIR", "DOCKER_CONFIG")
            if key in os.environ
        }
        self.docker = ["docker", "--host", docker_host]

    def command(self, arguments, *, data=None, check=True, environment=None):
        result = subprocess.run(
            arguments,
            input=data,
            capture_output=True,
            env={**self.environment, **(environment or {})},
            timeout=120,
            check=False,
        )
        if check and result.returncode:
            raise RuntimeError(result.stderr.decode(errors="replace"))
        return result

    def docker_command(self, *arguments, **options):
        return self.command([*self.docker, *arguments], **options)

    def labels(self, service=None):
        labels = [
            "--label",
            f"{OPERATION_LABEL}={self.operation_id}",
            "--label",
            f"{PROJECT_LABEL}={self.project}",
        ]
        if service:
            labels.extend(["--label", f"{SERVICE_LABEL}={service}"])
        return labels

    def cli(self, action, *arguments, expect_failure=False):
        command = [sys.executable, str(SCRIPT), action, *map(str, arguments)]
        if action != "verify":
            command.extend(["--docker-host", self.docker_host])
        result = self.command(command, check=not expect_failure)
        if expect_failure:
            require(result.returncode != 0, f"{action} unexpectedly succeeded.")
        return result

    def backup(self, output, database=SOURCE_DATABASE, expect_failure=False):
        return self.cli(
            "backup",
            "--project",
            self.project,
            "--db-container",
            self.database_container,
            "--database",
            database,
            "--db-user",
            SOURCE_USER,
            "--media-volume",
            self.media_volume,
            "--output",
            output,
            "--writers-stopped",
            expect_failure=expect_failure,
        )

    def sql(self, container, database, user, sql, *, check=True):
        return self.docker_command(
            "exec",
            "--interactive",
            container,
            "psql",
            "--no-psqlrc",
            "--quiet",
            "--tuples-only",
            "--no-align",
            "--set=ON_ERROR_STOP=1",
            "--username",
            user,
            "--dbname",
            database,
            data=sql.encode(),
            check=check,
        )

    def source_sql(self, sql, **options):
        return self.sql(
            self.database_container, SOURCE_DATABASE, SOURCE_USER, sql, **options
        )

    def database_snapshot(self, container, database, user):
        snapshots = {}
        for table in ("stories", "paragraphs", "words", "story_words"):
            query = (
                "SELECT coalesce(jsonb_agg(to_jsonb(record) ORDER BY to_jsonb(record)),"
                f" '[]'::jsonb) FROM {table} record;"
            )
            snapshots[table] = json.loads(
                self.sql(container, database, user, query).stdout
            )
        for name, query in {
            "constraints": """
                SELECT jsonb_agg(jsonb_build_array(c.conname,
                    pg_get_constraintdef(c.oid)) ORDER BY c.conname)
                FROM pg_constraint c JOIN pg_namespace n ON n.oid = c.connamespace
                WHERE n.nspname = 'public';
            """,
            "sequences": """
                SELECT jsonb_agg(jsonb_build_array(sequencename, last_value)
                    ORDER BY sequencename)
                FROM pg_sequences WHERE schemaname = 'public';
            """,
        }.items():
            snapshots[name] = json.loads(
                self.sql(container, database, user, query).stdout
            )
        return snapshots

    def media_hashes(self, volume):
        result = self.docker_command(
            "run",
            "--rm",
            "--pull=never",
            "--network=none",
            *self.labels(),
            "--mount",
            f"type=volume,src={volume},dst=/media,readonly",
            POSTGRES_IMAGE,
            "tar",
            "-cf",
            "-",
            "-C",
            "/media",
            ".",
        )
        with tarfile.open(fileobj=io.BytesIO(result.stdout)) as archive:
            return {
                member.name.removeprefix("./"): hashlib.sha256(
                    archive.extractfile(member).read()
                ).hexdigest()
                for member in archive
                if member.isfile()
            }

    def resource_ids(self):
        containers = self.docker_command("ps", "--all", "--quiet", "--no-trunc")
        volumes = self.docker_command("volume", "ls", "--quiet")
        return set(containers.stdout.splitlines()), set(volumes.stdout.splitlines())

    def resource_events(self, since):
        result = self.docker_command(
            "events",
            "--since",
            f"{since:.9f}",
            "--until",
            f"{time.time():.9f}",
            "--filter",
            "type=container",
            "--filter",
            "type=volume",
            "--format",
            "{{json .}}",
        )
        return [json.loads(line) for line in result.stdout.splitlines()]

    def prepare_source(self):
        self.docker_command("image", "inspect", POSTGRES_IMAGE)
        for volume in (self.database_volume, self.media_volume):
            self.docker_command("volume", "create", *self.labels(), volume)

        self.docker_command(
            "run",
            "--detach",
            "--pull=never",
            "--network=none",
            "--name",
            self.database_container,
            *self.labels("db"),
            "--env",
            f"POSTGRES_USER={SOURCE_USER}",
            "--env",
            f"POSTGRES_DB={SOURCE_DATABASE}",
            "--env",
            "POSTGRES_PASSWORD",
            "--env",
            "POSTGRES_INITDB_ARGS=--encoding=UTF8 --locale=C",
            "--mount",
            f"type=volume,src={self.database_volume},dst=/var/lib/postgresql/data",
            POSTGRES_IMAGE,
            environment={"POSTGRES_PASSWORD": secrets.token_urlsafe(32)},
        )
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            process = self.docker_command(
                "exec", self.database_container, "cat", "/proc/1/comm", check=False
            )
            ready = self.source_sql("SELECT 1;", check=False)
            if process.stdout.strip() == b"postgres" and ready.returncode == 0:
                break
            time.sleep(0.2)
        else:
            raise RuntimeError("The synthetic PostgreSQL source did not become ready.")
        self.source_sql(SEED_SQL)

        # docker cp transfers the fixture; the VM never mounts the host directory.
        archive_path = self.root / "synthetic-media.tar"
        with tarfile.open(archive_path, "w") as archive:
            for name, content in MEDIA_FILES.items():
                member = tarfile.TarInfo(name)
                member.size = len(content)
                archive.addfile(member, io.BytesIO(content))
        seed_container = f"{self.project}-seed"
        self.docker_command(
            "run",
            "--detach",
            "--pull=never",
            "--network=none",
            "--name",
            seed_container,
            *self.labels(),
            "--mount",
            f"type=volume,src={self.media_volume},dst=/media",
            POSTGRES_IMAGE,
            "sleep",
            "120",
        )
        self.docker_command("cp", str(archive_path), f"{seed_container}:/seed.tar")
        self.docker_command(
            "exec", seed_container, "tar", "-xf", "/seed.tar", "-C", "/media"
        )
        self.docker_command("rm", "--force", "--volumes", seed_container)
        self.docker_command(
            "create",
            "--pull=never",
            "--network=none",
            "--name",
            self.backend_container,
            *self.labels("backend"),
            "--mount",
            f"type=volume,src={self.media_volume},dst=/app/media",
            POSTGRES_IMAGE,
            "true",
        )
        self.docker_command("start", "--attach", self.backend_container)

    def check_writable_source_is_rejected(self):
        writer = f"{self.project}-writer"
        self.docker_command(
            "run",
            "--detach",
            "--pull=never",
            "--network=none",
            "--name",
            writer,
            *self.labels(),
            "--mount",
            f"type=volume,src={self.media_volume},dst=/media",
            POSTGRES_IMAGE,
            "sleep",
            "120",
        )
        try:
            output = self.root / "writer-must-block-backup"
            self.backup(output, expect_failure=True)
            require(not output.exists(), "Rejected backup left a published directory.")
        finally:
            self.docker_command("rm", "--force", "--volumes", writer)

    def check_corrupt_backup_is_rejected(self, bundle):
        dump = bundle / "database.dump"
        original = dump.read_bytes()
        try:
            dump.write_bytes(original[:-1] + bytes([original[-1] ^ 1]))
            resources = self.resource_ids()
            started = time.time()
            self.cli(
                "restore", "--bundle", bundle, "--trusted-backup", expect_failure=True
            )
            require(
                self.resource_ids() == resources, "Corrupt backup changed resources."
            )
            require(
                not any(
                    event["Action"] == "create"
                    for event in self.resource_events(started)
                ),
                "Corrupt backup reached resource creation before validation.",
            )
        finally:
            dump.write_bytes(original)

    def check_restored_database(self, restored, expected):
        arguments = (
            restored["database_container"],
            restored["database"],
            restored["database_user"],
        )
        require(
            self.database_snapshot(*arguments) == expected, "Restored SQL data differs."
        )
        for query, expected_id in (
            (
                "INSERT INTO stories(title) VALUES ('Restored-only row') RETURNING id;",
                41,
            ),
            (
                "INSERT INTO paragraphs(story_id, position, content) "
                "VALUES (41, 1, 'New text') RETURNING id;",
                71,
            ),
            ("INSERT INTO words(text) VALUES ('Restored-only word') RETURNING id;", 91),
        ):
            result = self.sql(*arguments, query)
            require(
                int(result.stdout.strip()) == expected_id, "Sequence state was lost."
            )
        for query in (
            "INSERT INTO paragraphs(story_id, position, content) VALUES (999, 1, 'x');",
            "INSERT INTO stories(title) VALUES ('Source sentinel');",
            "INSERT INTO stories(title) VALUES (NULL);",
            "INSERT INTO paragraphs(story_id, position, content) VALUES (1, 0, 'x');",
        ):
            result = self.sql(*arguments, query, check=False)
            require(
                result.returncode != 0, "A restored SQL constraint was not enforced."
            )

    def check_restore_failure_cleanup(self):
        self.docker_command(
            "exec", self.database_container, "mkdir", "/tmp/source-only-tablespace"
        )
        self.docker_command(
            "exec",
            self.database_container,
            "chown",
            "postgres",
            "/tmp/source-only-tablespace",
        )
        self.source_sql(
            "CREATE TABLESPACE fixture_space LOCATION '/tmp/source-only-tablespace';"
            "CREATE DATABASE failure_fixture;"
        )
        self.sql(
            self.database_container,
            "failure_fixture",
            SOURCE_USER,
            "CREATE TABLE needs_missing_tablespace(id INTEGER) "
            "TABLESPACE fixture_space;"
            "INSERT INTO needs_missing_tablespace VALUES (1);",
        )
        bundle = self.root / "valid-bundle-with-unavailable-tablespace"
        self.backup(bundle, database="failure_fixture")
        self.cli("verify", "--bundle", bundle)
        resources = self.resource_ids()
        started = time.time()
        failure = self.cli(
            "restore", "--bundle", bundle, "--trusted-backup", expect_failure=True
        )
        require(
            b"database restore" in failure.stderr,
            "Expected an actual PostgreSQL restore failure.",
        )
        events = self.resource_events(started)
        require(
            any(event["Action"] == "create" for event in events),
            "Failure fixture did not reach staging resource creation.",
        )
        require(
            self.resource_ids() == resources,
            "Failed restore left resources behind or deleted existing resources.",
        )

    def check_helper_failure_cleanup(self, *, timeout):
        resources = self.resource_ids()
        started = time.time()
        command = "sleep 15" if timeout else "printf '0123456789'"
        expected = "Timed out" if timeout else "Output limit exceeded"
        docker = local_recovery.Docker(self.docker_host)
        try:
            with patch.object(local_recovery, "COMMAND_TIMEOUT", 2):
                local_recovery.run_helper(
                    docker,
                    [
                        "--cap-drop=ALL",
                        "--entrypoint=sh",
                        POSTGRES_IMAGE,
                        "-c",
                        command,
                    ],
                    "synthetic helper failure",
                    limit=4,
                )
        except local_recovery.RecoveryError as error:
            require(expected in str(error), "Helper failed for an unexpected reason.")
        else:
            raise RuntimeError("The helper unexpectedly completed successfully.")
        require(
            any(
                event["Type"] == "container" and event["Action"] == "create"
                for event in self.resource_events(started)
            ),
            "The failure test did not create an actual Docker helper.",
        )
        require(
            self.resource_ids() == resources,
            "Helper failure changed existing resources or left a container/volume.",
        )

    def run(self):
        self.prepare_source()
        source_before = self.database_snapshot(
            self.database_container, SOURCE_DATABASE, SOURCE_USER
        )
        expected_media = {
            name: hashlib.sha256(content).hexdigest()
            for name, content in MEDIA_FILES.items()
        }
        require(
            self.media_hashes(self.media_volume) == expected_media, "Fixture mismatch."
        )
        self.check_writable_source_is_rejected()
        print("PASS: an active media writer blocks backup.", flush=True)

        bundle = self.root / "backup with spaces"
        self.backup(bundle)
        self.cli("verify", "--bundle", bundle)
        self.check_corrupt_backup_is_rejected(bundle)
        print("PASS: corrupt backup is rejected before resource creation.", flush=True)

        result = self.cli("restore", "--bundle", bundle, "--trusted-backup")
        restored = json.loads(result.stdout)
        operation = restored["operation_id"]
        require(
            str(uuid.UUID(operation)).replace("-", "") == operation.replace("-", ""),
            "Restore returned an invalid operation identifier.",
        )
        self.operations.add(operation)
        self.check_restored_database(restored, source_before)
        require(
            self.media_hashes(restored["media_volume"]) == expected_media,
            "Restored media names or hashes differ.",
        )
        print(
            "PASS: rows, foreign keys, constraints, sequences and media match.",
            flush=True,
        )

        self.check_helper_failure_cleanup(timeout=False)
        print("PASS: helper output overflow leaves no container or volume.", flush=True)
        self.check_helper_failure_cleanup(timeout=True)
        print("PASS: helper timeout leaves no container or volume.", flush=True)

        self.check_restore_failure_cleanup()
        print(
            "PASS: failed pg_restore cleans only its new staging resources.", flush=True
        )
        require(
            self.database_snapshot(
                self.database_container, SOURCE_DATABASE, SOURCE_USER
            )
            == source_before,
            "Recovery changed the original database.",
        )
        require(
            self.media_hashes(self.media_volume) == expected_media,
            "Recovery changed the original media volume.",
        )
        print(
            "PASS: original database and media sentinels remain unchanged.", flush=True
        )

    def cleanup(self):
        for operation in self.operations:
            label = f"label={OPERATION_LABEL}={operation}"
            containers = self.docker_command(
                "ps", "--all", "--quiet", "--filter", label
            )
            for container in containers.stdout.decode().splitlines():
                self.docker_command("rm", "--force", "--volumes", container)
            volumes = self.docker_command("volume", "ls", "--quiet", "--filter", label)
            for volume in volumes.stdout.decode().splitlines():
                self.docker_command("volume", "rm", volume)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--docker-host", required=True, help="Explicit local Unix socket"
    )
    arguments = parser.parse_args()
    with tempfile.TemporaryDirectory(
        prefix="story-filler-recovery-integration-"
    ) as root:
        integration = Integration(arguments.docker_host, root)
        original_resources = integration.resource_ids()
        try:
            integration.run()
        finally:
            integration.cleanup()
            require(
                integration.resource_ids() == original_resources,
                "Integration cleanup left containers or "
                "named/anonymous volumes behind.",
            )
    print("All recovery integration checks passed; temporary resources removed.")


if __name__ == "__main__":
    main()
