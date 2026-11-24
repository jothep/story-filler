"""Write the stories, words and library in the database as a content package.

Usage: python manage.py export_content [--output DIR] [--overwrite]

The command only reads the database. See ``core.content`` for the format.
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.content import ContentError, build_package, write_package


class Command(BaseCommand):
    help = "Write the stories, words and library in the database as a content package"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default=str(Path(settings.BASE_DIR).parent / "content"),
            help="Package directory (default: content/ at the repository root)",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Replace package files that already exist",
        )

    def handle(self, *args, **options):
        try:
            package = build_package()
        except ContentError as error:
            raise CommandError(
                "The database holds content the package cannot represent exactly:\n"
                + "\n".join(f"- {problem}" for problem in error.problems)
            ) from error
        try:
            paths = write_package(package, options["output"], options["overwrite"])
        except FileExistsError as error:
            raise CommandError(f"{error}. Use --overwrite to replace them.") from error

        paragraphs = sum(len(story["paragraphs"]) for story in package.stories.values())
        counts = {
            "stories": len(package.stories),
            "paragraphs": paragraphs,
            "words": len(package.words["words"]),
            "pictures": len(package.library["pictures"]),
            "music tracks": len(package.library["music"]),
        }
        self.stdout.write(
            f"Wrote {len(paths)} files to {options['output']} ("
            + ", ".join(f"{name}: {count}" for name, count in counts.items())
            + ")."
        )
