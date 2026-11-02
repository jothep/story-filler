"""Offline checks of image-verification ownership and failure boundaries."""

import hashlib
import json
import signal
import subprocess
import sys
import unittest
from contextlib import ExitStack
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import backend_integration as integration
import check_backend_runtime as runtime


def result(code=0, stdout=b"", stderr=b""):
    return subprocess.CompletedProcess([], code, stdout, stderr)


def verifier():
    value = integration.Verification.__new__(integration.Verification)
    value.operation = "a" * 32
    value.network = "fixture-network"
    value.network_created = False
    value.network_id = None
    value.containers = {}
    value.secret_values = []
    value.command = Mock()
    return value


class RuntimeContracts(unittest.TestCase):
    def test_remote_socket_rejected_before_command(self):
        with patch.object(integration.Verification, "command") as command:
            with self.assertRaisesRegex(RuntimeError, "local Docker"):
                integration.Verification("tcp://remote:2375", "fixture")
            command.assert_not_called()

    def test_image_options_and_shell_metacharacters_rejected_before_docker(self):
        for image in (
            "--privileged",
            "image;touch file",
            "$(command)",
            "image name",
            "image`command`",
            "image\nother",
        ):
            with (
                self.subTest(image=image),
                patch.object(integration.Verification, "command") as command,
            ):
                with self.assertRaisesRegex(RuntimeError, "image name or digest"):
                    integration.Verification("unix:///var/run/docker.sock", image)
                command.assert_not_called()

    def test_create_timeout_still_tracks_resource_for_cleanup(self):
        check = verifier()
        check.command.side_effect = [result(1), RuntimeError("timed out")]
        with self.assertRaisesRegex(RuntimeError, "timed out"):
            check.create("slow", "fixture", [])
        self.assertEqual(check.containers, {"fixture-network-slow": None})

    def test_resource_ownership_mismatch_prevents_removal(self):
        for identifier, labels in [
            ("1" * 64, {integration.LABEL: "other-owner"}),
            ("2" * 64, {integration.LABEL: "a" * 32}),
            ("1" * 64, None),
        ]:
            check = verifier()
            metadata = {"id": identifier, "labels": labels}
            check.command.return_value = result(stdout=json.dumps(metadata).encode())
            with self.assertRaisesRegex(RuntimeError, "ownership changed"):
                check.remove_owned("container", "example", "1" * 64)
            self.assertEqual(check.command.call_count, 1)

    def test_owned_container_removal_uses_id_and_anonymous_volume_cleanup(self):
        check = verifier()
        metadata = {"id": "1" * 64, "labels": {integration.LABEL: check.operation}}
        check.command.side_effect = [
            result(stdout=json.dumps(metadata).encode()),
            result(),
        ]
        check.remove_owned("container", "example", "1" * 64)
        self.assertEqual(
            check.command.call_args.args[0], ["rm", "--force", "--volumes", "1" * 64]
        )

    def test_cleanup_continues_after_failure_but_reports_it(self):
        check = verifier()
        check.containers = {"first": "1", "second": "2"}
        check.network_created = True
        check.network_id = "3"
        check.remove_owned = Mock(
            side_effect=[RuntimeError("removal timed out"), None, None]
        )
        with self.assertRaisesRegex(RuntimeError, "removal timed out"):
            check.cleanup()
        self.assertEqual(check.remove_owned.call_count, 3)
        self.assertEqual(
            check.remove_owned.call_args.args, ("network", "fixture-network", "3")
        )

    def test_absent_failed_create_requires_successful_daemon_inventory(self):
        check = verifier()
        check.command.side_effect = [result(1), result(stdout=b"unrelated\n")]
        check.remove_owned("container", "absent", "1" * 64)
        self.assertEqual(check.command.call_count, 2)
        check.command.side_effect = [result(1), RuntimeError("daemon unavailable")]
        with self.assertRaisesRegex(RuntimeError, "daemon unavailable"):
            check.remove_owned("container", "absent", "1" * 64)

    def test_late_container_and_network_are_found_and_removed(self):
        for kind in ("container", "network"):
            with self.subTest(kind=kind), patch.object(integration.time, "sleep"):
                check = verifier()
                metadata = {
                    "id": "1" * 64,
                    "labels": {integration.LABEL: check.operation},
                }
                check.command.side_effect = [
                    result(1),
                    result(stdout=b""),
                    result(stdout=json.dumps(metadata).encode()),
                    result(),
                ]
                check.remove_owned(kind, "late", None)
                inventory = check.command.call_args_list[1].args[0]
                self.assertIn(f"label={integration.LABEL}={check.operation}", inventory)
                self.assertEqual(check.command.call_args.args[0][-1], "1" * 64)

    def test_unresolved_create_never_reports_successful_cleanup(self):
        check = verifier()
        check.containers = {"late": None}
        check.command.side_effect = [
            result(1),
            result(),
        ] * integration.UNCERTAIN_CREATE_ATTEMPTS
        with patch.object(integration.time, "sleep"), patch("builtins.print") as output:
            with self.assertRaisesRegex(
                RuntimeError, "Cleanup is not confirmed"
            ) as error:
                check.cleanup()
        self.assertIn(f"{integration.LABEL}={check.operation}", str(error.exception))
        self.assertEqual(
            check.command.call_count, 2 * integration.UNCERTAIN_CREATE_ATTEMPTS
        )
        output.assert_not_called()

    def test_repeated_signals_do_not_interrupt_cleanup_and_handlers_are_restored(self):
        check = verifier()
        check.containers = {"first": "1", "second": "2"}
        received = []
        signals = (signal.SIGTERM, signal.SIGINT)
        previous = {number: signal.getsignal(number) for number in signals}

        def handler(number, _frame):
            received.append(number)

        def remove(*_):
            for number in signals:
                signal.raise_signal(number)
                signal.raise_signal(number)

        try:
            for number in signals:
                signal.signal(number, handler)
            check.remove_owned = Mock(side_effect=remove)
            with patch("builtins.print"):
                check.cleanup()
            self.assertEqual(check.remove_owned.call_count, 2)
            self.assertEqual(received, [])
            for number in signals:
                self.assertIs(signal.getsignal(number), handler)
                signal.raise_signal(number)
            self.assertEqual(received, list(signals))
        finally:
            for number, callback in previous.items():
                signal.signal(number, callback)

    def test_cleanup_failure_restores_signal_handlers(self):
        previous = {
            number: signal.getsignal(number)
            for number in (signal.SIGTERM, signal.SIGINT)
        }
        check = verifier()
        check.containers = {"first": "1"}
        check.remove_owned = Mock(side_effect=RuntimeError("cleanup failed"))
        with self.assertRaisesRegex(RuntimeError, "cleanup failed"):
            check.cleanup()
        for number, handler in previous.items():
            self.assertIs(signal.getsignal(number), handler)

    def test_application_readiness_requires_all_workers_before_http(self):
        with (
            patch.object(Path, "read_bytes", return_value=b"gunicorn"),
            patch("urllib.request.urlopen") as http,
        ):
            with patch.object(Path, "read_text", return_value="10"):
                with self.assertRaises(AssertionError):
                    exec(integration.APPLICATION_READY, {})
                http.assert_not_called()
            with patch.object(Path, "read_text", return_value="10 11 12"):
                exec(integration.APPLICATION_READY, {})
                http.assert_called_once()

    def test_readiness_deadline_keeps_the_last_safe_diagnostic(self):
        check = verifier()
        check.secret_values = ["synthetic-password"]
        check.command.side_effect = [
            result(stdout=b"true"),
            result(1, stderr=b"database rejected synthetic-password"),
        ]
        with (
            patch.object(integration.time, "monotonic", side_effect=[0, 1, 61]),
            patch.object(integration.time, "sleep"),
        ):
            with self.assertRaisesRegex(RuntimeError, "exit 1") as error:
                check.wait_ready("container", ["python", "-c", "pass"], "ready")
        self.assertIn("database rejected [redacted]", str(error.exception))
        self.assertNotIn("synthetic-password", str(error.exception))

    def test_diagnostics_redact_before_truncating_and_do_not_print_stdout(self):
        check = verifier()
        check.secret_values = ["secret" * 250, "synthetic-signing-key"]
        stderr = (
            "prefix " + check.secret_values[0] + " " + check.secret_values[1]
        ).encode()
        message = check.diagnostics(result(2, stdout=b"private stdout", stderr=stderr))
        self.assertIn("exit 2", message)
        self.assertEqual(message.count("[redacted]"), 2)
        self.assertNotIn("secret", message)
        self.assertNotIn("signing", message)
        self.assertNotIn("private stdout", message)
        long_message = check.diagnostics(result(1, stderr=b"x" * 3000))
        self.assertLessEqual(len(long_message), 1032)

    def test_real_child_timeout_is_bounded_and_sanitized(self):
        check = integration.Verification.__new__(integration.Verification)
        check.prefix = [sys.executable, "-c", "import time; time.sleep(10)"]
        check.environment = {}
        with self.assertRaisesRegex(
            RuntimeError, "^synthetic timeout did not complete$"
        ):
            check.command([], "synthetic timeout", timeout=0.05)

    def test_sqlite_absence_accepts_removed_modules_library_and_metadata(self):
        with (
            patch.object(runtime.importlib.util, "find_spec", return_value=None),
            patch.object(Path, "exists", return_value=False),
            patch.object(Path, "glob", return_value=[]),
            patch.object(Path, "read_text", return_value="P:libpq\nP:python3\n"),
            patch("builtins.print"),
        ):
            runtime.check_sqlite_absent()

    def test_sqlite_components_must_be_removed_not_just_hidden(self):
        cases = (
            ("module", {"spec": object()}),
            ("stdlib", {"exists": True}),
            ("native extension", {"glob": "_sqlite3*.so"}),
            ("shared library", {"glob": "libsqlite3.so*"}),
            ("metadata", {"metadata": "P:sqlite-libs\nV:3.53.4\n"}),
        )
        for name, changes in cases:
            with self.subTest(component=name), ExitStack() as stack:
                stack.enter_context(
                    patch.object(
                        runtime.importlib.util,
                        "find_spec",
                        return_value=changes.get("spec"),
                    )
                )
                stack.enter_context(
                    patch.object(
                        Path, "exists", return_value=changes.get("exists", False)
                    )
                )
                stack.enter_context(
                    patch.object(
                        Path,
                        "glob",
                        autospec=True,
                        side_effect=lambda _path, pattern: (
                            [Path("sqlite-component")]
                            if pattern == changes.get("glob")
                            else []
                        ),
                    )
                )
                stack.enter_context(
                    patch.object(
                        Path,
                        "read_text",
                        return_value=changes.get("metadata", "P:libpq\n"),
                    )
                )
                with self.assertRaisesRegex(RuntimeError, "SQLite"):
                    runtime.check_sqlite_absent()

    def test_database_checks_reject_sqlite_before_starting_django_tests(self):
        connection = SimpleNamespace(vendor="sqlite", ensure_connection=Mock())
        with (
            patch.dict(
                sys.modules,
                {
                    "django": SimpleNamespace(setup=Mock()),
                    "django.db": SimpleNamespace(connection=connection),
                },
            ),
            patch.object(subprocess, "run") as command,
            patch.dict(integration.os.environ),
        ):
            with self.assertRaisesRegex(AssertionError, "require PostgreSQL"):
                exec(integration.DJANGO_CHECKS, {})
            command.assert_not_called()
            connection.ensure_connection.assert_not_called()

    def test_database_checks_detect_an_unremoved_django_test_database(self):
        connection = MagicMock()
        connection.vendor = "postgresql"
        connection.settings_dict = {"NAME": "runtime_test", "TEST": {"NAME": None}}
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (1,)
        with (
            patch.dict(
                sys.modules,
                {
                    "django": SimpleNamespace(setup=Mock()),
                    "django.db": SimpleNamespace(connection=connection),
                },
            ),
            patch.object(
                subprocess, "run", return_value=result(stderr=b"Ran 31 tests")
            ) as command,
            patch.dict(integration.os.environ),
            patch("builtins.print"),
        ):
            with self.assertRaisesRegex(AssertionError, "was not removed"):
                exec(integration.DJANGO_CHECKS, {})
        self.assertEqual(command.call_count, 3)
        connection.ensure_connection.assert_called_once()
        cursor.execute.assert_called_once_with(
            "SELECT 1 FROM pg_database WHERE datname = %s", ["test_runtime_test"]
        )

    def test_wrong_runtime_lock_rejected(self):
        with patch.object(Path, "read_bytes", return_value=b"reviewed-lock"):
            with self.assertRaisesRegex(RuntimeError, "Image lock differs"):
                runtime.check_packages({}, "0" * 64)

    def test_missing_or_unexpected_package_is_rejected(self):
        with (
            patch.object(Path, "read_bytes", return_value=b"reviewed-lock"),
            patch("importlib.metadata.distributions", return_value=[]),
        ):
            with self.assertRaisesRegex(RuntimeError, "versions differ"):
                runtime.check_packages(
                    {"django": "5.2.18"}, hashlib.sha256(b"reviewed-lock").hexdigest()
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
