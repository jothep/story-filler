# core/urls.py
# Define API endpoints for the 'core' app.
# Map URLs to the StoryList and StoryDetail views.
from django.urls import path
from .views import StoryListAPIView, StoryDetailAPIView

urlpatterns = [
    path("stories/", StoryListAPIView.as_view(), name="story-list"),
    path("stories/<int:pk>/", StoryDetailAPIView.as_view(), name="story-detail"),
]
