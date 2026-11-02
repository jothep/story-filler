"""Verify that retired restore entry points cannot reach operational commands."""

from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest

SCRIPTS_DIR = Path(__file__).resolve().parent
RESTORE_SCRIPTS = ("restore-volumes.sh", "restore-volumes-ec2.sh")
OPERATIONAL_COMMANDS = (
    "docker",
    "docker-compose",
    "compose",
    "rm",
    "aws",
    "gcloud",
    "kubectl",
    "terraform",
    "sudo",
    "tar",
    "cp",
    "mv",
    "mkdir",
)
COMMAND_STUB = """#!/bin/sh
printf '%s' "${0##*/}" >> "$RESTORE_SAFETY_COMMAND_LOG"
printf ' <%s>' "$@" >> "$RESTORE_SAFETY_COMMAND_LOG"
printf '\\n' >> "$RESTORE_SAFETY_COMMAND_LOG"
exit 0
"""


class RestoreSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory(prefix="restore-safety-")
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.backup = self.root / "backup with spaces"
        self.backup.mkdir()
        self.command_log = self.root / "commands.log"
        self.bin_dir = self.root / "bin"
        self.bin_dir.mkdir()

        # No real Docker, cloud CLI, or deletion command is on the subprocess PATH.
        for command in OPERATIONAL_COMMANDS:
            executable = self.bin_dir / command
            executable.write_text(COMMAND_STUB)
            executable.chmod(0o755)

        self.environment = {
            "PATH": str(self.bin_dir),
            "RESTORE_SAFETY_COMMAND_LOG": str(self.command_log),
            "LC_ALL": "C",
        }

    def assert_restore_disabled(self, arguments, input_text="", extra_environment=None):
        environment = {**self.environment, **(extra_environment or {})}
        for script_name in RESTORE_SCRIPTS:
            with self.subTest(script=script_name, arguments=arguments):
                self.command_log.write_text("")
                result = subprocess.run(
                    ["/bin/bash", str(SCRIPTS_DIR / script_name), *arguments],
                    cwd=self.root,
                    env=environment,
                    input=input_text,
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                commands = self.command_log.read_text()
                self.assertEqual(
                    commands, "", f"Operational commands were called:\n{commands}"
                )
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, "")
                self.assertIn("disabled", result.stderr)
                self.assertIn("delete existing data", result.stderr)
                self.assertIn("not available", result.stderr)

    def test_missing_argument(self):
        self.assert_restore_disabled([])

    def test_missing_backup_directory(self):
        self.assert_restore_disabled([str(self.root / "missing")])

    def test_relative_backup_directory(self):
        self.assert_restore_disabled([self.backup.name])

    def test_absolute_backup_directory(self):
        self.assert_restore_disabled([str(self.backup)])

    def test_complete_archives_do_not_enable_restore(self):
        for filename in ("postgres_data.tar.gz", "media_data.tar.gz"):
            with tarfile.open(self.backup / filename, "w:gz"):
                pass
        self.assert_restore_disabled([str(self.backup)], input_text="yes\nyes\n")

    def test_options_and_confirmation_do_not_enable_restore(self):
        for arguments in (["--help"], [str(self.backup), "--force", "--yes"]):
            self.assert_restore_disabled(arguments, input_text="yes\nyes\n")

    def test_environment_variables_do_not_enable_restore(self):
        self.assert_restore_disabled(
            [str(self.backup)],
            input_text="yes\nyes\n",
            extra_environment={
                "ALLOW_UNSAFE_RESTORE": "1",
                "FORCE_RESTORE": "1",
                "SKIP_CONFIRMATION": "1",
            },
        )


if __name__ == "__main__":
    unittest.main()
