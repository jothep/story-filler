"""Shared output for the upload commands."""

from django.core.management.base import CommandError


def write_report(command, report, dry_run):
    """Print what was (or would be) saved and skipped; fail if anything was skipped."""
    for line in report.saved:
        command.stdout.write(("PLAN " if dry_run else "SAVED ") + line)
    for line in report.skipped:
        command.stdout.write("SKIPPED " + line)
    verb = "would be saved" if dry_run else "saved"
    command.stdout.write(f"{len(report.saved)} {verb}, {len(report.skipped)} skipped.")
    if report.skipped:
        raise CommandError(f"{len(report.skipped)} files were not saved.")
