"""Save narration MP3 files to a story's pages from the command line.

Usage: python manage.py upload_narration STORY PATH... [--dry-run]

STORY is the story's id or exact title. Each file goes to the page whose
number ends its name, as on the admin's Upload narration page. Run with
--dry-run first; see docs/operations/content-admin.md.
"""

from django.core.management.base import BaseCommand, CommandError

from core.models import Story
from core.uploads import opened_files, plan_narration, run, storage_description

from ._upload_output import write_report


class Command(BaseCommand):
    help = "Save narration MP3 files to a story's pages, matched by page number"

    def add_arguments(self, parser):
        parser.add_argument("story", help="Story id or exact title")
        parser.add_argument("paths", nargs="+", help="MP3 files or folders")
        parser.add_argument(
            "--dry-run", action="store_true", help="Show the matches; save nothing"
        )

    def handle(self, *args, **options):
        story = find_story(options["story"])
        self.stdout.write(f"Story: {story.title} (id {story.pk})")
        self.stdout.write(f"Storage: {storage_description()}")
        try:
            with opened_files(options["paths"]) as uploads:
                report = run(*plan_narration(story, uploads), options["dry_run"])
        except FileNotFoundError as error:
            raise CommandError(str(error)) from error
        write_report(self, report, options["dry_run"])


def find_story(value):
    """Return the story with this id or exact title (case-insensitive)."""
    if value.isdigit():
        story = Story.objects.filter(pk=int(value)).first()
        if story:
            return story
    matches = list(Story.objects.filter(title__iexact=value))
    if len(matches) == 1:
        return matches[0]
    if matches:
        ids = ", ".join(str(story.pk) for story in matches)
        raise CommandError(f"Several stories are titled {value!r}: ids {ids}.")
    raise CommandError(f"No story has the id or title {value!r}.")
