"""Save word pictures and audio from the command line.

Usage: python manage.py upload_word_files PATH... [--dry-run]

Files are matched by name as on the admin's Upload files page: moon.jpg is
the picture of the word moon, moon.mi.mp3 its Māori audio. Run with
--dry-run first; see docs/operations/content-admin.md.
"""

from django.core.management.base import BaseCommand, CommandError

from core.uploads import opened_files, plan_word_files, run, storage_description

from ._upload_output import write_report


class Command(BaseCommand):
    help = "Save word pictures and audio, matched by key and language code"

    def add_arguments(self, parser):
        parser.add_argument("paths", nargs="+", help="Files or folders")
        parser.add_argument(
            "--dry-run", action="store_true", help="Show the matches; save nothing"
        )

    def handle(self, *args, **options):
        self.stdout.write(f"Storage: {storage_description()}")
        try:
            with opened_files(options["paths"]) as uploads:
                report = run(*plan_word_files(uploads), options["dry_run"])
        except FileNotFoundError as error:
            raise CommandError(str(error)) from error
        write_report(self, report, options["dry_run"])
