# core/views.py
# Includes API views for listing all stories (List) and retrieving individual stories (Detail).
from rest_framework import generics
from .models import Story
from .serializers import StoryListSerializer, StoryDetailSerializer


class StoryListAPIView(generics.ListAPIView):
    queryset = Story.objects.all()
    serializer_class = StoryListSerializer


class StoryDetailAPIView(generics.RetrieveAPIView):
    queryset = Story.objects.all()
    serializer_class = StoryDetailSerializer
