"""Exercise source guards, new-resource ownership and failure cleanup offline."""

from argparse import Namespace
from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import stat
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import local_recovery as recovery


class FakeDocker:
    """Model Docker resource identities without invoking Docker or a database."""

    def __init__(self, media):
        self.calls = []
        self.media = media
        self.fail_stage = None
        self.containers = {
            "source-db": {
                "labels": {
                    recovery.PROJECT_LABEL: "sample",
                    recovery.SERVICE_LABEL: "db",
                },
                "running": True,
                "mounts": [],
            },
            "source-backend": {
                "labels": {
                    recovery.PROJECT_LABEL: "sample",
                    recovery.SERVICE_LABEL: "backend",
                },
                "running": False,
                "mounts": [
                    {
                        "Type": "volume",
                        "Destination": "/app/media",
                        "Name": "source-media",
                        "RW": True,
                    }
                ],
            },
        }
        self.volumes = {"source-media": {recovery.PROJECT_LABEL: "sample"}}
        self.server_version = "160015"
        self.dump_version = "pg_dump (PostgreSQL) 16.15"
        self.table_count = "3"

    def require_image(self):
        self.calls.append(("image-check",))

    def inspect(self, kind, name, field):
        self.calls.append(("inspect", kind, name, field))
        try:
            if kind == "volume":
                return self.volumes[name]
            item = self.containers[name]
            return {
                ".Config.Labels": item["labels"],
                ".State.Running": item["running"],
                ".Mounts": item["mounts"],
            }[field]
        except KeyError as error:
            raise recovery.RecoveryError("Resource inspection failed.") from error

    def sql(self, container, database, user, query):
        self.calls.append(("sql", container, query))
        if query == "SHOW server_version_num":
            return self.server_version
        if query == "SELECT 1":
            return "1"
        return self.table_count

    def text(self, arguments, stage):
        return self.command(arguments, stage).decode().strip()

    def command(self, arguments, stage, *, source=None, destination=None, limit=None):
        self.calls.append(tuple(arguments))
        if stage == self.fail_stage:
            raise recovery.RecoveryError("Docker command failed during " + stage + ".")
        result = b""
        if arguments[:3] == ["ps", "--all", "--quiet"]:
            result = b"source-backend"
        elif arguments == ["ps", "--quiet"]:
            result = "\n".join(
                k for k, v in self.containers.items() if v["running"]
            ).encode()
        elif arguments[:3] == ["ps", "--all", "--format"]:
            result = "\n".join(self.containers).encode()
        elif arguments[:2] == ["volume", "ls"]:
            result = "\n".join(self.volumes).encode()
        elif arguments[:2] == ["volume", "create"]:
            label = arguments[arguments.index("--label") + 1]
            key, value = label.split("=", 1)
            self.volumes[arguments[-1]] = {key: value}
        elif arguments[:2] == ["volume", "rm"]:
            del self.volumes[arguments[-1]]
        elif arguments[:2] == ["container", "rm"]:
            del self.containers[arguments[-1]]
        elif arguments[0] == "run":
            if "--name" in arguments:
                name = arguments[arguments.index("--name") + 1]
                key, value = arguments[arguments.index("--label") + 1].split("=", 1)
                self.containers[name] = {
                    "labels": {key: value},
                    "running": "--detach" in arguments,
                    "mounts": [],
                }
                result = name.encode()
            if stage in {"media backup", "restored media verification"}:
                result = self.media
        elif arguments[0] == "exec":
            if stage == "database backup":
                result = b"PGDMP\x01synthetic dump"
            elif stage == "dump version check":
                result = self.dump_version.encode()
            elif stage == "database readiness check":
                result = b"postgres"
        if destination is not None:
            destination.write(result)
            return b""
        return result


class LocalRecoveryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="recovery-unit-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.bundle = self.root / "valid bundle"
        self.bundle.mkdir()
        with tarfile.open(self.bundle / "media.tar", "w") as archive:
            member = tarfile.TarInfo("photos/hello world.txt")
            member.mode = 0o777
            member.uid = 12345
            member.size = 6
            archive.addfile(member, io.BytesIO(b"hello\n"))
        (self.bundle / "database.dump").write_bytes(b"PGDMP\x01synthetic dump")
        recovery.write_manifest(self.bundle)
        self.docker = FakeDocker((self.bundle / "media.tar").read_bytes())
        self.backup_args = Namespace(
            project="sample",
            db_container="source-db",
            database="sample",
            db_user="sample",
            media_volume="source-media",
            output=str(self.root / "backup"),
            writers_stopped=True,
        )
        self.restore_args = Namespace(bundle=str(self.bundle), trusted_backup=True)

    def assert_source_untouched(self):
        self.assertIn("source-db", self.docker.containers)
        self.assertTrue(self.docker.containers["source-db"]["running"])
        self.assertIn("source-backend", self.docker.containers)
        self.assertIn("source-media", self.docker.volumes)
        forbidden = {"stop", "start", "restart", "prune", "compose"}
        self.assertFalse(any(call[0] in forbidden for call in self.docker.calls))
        for call in self.docker.calls:
            if len(call) > 1 and call[1] == "rm":
                self.assertNotIn(
                    call[-1], {"source-db", "source-backend", "source-media"}
                )

    def test_host_rejects_remote_and_ambiguous_endpoints(self):
        for host in (
            "",
            "tcp://localhost:2375",
            "ssh://host",
            "unix://relative",
            "unix:///tmp/docker.sock?x=y",
        ):
            with self.subTest(host=host), self.assertRaises(recovery.RecoveryError):
                recovery.Docker(host)

    def test_command_failure_hides_raw_stderr(self):
        docker = recovery.Docker("unix:///tmp/test-only.sock")
        docker.prefix = [
            sys.executable,
            "-c",
            "import sys; print('private-sql-and-token', file=sys.stderr); sys.exit(1)",
        ]
        with self.assertRaises(recovery.RecoveryError) as caught:
            docker.command([], "test operation")
        self.assertEqual(
            str(caught.exception), "Docker command failed during test operation."
        )

    def test_command_output_is_bounded(self):
        docker = recovery.Docker("unix:///tmp/test-only.sock")
        docker.prefix = [sys.executable, "-c", "print('123456789')"]
        with self.assertRaisesRegex(recovery.RecoveryError, "Output limit"):
            docker.command([], "test operation", limit=4)

    def test_explicit_docker_host_does_not_inherit_context_override(self):
        docker = recovery.Docker("unix:///tmp/test-only.sock")
        docker.prefix = [
            sys.executable,
            "-c",
            "import os; print(os.environ.get('DOCKER_CONTEXT', 'absent'))",
        ]
        with patch.dict(os.environ, {"DOCKER_CONTEXT": "some-remote-context"}):
            self.assertEqual(docker.text([], "test operation"), "absent")

    def test_backup_requires_explicit_writer_confirmation(self):
        self.backup_args.writers_stopped = False
        with self.assertRaises(recovery.RecoveryError):
            recovery.backup(self.docker, self.backup_args)
        self.assertEqual(self.docker.calls, [])
        self.assertFalse(Path(self.backup_args.output).exists())

    def test_backup_rejects_identifiers_before_docker(self):
        self.backup_args.database = "sample; unsafe"
        with self.assertRaises(recovery.RecoveryError):
            recovery.backup(self.docker, self.backup_args)
        self.assertEqual(self.docker.calls, [])

    def test_wrong_project_or_running_backend_is_rejected(self):
        cases = (
            lambda: self.docker.containers["source-db"]["labels"].update(
                {recovery.PROJECT_LABEL: "other"}
            ),
            lambda: self.docker.containers["source-backend"].update(running=True),
        )
        for change in cases:
            with self.subTest(change=change):
                self.docker = FakeDocker((self.bundle / "media.tar").read_bytes())
                change()
                with self.assertRaises(recovery.RecoveryError):
                    recovery.backup(self.docker, self.backup_args)
                self.assertFalse(Path(self.backup_args.output).exists())

    def test_other_container_with_writable_media_blocks_backup(self):
        self.docker.containers["external-writer"] = {
            "labels": {},
            "running": True,
            "mounts": [{"Name": "source-media", "RW": True}],
        }
        with self.assertRaises(recovery.RecoveryError):
            recovery.backup(self.docker, self.backup_args)
        self.assertFalse(Path(self.backup_args.output).exists())

    def test_wrong_or_missing_backend_media_mount_blocks_backup(self):
        for mounts in (
            [],
            [{"Type": "bind", "Destination": "/app/media", "Name": "source-media"}],
            [{"Type": "volume", "Destination": "/app/media", "Name": "wrong-volume"}],
        ):
            with self.subTest(mounts=mounts):
                self.docker.containers["source-backend"]["mounts"] = mounts
                with self.assertRaises(recovery.RecoveryError):
                    recovery.backup(self.docker, self.backup_args)
                self.assertFalse(Path(self.backup_args.output).exists())

    def test_version_mismatch_blocks_backup(self):
        self.docker.server_version = "150010"
        with self.assertRaises(recovery.RecoveryError):
            recovery.backup(self.docker, self.backup_args)
        self.assertFalse(Path(self.backup_args.output).exists())

    def test_backup_is_logical_read_only_and_private(self):
        result = recovery.backup(self.docker, self.backup_args)
        output = Path(result["backup_directory"])
        recovery.validate_bundle(output)
        self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o700)
        for filename in recovery.BUNDLE_FILES:
            self.assertEqual(stat.S_IMODE((output / filename).stat().st_mode), 0o600)
        dump_call = next(
            call
            for call in self.docker.calls
            if "pg_dump" in call and "--format=custom" in call
        )
        self.assertIn("--host=/var/run/postgresql", dump_call)
        media_call = next(
            call for call in self.docker.calls if "--entrypoint=tar" in call
        )
        self.assertIn("type=volume,src=source-media,dst=/source,readonly", media_call)
        self.assertIn("--pull=never", media_call)
        self.assertIn("--network=none", media_call)
        self.assert_source_untouched()

    def test_failed_backup_keeps_incomplete_files_without_manifest(self):
        self.docker.fail_stage = "media backup"
        with self.assertRaises(recovery.RecoveryError):
            recovery.backup(self.docker, self.backup_args)
        self.assertTrue((Path(self.backup_args.output) / "database.dump").exists())
        self.assertFalse((Path(self.backup_args.output) / "manifest.json").exists())
        self.assert_source_untouched()

    def test_existing_backup_is_never_overwritten(self):
        self.backup_args.output = str(self.bundle)
        before = (self.bundle / "database.dump").read_bytes()
        with self.assertRaises(FileExistsError):
            recovery.backup(self.docker, self.backup_args)
        self.assertEqual((self.bundle / "database.dump").read_bytes(), before)
        self.assertFalse(any(call[0] == "run" for call in self.docker.calls))

    def test_restore_requires_trust_before_any_docker_call(self):
        self.restore_args.trusted_backup = False
        with self.assertRaises(recovery.RecoveryError):
            recovery.restore(self.docker, self.restore_args)
        self.assertEqual(self.docker.calls, [])

    def test_invalid_bundle_is_rejected_before_docker(self):
        (self.bundle / "database.dump").write_bytes(b"broken")
        with self.assertRaises(recovery.RecoveryError):
            recovery.restore(self.docker, self.restore_args)
        self.assertEqual(self.docker.calls, [])

    def test_snapshot_rejects_symlinks_hardlinks_and_extra_files(self):
        original = self.bundle / "database.dump"
        original.rename(self.root / "dump")
        original.symlink_to(self.root / "dump")
        with tempfile.TemporaryDirectory() as target, self.assertRaises(OSError):
            recovery.snapshot_bundle(self.bundle, target)
        original.unlink()
        os.link(self.root / "dump", original)
        with (
            tempfile.TemporaryDirectory() as target,
            self.assertRaises(recovery.RecoveryError),
        ):
            recovery.snapshot_bundle(self.bundle, target)
        original.unlink()
        original.write_bytes(b"PGDMP\x01synthetic dump")
        (self.bundle / "unexpected").write_text("extra")
        with (
            tempfile.TemporaryDirectory() as target,
            self.assertRaises(recovery.RecoveryError),
        ):
            recovery.snapshot_bundle(self.bundle, target)

    def test_dump_readability_is_checked_before_creating_volumes(self):
        self.docker.fail_stage = "dump readability check"
        with self.assertRaises(recovery.RecoveryError):
            recovery.restore(self.docker, self.restore_args)
        self.assertFalse(
            any(call[:2] == ("volume", "create") for call in self.docker.calls)
        )
        self.assert_source_untouched()

    def test_volume_name_collision_does_not_reuse_or_remove_existing_volume(self):
        resources = recovery.RestoreResources(self.docker)
        name = resources.prefix + "-database"
        self.docker.volumes[name] = {"owner": "other"}
        with self.assertRaises(recovery.RecoveryError):
            resources.create_volume("database")
        self.assertEqual(resources.cleanup(volumes=True), [])
        self.assertEqual(self.docker.volumes[name], {"owner": "other"})

    def test_cleanup_refuses_resource_with_changed_ownership(self):
        resources = recovery.RestoreResources(self.docker)
        name = resources.create_volume("database")
        self.docker.volumes[name] = {recovery.OPERATION_LABEL: "another-operation"}
        self.assertEqual(resources.cleanup(volumes=True), [name])
        self.assertIn(name, self.docker.volumes)

    def test_helper_cleanup_failure_is_not_reported_as_success(self):
        self.docker.fail_stage = "recovery cleanup"
        with self.assertRaisesRegex(recovery.RecoveryError, "cleanup needs review"):
            recovery.run_helper(self.docker, [recovery.POSTGRES_IMAGE], "helper test")
        remaining = set(self.docker.containers) - {"source-db", "source-backend"}
        self.assertEqual(len(remaining), 1)
        self.assert_source_untouched()

    def test_interrupted_helper_is_cleaned_with_its_anonymous_volumes(self):
        command = self.docker.command

        def interrupt(arguments, stage, **kwargs):
            result = command(arguments, stage, **kwargs)
            if stage == "helper test":
                raise KeyboardInterrupt
            return result

        with patch.object(self.docker, "command", side_effect=interrupt):
            with self.assertRaises(KeyboardInterrupt):
                recovery.run_helper(
                    self.docker, [recovery.POSTGRES_IMAGE], "helper test"
                )
        self.assertEqual(set(self.docker.containers), {"source-db", "source-backend"})
        removed = [
            call for call in self.docker.calls if call[:2] == ("container", "rm")
        ]
        self.assertEqual(len(removed), 1)
        self.assertIn("--volumes", removed[0])
        self.assert_source_untouched()

    def test_failed_database_restore_cleans_only_new_resources(self):
        self.docker.fail_stage = "database restore"
        with self.assertRaises(recovery.RecoveryError):
            recovery.restore(self.docker, self.restore_args)
        self.assertEqual(set(self.docker.volumes), {"source-media"})
        self.assertEqual(set(self.docker.containers), {"source-db", "source-backend"})
        self.assert_source_untouched()

    def test_failed_media_verification_cleans_only_new_resources(self):
        self.docker.fail_stage = "restored media verification"
        with self.assertRaises(recovery.RecoveryError):
            recovery.restore(self.docker, self.restore_args)
        self.assertEqual(set(self.docker.volumes), {"source-media"})
        self.assert_source_untouched()

    def test_success_keeps_isolated_database_and_new_volumes(self):
        result = recovery.restore(self.docker, self.restore_args)
        self.assertEqual(result["status"], "verified")
        self.assertEqual(
            set(self.docker.volumes),
            {"source-media", result["media_volume"], result["database_volume"]},
        )
        self.assertEqual(
            set(self.docker.containers),
            {"source-db", "source-backend", result["database_container"]},
        )
        for call in self.docker.calls:
            if call[0] == "run":
                self.assertIn("--name", call)
                self.assertIn("--label", call)
                self.assertNotIn("--rm", call)
                self.assertIn("--network=none", call)
                self.assertIn("--pull=never", call)
                self.assertFalse(
                    any(
                        argument in {"-p", "--publish", "--privileged"}
                        for argument in call
                    )
                )
        restore_call = next(
            call
            for call in self.docker.calls
            if call[0] == "exec" and "pg_restore" in call
        )
        self.assertIn("--single-transaction", restore_call)
        self.assertNotIn("--clean", restore_call)
        self.assert_source_untouched()

    def test_media_normalization_drops_ownership_and_dangerous_modes(self):
        normalized = self.root / "normalized.tar"
        recovery.canonical_media_tar(self.bundle / "media.tar", normalized)
        with tarfile.open(normalized) as archive:
            member = archive.getmembers()[0]
            self.assertEqual(member.mode, 0o644)
            self.assertEqual(member.uid, 0)
            self.assertEqual(member.gid, 0)
        self.assertEqual(
            recovery.comparable_media(self.bundle / "media.tar"),
            recovery.comparable_media(normalized),
        )

    def test_verify_cli_needs_no_docker_and_returns_only_status(self):
        output = io.StringIO()
        with patch.object(recovery, "Docker") as docker, redirect_stdout(output):
            self.assertEqual(recovery.main(["verify", "--bundle", str(self.bundle)]), 0)
        docker.assert_not_called()
        self.assertEqual(json.loads(output.getvalue()), {"status": "valid"})

    def test_cli_does_not_disclose_filesystem_exception_details(self):
        output = io.StringIO()
        with (
            patch.object(
                recovery,
                "validate_bundle",
                side_effect=OSError("private-token-and-file"),
            ),
            redirect_stderr(output),
        ):
            self.assertEqual(recovery.main(["verify", "--bundle", str(self.bundle)]), 1)
        self.assertNotIn("private-token", output.getvalue())


if __name__ == "__main__":
    unittest.main()
