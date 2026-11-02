"""Offline validation tests for recovery archives; no Docker or database access."""

import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import recovery_archive as recovery


def tar_bytes(entries=(), *, archive_format=tarfile.PAX_FORMAT):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w", format=archive_format) as archive:
        for name, content, entry_type in entries:
            info = tarfile.TarInfo(name)
            info.type = entry_type
            info.size = len(content)
            if entry_type in {tarfile.SYMTYPE, tarfile.LNKTYPE}:
                info.linkname = "sensitive-link-target"
            archive.addfile(info, io.BytesIO(content))
    return output.getvalue()


class RecoveryArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="recovery-archive-test-")
        self.addCleanup(self.temporary.cleanup)
        self.bundle = Path(self.temporary.name) / "private bundle"
        self.bundle.mkdir()
        (self.bundle / "database.dump").write_bytes(b"PGDMP\x01example-dump")
        (self.bundle / "media.tar").write_bytes(tar_bytes())

    def write_unchecked_manifest(self):
        manifest = {"version": 1, "postgres_major": 16, "files": {}}
        for name in ("database.dump", "media.tar"):
            contents = (self.bundle / name).read_bytes()
            manifest["files"][name] = {
                "size": len(contents),
                "sha256": hashlib.sha256(contents).hexdigest(),
            }
        (self.bundle / "manifest.json").write_text(json.dumps(manifest))
        return manifest

    def assert_media_rejected(self, contents):
        (self.bundle / "media.tar").write_bytes(contents)
        self.write_unchecked_manifest()
        with self.assertRaises(recovery.RecoveryError):
            recovery.validate_bundle(self.bundle)

    def test_empty_media_round_trip_and_private_manifest(self):
        manifest = recovery.write_manifest(self.bundle)
        self.assertEqual(recovery.validate_bundle(str(self.bundle)), manifest)
        self.assertEqual(recovery.media_fingerprints(self.bundle / "media.tar"), {})
        self.assertEqual(set(manifest), {"version", "postgres_major", "files"})
        self.assertEqual((self.bundle / "manifest.json").stat().st_mode & 0o777, 0o600)
        self.assertNotIn(str(self.bundle), json.dumps(manifest))
        self.assertEqual(
            set(entry.name for entry in self.bundle.iterdir()), recovery.BUNDLE_NAMES
        )

    def test_files_spaces_unicode_and_root_directory_are_valid(self):
        entries = [
            ("./", b"", tarfile.DIRTYPE),
            ("./word images/", b"", tarfile.DIRTYPE),
            ("./word images/kāinga photo.png", b"picture", tarfile.REGTYPE),
            ("empty file", b"", tarfile.REGTYPE),
            ("empty directory/", b"", tarfile.DIRTYPE),
        ]
        (self.bundle / "media.tar").write_bytes(tar_bytes(entries))
        recovery.write_manifest(self.bundle)
        recovery.validate_bundle(self.bundle)
        result = recovery.media_fingerprints(self.bundle / "media.tar")
        self.assertEqual(result["."], {"type": "directory"})
        self.assertEqual(result["empty directory"], {"type": "directory"})
        self.assertEqual(
            result["word images/kāinga photo.png"],
            {
                "type": "file",
                "size": 7,
                "sha256": hashlib.sha256(b"picture").hexdigest(),
            },
        )
        self.assertEqual(result["empty file"]["size"], 0)

    def test_long_names_in_pax_and_gnu_archives_are_supported(self):
        name = "a" * 120 + "/picture.png"
        for archive_format in (tarfile.PAX_FORMAT, tarfile.GNU_FORMAT):
            with self.subTest(archive_format=archive_format):
                data = tar_bytes(
                    [(name, b"image", tarfile.REGTYPE)], archive_format=archive_format
                )
                (self.bundle / "media.tar").write_bytes(data)
                recovery.write_manifest(self.bundle)
                self.assertIn(
                    name, recovery.media_fingerprints(self.bundle / "media.tar")
                )

    def test_changed_payload_is_rejected_by_checksum(self):
        recovery.write_manifest(self.bundle)
        (self.bundle / "database.dump").write_bytes(b"PGDMP\x01tampered-dump")
        with self.assertRaisesRegex(recovery.RecoveryError, "does not match"):
            recovery.validate_bundle(self.bundle)

    def test_invalid_or_empty_dump_with_matching_hash_is_rejected(self):
        for contents in (b"", b"PGDMP", b"plain SQL contains private-data"):
            with self.subTest(contents=contents):
                (self.bundle / "database.dump").write_bytes(contents)
                self.write_unchecked_manifest()
                with self.assertRaises(recovery.RecoveryError):
                    recovery.validate_bundle(self.bundle)

    def test_manifest_rejects_unknown_schema_and_invalid_types(self):
        changes = [
            lambda m: m.update(extra="private-data"),
            lambda m: m.update(version=2),
            lambda m: m.update(version=True),
            lambda m: m.update(postgres_major=17),
            lambda m: m.update(postgres_major="16"),
            lambda m: m["files"].update(extra={}),
            lambda m: m["files"]["media.tar"].update(extra="private-data"),
            lambda m: m["files"]["media.tar"].update(size=True),
            lambda m: m["files"]["media.tar"].update(size=-1),
            lambda m: m["files"]["media.tar"].update(size=1.0),
            lambda m: m["files"]["media.tar"].update(sha256="not-a-checksum"),
            lambda m: m["files"]["media.tar"].update(sha256=0),
        ]
        for change in changes:
            with self.subTest(change=change):
                manifest = self.write_unchecked_manifest()
                change(manifest)
                (self.bundle / "manifest.json").write_text(json.dumps(manifest))
                with self.assertRaises(recovery.RecoveryError) as caught:
                    recovery.validate_bundle(self.bundle)
                self.assertNotIn("private-data", str(caught.exception))

    def test_duplicate_json_keys_are_rejected_at_any_depth(self):
        manifest = self.write_unchecked_manifest()
        text = json.dumps(manifest)
        variants = [
            text.replace('"version": 1', '"version": 1, "version": 1'),
            text.replace('"size": ', '"size": 0, "size": ', 1),
        ]
        for text in variants:
            with self.subTest(text=text):
                (self.bundle / "manifest.json").write_text(text)
                with self.assertRaisesRegex(recovery.RecoveryError, "duplicate keys"):
                    recovery.validate_bundle(self.bundle)

    def test_bad_json_and_oversized_manifest_have_safe_errors(self):
        for content in (
            b'{"sensitive-token":',
            b"\xffinvalid",
            b" " * 17_000,
            b"[" * 2_000 + b"]" * 2_000,
        ):
            with self.subTest(length=len(content)):
                (self.bundle / "manifest.json").write_bytes(content)
                with self.assertRaises(recovery.RecoveryError) as caught:
                    recovery.validate_bundle(self.bundle)
                self.assertNotIn("sensitive-token", str(caught.exception))
                self.assertNotIn(str(self.bundle), str(caught.exception))

    def test_missing_and_extra_files_are_rejected(self):
        with self.assertRaises(recovery.RecoveryError):
            recovery.validate_bundle(self.bundle)
        recovery.write_manifest(self.bundle)
        (self.bundle / "extra-private-file").write_text("private-data")
        with self.assertRaises(recovery.RecoveryError) as caught:
            recovery.validate_bundle(self.bundle)
        self.assertNotIn("private", str(caught.exception))

    def test_bundle_directory_and_each_entry_cannot_be_symlinks(self):
        recovery.write_manifest(self.bundle)
        linked_bundle = self.bundle.parent / "linked-bundle"
        linked_bundle.symlink_to(self.bundle, target_is_directory=True)
        with self.assertRaises(recovery.RecoveryError):
            recovery.validate_bundle(linked_bundle)
        for name in recovery.BUNDLE_NAMES:
            with self.subTest(name=name):
                target = self.bundle / name
                saved = self.bundle.parent / name
                target.rename(saved)
                target.symlink_to(saved)
                with self.assertRaises(recovery.RecoveryError):
                    recovery.validate_bundle(self.bundle)
                target.unlink()
                saved.rename(target)

    def test_directory_cannot_replace_a_bundle_file(self):
        (self.bundle / "database.dump").unlink()
        (self.bundle / "database.dump").mkdir()
        with self.assertRaises(recovery.RecoveryError):
            recovery.write_manifest(self.bundle)

    def test_unsafe_paths_are_rejected_without_including_the_name(self):
        names = [
            "/private-secret",
            "../private-secret",
            "a/../private-secret",
            "a\\private-secret",
            "C:/private-secret",
            "C:private-secret",
            "./C:/private-secret",
            "./C:private-secret",
            "a\nprivate-secret",
            "a\x7fprivate-secret",
            "a\u202eprivate-secret",
            ".",
            "file/",
        ]
        for name in names:
            with self.subTest(name=name):
                contents = tar_bytes([(name, b"value", tarfile.REGTYPE)])
                (self.bundle / "media.tar").write_bytes(contents)
                self.write_unchecked_manifest()
                with self.assertRaises(recovery.RecoveryError) as caught:
                    recovery.validate_bundle(self.bundle)
                self.assertNotIn("private-secret", str(caught.exception))

    def test_duplicate_normalized_paths_and_file_directory_conflicts(self):
        entry_sets = [
            [("file", b"a", tarfile.REGTYPE), ("./file", b"b", tarfile.REGTYPE)],
            [("folder/", b"", tarfile.DIRTYPE), ("folder", b"a", tarfile.REGTYPE)],
            [("a", b"a", tarfile.REGTYPE), ("a/b", b"b", tarfile.REGTYPE)],
            [("a/b", b"b", tarfile.REGTYPE), ("a", b"a", tarfile.REGTYPE)],
            [("a//b", b"a", tarfile.REGTYPE), ("a/./b", b"b", tarfile.REGTYPE)],
        ]
        for entries in entry_sets:
            with self.subTest(entries=entries):
                self.assert_media_rejected(tar_bytes(entries))

    def test_links_devices_fifo_and_sparse_entries_are_rejected(self):
        types = [
            tarfile.SYMTYPE,
            tarfile.LNKTYPE,
            tarfile.CHRTYPE,
            tarfile.BLKTYPE,
            tarfile.FIFOTYPE,
            tarfile.GNUTYPE_SPARSE,
        ]
        for entry_type in types:
            with self.subTest(entry_type=entry_type):
                self.assert_media_rejected(tar_bytes([("entry", b"", entry_type)]))

    def test_pax_sparse_metadata_is_rejected_before_sparse_map_parsing(self):
        output = io.BytesIO()
        with tarfile.open(
            fileobj=output, mode="w", format=tarfile.PAX_FORMAT
        ) as archive:
            info = tarfile.TarInfo("file")
            info.pax_headers = {"GNU.sparse.major": "1", "GNU.sparse.minor": "0"}
            archive.addfile(info, io.BytesIO())
        self.assert_media_rejected(output.getvalue())

    def test_deep_extended_header_chain_fails_with_a_safe_error(self):
        metadata = b"11 mtime=0\n"
        header = tarfile.TarInfo("metadata")
        header.type = tarfile.XHDTYPE
        header.size = len(metadata)
        record = header.tobuf() + metadata + bytes(512 - len(metadata))
        contents = record * 1_100 + tar_bytes([("file", b"x", tarfile.REGTYPE)])
        self.assert_media_rejected(contents)

    def test_truncated_data_header_and_end_marker_are_rejected(self):
        complete = tar_bytes([("file", b"x" * 600, tarfile.REGTYPE)])
        for cut in (0, 100, 512 + 50, 512 + 1024, 512 + 1024 + 512):
            with self.subTest(cut=cut):
                self.assert_media_rejected(complete[:cut])

    def test_nonzero_trailing_data_and_bad_header_checksum_are_rejected(self):
        complete = tar_bytes([("file", b"x", tarfile.REGTYPE)])
        self.assert_media_rejected(complete + bytes(511) + b"x")
        bad_header = bytearray(complete)
        bad_header[0] ^= 1
        self.assert_media_rejected(bytes(bad_header))

    def test_compressed_media_is_rejected(self):
        output = io.BytesIO()
        with tarfile.open(fileobj=output, mode="w:gz"):
            pass
        self.assert_media_rejected(output.getvalue())

    def test_limits_bound_total_archive_and_expanded_file_sizes(self):
        recovery.write_manifest(self.bundle)
        with patch.object(recovery, "MAX_BUNDLE_BYTES", 1024):
            with self.assertRaisesRegex(recovery.RecoveryError, "size limit"):
                recovery.validate_bundle(self.bundle)
        contents = tar_bytes(
            [
                ("one", b"a" * 6, tarfile.REGTYPE),
                ("two", b"b" * 6, tarfile.REGTYPE),
            ]
        )
        (self.bundle / "media.tar").write_bytes(contents)
        self.write_unchecked_manifest()
        with patch.object(recovery, "MAX_MEDIA_BYTES", 10):
            with self.assertRaisesRegex(recovery.RecoveryError, "size limit"):
                recovery.validate_bundle(self.bundle)

    def test_member_and_path_limits(self):
        (self.bundle / "media.tar").write_bytes(
            tar_bytes(
                [
                    ("one", b"a", tarfile.REGTYPE),
                    ("two", b"b", tarfile.REGTYPE),
                ]
            )
        )
        self.write_unchecked_manifest()
        with patch.object(recovery, "MAX_MEMBERS", 1):
            with self.assertRaisesRegex(recovery.RecoveryError, "too many"):
                recovery.validate_bundle(self.bundle)
        self.assert_media_rejected(tar_bytes([("x" * 513, b"a", tarfile.REGTYPE)]))

    def test_oversized_extended_metadata_is_rejected(self):
        header = tarfile.TarInfo("metadata")
        header.type = tarfile.XHDTYPE
        header.size = recovery.MAX_TAR_METADATA_BYTES + 1
        self.assert_media_rejected(header.tobuf() + bytes(header.size + 2048))

    def test_write_manifest_rejects_other_postgres_versions(self):
        for version in (15, 17, True, "16"):
            with self.subTest(version=version):
                with self.assertRaises(recovery.RecoveryError):
                    recovery.write_manifest(self.bundle, version)

    def test_manifest_write_failure_is_safe_and_cleans_its_temporary_file(self):
        with patch.object(recovery.os, "replace", side_effect=OSError("private-token")):
            with self.assertRaises(recovery.RecoveryError) as caught:
                recovery.write_manifest(self.bundle)
        self.assertNotIn("private-token", str(caught.exception))
        self.assertEqual(
            set(entry.name for entry in self.bundle.iterdir()), recovery.PAYLOAD_NAMES
        )


if __name__ == "__main__":
    unittest.main()
