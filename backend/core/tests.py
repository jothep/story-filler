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
        config = AppConfig.objects.create(
            key="menu_bgm_path",
            value="/media/bgm/Schumann_Fantasy.mp3"
        )
        self.assertEqual(config.key, "menu_bgm_path")
        self.assertEqual(config.value, "/media/bgm/Schumann_Fantasy.mp3")

    def test_app_config_str_representation(self):
        """Test string representation of AppConfig."""
        print("Running: test_app_config_str_representation")
        config = AppConfig.objects.create(
            key="menu_bgm_path",
            value="/media/bgm/test.mp3"
        )
        self.assertEqual(str(config), "menu_bgm_path")

    def test_app_config_unique_key(self):
        """Test that keys are unique."""
        print("Running: test_app_config_unique_key")
        AppConfig.objects.create(key="test_key", value="value1")

        # Attempting to create duplicate key should raise error
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            AppConfig.objects.create(key="test_key", value="value2")

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
        # Create menu BGM configuration
        AppConfig.objects.create(
            key="menu_bgm_path",
            value="/media/bgm/Schumann_Fantasy.mp3"
        )
        cls.config_url = reverse('app-config')

    def test_get_app_config(self):
        """Test retrieving application configuration."""
        print("Running: test_get_app_config")
        response = self.client.get(self.config_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("menu_bgm_path", response.data)
        self.assertEqual(
            response.data["menu_bgm_path"],
            "/media/bgm/Schumann_Fantasy.mp3"
        )

    def test_get_app_config_empty(self):
        """Test retrieving config when no menu_bgm_path is set."""
        print("Running: test_get_app_config_empty")
        # Delete the config
        AppConfig.objects.filter(key="menu_bgm_path").delete()

        response = self.client.get(self.config_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return empty dict or null for missing config
        self.assertIn("menu_bgm_path", response.data)
        self.assertIsNone(response.data["menu_bgm_path"])