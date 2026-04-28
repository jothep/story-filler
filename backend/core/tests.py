# core/tests.py

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Story, AppConfig

# --- Model Tests ---

class StoryModelTest(TestCase):


    def test_story_str_representation(self):
        print("Running: test_story_str_representation")
        story = Story.objects.create(title="My Test Story")
        self.assertEqual(str(story), "My Test Story")


class AppConfigModelTest(TestCase):
    """Test AppConfig model for global application settings."""

    def test_app_config_creation(self):
        """Test creating an AppConfig instance."""
        print("Running: test_app_config_creation")
        config = AppConfig.objects.create()
        self.assertIsNotNone(config)
        self.assertIsNone(config.menu_bgm)

    def test_app_config_str_representation(self):
        """Test string representation of AppConfig."""
        print("Running: test_app_config_str_representation")
        config = AppConfig.objects.create()
        self.assertIn("App Config", str(config))

    def test_app_config_single_instance(self):
        """Test that only one AppConfig instance can exist."""
        print("Running: test_app_config_single_instance")
        AppConfig.objects.create()

        # Attempting to create second instance should raise error
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            config2 = AppConfig()
            config2.save()

# --- API View Tests ---

class StoryAPITest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        print("Running: setUpTestData for API tests")
        cls.story1 = Story.objects.create(title="Rona and the Moon")
        cls.story2 = Story.objects.create(title="The Great Waka")
        
        cls.list_url = reverse('story-list') 
        cls.detail_url = reverse('story-detail', args=[cls.story1.pk])
        cls.detail_not_found_url = reverse('story-detail', args=[999]) 

    def test_get_story_list(self):
        print("Running: test_get_story_list")
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) 

    def test_get_story_detail(self):
        print("Running: test_get_story_detail")
        response = self.client.get(self.detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.story1.title)

    def test_get_story_detail_not_found(self):
        print("Running: test_get_story_detail_not_found")
        response = self.client.get(self.detail_not_found_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AppConfigAPITest(APITestCase):
    """Test AppConfig API endpoints."""

    @classmethod
    def setUpTestData(cls):
        print("Running: setUpTestData for AppConfig API tests")
        # Create app configuration
        AppConfig.objects.create()
        cls.config_url = reverse('app-config')

    def test_get_app_config(self):
        """Test retrieving application configuration."""
        print("Running: test_get_app_config")
        response = self.client.get(self.config_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Config should exist and have menu_bgm field
        self.assertIn("menu_bgm", response.data)

    def test_get_app_config_no_bgm(self):
        """Test retrieving config when no menu_bgm is set."""
        print("Running: test_get_app_config_no_bgm")
        response = self.client.get(self.config_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # menu_bgm should be null when not set
        self.assertIn("menu_bgm", response.data)
        self.assertIsNone(response.data["menu_bgm"])


# --- Storage Configuration Tests ---

class StorageConfigurationTest(TestCase):
    """Test storage backend configuration (local, MinIO, AWS S3)."""

    def test_default_uses_local_storage(self):
        """Test that default configuration uses local file storage."""
        print("Running: test_default_uses_local_storage")
        from django.conf import settings

        # Verify local storage configuration
        self.assertEqual(settings.MEDIA_URL, "/media/")

    def test_media_url_generation_local(self):
        """Test media URL generation for local storage."""
        print("Running: test_media_url_generation_local")
        from .models import StoryPicture
        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image
        from io import BytesIO

        # Create a real test image to avoid compression errors
        img = Image.new('RGB', (100, 100), color='red')
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)

        test_image = SimpleUploadedFile(
            "test.jpg",
            img_io.read(),
            content_type="image/jpeg"
        )

        picture = StoryPicture.objects.create(
            title="Test Picture",
            image_file=test_image
        )

        # URL should start with /media/ for local storage
        self.assertTrue(picture.image_file.url.startswith('/media/'))

        # Cleanup
        picture.delete()