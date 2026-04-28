"""
Django management command to test GCS connectivity
Usage: python manage.py test_gcs
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


class Command(BaseCommand):
    help = 'Test GCS connectivity and django-storages configuration'

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("GCS Configuration Test")
        self.stdout.write("=" * 60)

        self.stdout.write(f"\nUSE_GCS: {getattr(settings, 'USE_GCS', False)}")

        if hasattr(settings, 'STORAGES'):
            self.stdout.write(f"STORAGES (default backend): {settings.STORAGES.get('default', {}).get('BACKEND', 'N/A')}")

        if hasattr(settings, 'GS_BUCKET_NAME'):
            self.stdout.write(f"GS_BUCKET_NAME: {settings.GS_BUCKET_NAME}")
            self.stdout.write(f"GS_DEFAULT_ACL: {getattr(settings, 'GS_DEFAULT_ACL', 'N/A')}")
            self.stdout.write(f"GS_CREDENTIALS: {getattr(settings, 'GS_CREDENTIALS', 'N/A')}")

        self.stdout.write(f"\nStorage backend: {default_storage.__class__.__name__}")
        self.stdout.write(f"Storage module: {default_storage.__class__.__module__}")

        # Test file write
        try:
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write("Testing file upload to GCS...")
            self.stdout.write("=" * 60)

            test_content = ContentFile(b"Hello from Django GCS test!")
            file_name = "test/django_test.txt"

            self.stdout.write(f"\nAttempting to save file: {file_name}")
            saved_name = default_storage.save(file_name, test_content)
            self.stdout.write(self.style.SUCCESS(f"✓ File saved: {saved_name}"))

            file_url = default_storage.url(saved_name)
            self.stdout.write(self.style.SUCCESS(f"✓ File URL: {file_url}"))

            # Test file exists
            exists = default_storage.exists(saved_name)
            self.stdout.write(self.style.SUCCESS(f"✓ File exists: {exists}"))

            # Clean up
            default_storage.delete(saved_name)
            self.stdout.write(self.style.SUCCESS(f"✓ File deleted"))

            self.stdout.write(self.style.SUCCESS("\n✓✓✓ GCS connection is working! ✓✓✓"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n✗✗✗ Error: {e} ✗✗✗"))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
