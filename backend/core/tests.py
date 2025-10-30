# core/tests.py

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Story

# --- Model Tests ---

class StoryModelTest(TestCase):

    
    def test_story_str_representation(self):
        print("Running: test_story_str_representation")
        story = Story.objects.create(title="My Test Story")
        self.assertEqual(str(story), "My Test Story")

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