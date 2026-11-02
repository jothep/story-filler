"""Run historical demo security regressions without opening any database."""

from pathlib import Path
import secrets
import sys

import django
from django.conf import settings
from django.test.runner import DiscoverRunner


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "demo"))
    settings.configure(
        SECRET_KEY=secrets.token_urlsafe(48),
        INSTALLED_APPS=["polls"],
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "unused_demo_security",
                "HOST": "127.0.0.1",
                "PORT": "1",
            }
        },
    )
    django.setup()
    # SimpleTestCase refuses database access. Stored question text is supplied
    # as a test fixture through a mocked query, not a live database.
    return DiscoverRunner(verbosity=2).run_tests(["polls.tests"])


if __name__ == "__main__":
    raise SystemExit(main())
