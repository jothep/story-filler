#!/bin/bash
# Retired entry point: old archives and implicit targets are not safe to reuse.
printf '%s\n' \
    'ERROR: This legacy backup/restore entry point is disabled.' \
    'Use python3 scripts/local_recovery.py with explicit local targets.' \
    'Read VOLUME_BACKUP_GUIDE.md for backup, verification and isolated recovery.' \
    'No containers, volumes, backups or cloud resources were changed.' >&2
exit 1
