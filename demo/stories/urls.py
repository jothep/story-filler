# stories/urls.py
from django.urls import path
from .views import StoryListAPIView, StoryDetailAPIView

urlpatterns = [
    path('stories/', StoryListAPIView.as_view(), name='story-list'),
    path('stories/<int:pk>/', StoryDetailAPIView.as_view(), name='story-detail'),
]