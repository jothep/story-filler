"""Validate portable recovery bundles without extracting their contents.

Restore callers must copy an untrusted bundle into a private directory first,
then validate and use that same snapshot. Validation alone cannot prevent an
external process from changing files between a check and a later restore.
"""

import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import re
import stat
import tarfile
import tempfile
import unicodedata

MAX_BUNDLE_BYTES = 2 * 1024**3
MAX_MEDIA_BYTES = 2 * 1024**3
MAX_MEMBERS = 100_000
MAX_PATH_LENGTH = 512
MAX_MANIFEST_BYTES = 16 * 1024
MAX_TAR_METADATA_BYTES = 64 * 1024
CHUNK_BYTES = 1024 * 1024
BLOCK_BYTES = 512
PAYLOAD_NAMES = frozenset({"database.dump", "media.tar"})
BUNDLE_NAMES = PAYLOAD_NAMES | {"manifest.json"}
REGULAR_TYPES = {tarfile.REGTYPE, tarfile.AREGTYPE}
METADATA_TYPES = {tarfile.XHDTYPE, tarfile.XGLTYPE, tarfile.GNUTYPE_LONGNAME}


class RecoveryError(Exception):
    """A safe, user-facing explanation of an invalid recovery bundle."""


def _bundle_directory(directory, *, require_manifest):
    path = Path(directory)
    if path.is_symlink() or not path.is_dir():
        raise RecoveryError("The recovery bundle must be a regular directory.")
    names = {entry.name for entry in path.iterdir()}
    if require_manifest:
        valid_names = names == BUNDLE_NAMES
    else:
        valid_names = names in (PAYLOAD_NAMES, BUNDLE_NAMES)
    if not valid_names:
        raise RecoveryError("The recovery bundle has missing or unexpected files.")
    for name in names:
        if not stat.S_ISREG((path / name).lstat().st_mode):
            raise RecoveryError("Recovery bundle entries must be regular files.")
    size = sum((path / name).stat().st_size for name in PAYLOAD_NAMES)
    if size > MAX_BUNDLE_BYTES:
        raise RecoveryError("The recovery bundle exceeds the size limit.")
    return path


def _unique_json_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise RecoveryError("The recovery manifest contains duplicate keys.")
        result[key] = value
    return result


def _read_manifest(path):
    if path.stat().st_size > MAX_MANIFEST_BYTES:
        raise RecoveryError("The recovery manifest exceeds the size limit.")
    with path.open("rb") as source:
        raw = source.read(MAX_MANIFEST_BYTES + 1)
    if len(raw) > MAX_MANIFEST_BYTES:
        raise RecoveryError("The recovery manifest exceeds the size limit.")
    try:
        manifest = json.loads(raw, object_pairs_hook=_unique_json_keys)
    except (ValueError, UnicodeError, RecursionError):
        raise RecoveryError("The recovery manifest is not valid JSON.") from None
    if type(manifest) is not dict or set(manifest) != {
        "version",
        "postgres_major",
        "files",
    }:
        raise RecoveryError("The recovery manifest has an unsupported schema.")
    if type(manifest["version"]) is not int or manifest["version"] != 1:
        raise RecoveryError("The recovery manifest version is unsupported.")
    if type(manifest["postgres_major"]) is not int or manifest["postgres_major"] != 16:
        raise RecoveryError("The recovery bundle requires PostgreSQL 16.")
    records = manifest["files"]
    if type(records) is not dict or set(records) != PAYLOAD_NAMES:
        raise RecoveryError("The recovery manifest has unexpected file records.")
    for record in records.values():
        if type(record) is not dict or set(record) != {"size", "sha256"}:
            raise RecoveryError("The recovery manifest has an invalid file record.")
        if (
            type(record["size"]) is not int
            or not 0 <= record["size"] <= MAX_BUNDLE_BYTES
        ):
            raise RecoveryError("The recovery manifest has an invalid file size.")
        if not isinstance(record["sha256"], str) or not re.fullmatch(
            r"[0-9a-f]{64}", record["sha256"]
        ):
            raise RecoveryError("The recovery manifest has an invalid checksum.")
    if sum(record["size"] for record in records.values()) > MAX_BUNDLE_BYTES:
        raise RecoveryError("The recovery bundle exceeds the size limit.")
    return manifest


def _file_record(path):
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as source:
        while chunk := source.read(CHUNK_BYTES):
            size += len(chunk)
            if size > MAX_BUNDLE_BYTES:
                raise RecoveryError("A recovery file exceeds the size limit.")
            digest.update(chunk)
    return {"size": size, "sha256": digest.hexdigest()}


def _check_database_dump(path):
    with path.open("rb") as source:
        header = source.read(6)
    if len(header) < 6 or not header.startswith(b"PGDMP"):
        raise RecoveryError(
            "The database backup must be a nonempty custom-format dump."
        )


def _read_exact(source, size):
    """Consume a bounded region without loading file payloads into memory."""
    while size:
        chunk = source.read(min(size, CHUNK_BYTES))
        if not chunk:
            raise RecoveryError("The media archive is truncated.")
        size -= len(chunk)


def _check_pax_headers(data):
    """Reject sparse extensions before tarfile can interpret their data maps."""
    offset = 0
    while offset < len(data):
        separator = data.find(b" ", offset)
        if separator < 0 or separator - offset > 10:
            raise RecoveryError("The media archive has invalid metadata.")
        length_text = data[offset:separator]
        if not length_text.isdigit():
            raise RecoveryError("The media archive has invalid metadata.")
        end = offset + int(length_text)
        if end <= separator + 2 or end > len(data) or data[end - 1 : end] != b"\n":
            raise RecoveryError("The media archive has invalid metadata.")
        field = data[separator + 1 : end - 1]
        if b"=" not in field or field.split(b"=", 1)[0].startswith(b"GNU.sparse"):
            raise RecoveryError("The media archive contains unsupported metadata.")
        offset = end


def _check_tar_blocks(path):
    """Check physical records before tarfile reads extended-header metadata.

    tarfile accepts a missing end marker and can allocate a complete extended
    header. This pass requires the end marker and caps metadata before parsing.
    """
    count = 0
    with path.open("rb") as source:
        while True:
            block = source.read(BLOCK_BYTES)
            if len(block) != BLOCK_BYTES:
                raise RecoveryError("The media archive is truncated.")
            if block == bytes(BLOCK_BYTES):
                if source.read(BLOCK_BYTES) != bytes(BLOCK_BYTES):
                    raise RecoveryError("The media archive has an invalid end marker.")
                while padding := source.read(CHUNK_BYTES):
                    if len(padding) % BLOCK_BYTES or any(padding):
                        raise RecoveryError(
                            "The media archive has invalid trailing data."
                        )
                return
            count += 1
            if count > MAX_MEMBERS:
                raise RecoveryError("The media archive has too many members.")
            header = tarfile.TarInfo.frombuf(block, "utf-8", "surrogateescape")
            if header.type not in REGULAR_TYPES | METADATA_TYPES | {tarfile.DIRTYPE}:
                raise RecoveryError("The media archive contains an unsupported entry.")
            if header.size < 0 or header.size > MAX_MEDIA_BYTES:
                raise RecoveryError("The media archive exceeds the size limit.")
            if header.type == tarfile.DIRTYPE and header.size:
                raise RecoveryError("A media directory has an invalid payload.")
            if header.type in METADATA_TYPES and header.size > MAX_TAR_METADATA_BYTES:
                raise RecoveryError("The media archive has oversized metadata.")
            padded_size = (header.size + BLOCK_BYTES - 1) // BLOCK_BYTES * BLOCK_BYTES
            if header.type in {tarfile.XHDTYPE, tarfile.XGLTYPE}:
                metadata = source.read(header.size)
                if len(metadata) != header.size:
                    raise RecoveryError("The media archive is truncated.")
                _check_pax_headers(metadata)
                _read_exact(source, padded_size - header.size)
            else:
                _read_exact(source, padded_size)


def _member_path(member):
    name = member.name
    if (
        not name
        or len(name) > MAX_PATH_LENGTH
        or name.startswith("/")
        or "\\" in name
        or PureWindowsPath(name).drive
        or any(unicodedata.category(char) in {"Cc", "Cf", "Cs"} for char in name)
    ):
        raise RecoveryError("The media archive contains an unsafe path.")
    parts = name.split("/")
    if ".." in parts:
        raise RecoveryError("The media archive contains an unsafe path.")
    normalized = "/".join(part for part in parts if part not in {"", "."}) or "."
    if PureWindowsPath(normalized).drive:
        raise RecoveryError("The media archive contains an unsafe path.")
    if member.type in REGULAR_TYPES and (normalized == "." or name.endswith("/")):
        raise RecoveryError("A media file has an invalid path.")
    return normalized


def _media_fingerprints(path):
    if not stat.S_ISREG(path.lstat().st_mode):
        raise RecoveryError("The media archive must be a regular file.")
    if path.stat().st_size > MAX_BUNDLE_BYTES:
        raise RecoveryError("The media archive exceeds the size limit.")
    _check_tar_blocks(path)
    fingerprints = {}
    total_size = 0
    with tarfile.open(path, mode="r|", stream=True) as archive:
        for member in archive:
            if len(fingerprints) >= MAX_MEMBERS:
                raise RecoveryError("The media archive has too many members.")
            if (
                member.type not in REGULAR_TYPES | {tarfile.DIRTYPE}
                or member.sparse is not None
                or any(key.startswith("GNU.sparse") for key in member.pax_headers)
            ):
                raise RecoveryError("The media archive contains an unsupported entry.")
            name = _member_path(member)
            if name in fingerprints:
                raise RecoveryError("The media archive contains duplicate paths.")
            if member.isdir():
                if member.size:
                    raise RecoveryError("A media directory has an invalid payload.")
                fingerprints[name] = {"type": "directory"}
                continue
            if member.size < 0:
                raise RecoveryError("A media file has an invalid size.")
            total_size += member.size
            if total_size > MAX_MEDIA_BYTES:
                raise RecoveryError("The media archive exceeds the size limit.")
            digest = hashlib.sha256()
            size = 0
            with archive.extractfile(member) as source:
                while chunk := source.read(CHUNK_BYTES):
                    size += len(chunk)
                    digest.update(chunk)
            if size != member.size:
                raise RecoveryError("The media archive is truncated.")
            fingerprints[name] = {
                "type": "file",
                "size": size,
                "sha256": digest.hexdigest(),
            }
    for name in fingerprints:
        parts = name.split("/")
        for length in range(1, len(parts)):
            parent = fingerprints.get("/".join(parts[:length]))
            if parent and parent["type"] == "file":
                raise RecoveryError("The media archive has conflicting file paths.")
    return fingerprints


def media_fingerprints(path):
    """Validate a plain tar and return normalized file hashes and directory names.

    Ownership, permissions and timestamps are deliberately excluded. No archive
    member is extracted or used as a filesystem path by this function.
    """
    try:
        return _media_fingerprints(Path(path))
    except RecoveryError:
        raise
    except (OSError, tarfile.TarError, ValueError, UnicodeError, RecursionError):
        raise RecoveryError("The media archive could not be validated.") from None


def validate_bundle(directory):
    """Check the complete bundle, its checksums and safe media contents."""
    try:
        path = _bundle_directory(directory, require_manifest=True)
        manifest = _read_manifest(path / "manifest.json")
        for name in sorted(PAYLOAD_NAMES):
            if _file_record(path / name) != manifest["files"][name]:
                raise RecoveryError("A recovery file does not match its manifest.")
        _check_database_dump(path / "database.dump")
        _media_fingerprints(path / "media.tar")
        return manifest
    except RecoveryError:
        raise
    except (OSError, tarfile.TarError, ValueError, UnicodeError, RecursionError):
        raise RecoveryError("The recovery bundle could not be validated.") from None


def write_manifest(directory, postgres_major=16):
    """Validate two payloads and atomically write their version-1 manifest."""
    if type(postgres_major) is not int or postgres_major != 16:
        raise RecoveryError("Recovery bundles require PostgreSQL 16.")
    temporary_path = None
    try:
        path = _bundle_directory(directory, require_manifest=False)
        _check_database_dump(path / "database.dump")
        _media_fingerprints(path / "media.tar")
        manifest = {
            "version": 1,
            "postgres_major": postgres_major,
            "files": {
                name: _file_record(path / name) for name in sorted(PAYLOAD_NAMES)
            },
        }
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path, prefix=".manifest-", delete=False
        ) as target:
            temporary_path = Path(target.name)
            json.dump(manifest, target, indent=2, sort_keys=True)
            target.write("\n")
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary_path, path / "manifest.json")
        temporary_path = None
        return manifest
    except RecoveryError:
        raise
    except (OSError, tarfile.TarError, ValueError, UnicodeError, RecursionError):
        raise RecoveryError("The recovery manifest could not be written.") from None
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                raise RecoveryError(
                    "The temporary recovery manifest could not be removed."
                ) from None
