"""Offline checks of image-verification ownership and failure boundaries."""

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import backend_integration as integration
import check_backend_runtime as runtime


def result(code=0, stdout=b""):
    return subprocess.CompletedProcess([], code, stdout, b"")


def verifier():
    value = integration.Verification.__new__(integration.Verification)
    value.operation = "a" * 32
    value.network = "fixture-network"
    value.network_created = False
    value.network_id = None
    value.containers = {}
    value.command = Mock()
    return value


class RuntimeContracts(unittest.TestCase):
    def test_remote_socket_rejected_before_command(self):
        with patch.object(integration.Verification, "command") as command:
            with self.assertRaisesRegex(RuntimeError, "local Docker"):
                integration.Verification("tcp://remote:2375", "fixture")
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
        check.remove_owned("container", "absent", None)
        self.assertEqual(check.command.call_count, 2)
        check.command.side_effect = [result(1), RuntimeError("daemon unavailable")]
        with self.assertRaisesRegex(RuntimeError, "daemon unavailable"):
            check.remove_owned("container", "absent", None)

    def test_real_child_timeout_is_bounded_and_sanitized(self):
        check = integration.Verification.__new__(integration.Verification)
        check.prefix = [sys.executable, "-c", "import time; time.sleep(10)"]
        check.environment = {}
        with self.assertRaisesRegex(
            RuntimeError, "^synthetic timeout did not complete$"
        ):
            check.command([], "synthetic timeout", timeout=0.05)

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
