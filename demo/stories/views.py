# stories/views.py
from rest_framework import generics
from .models import Story
from .serializers import StorySerializer

# This view for get list of all stories
class StoryListAPIView(generics.ListAPIView):
    queryset = Story.objects.all()
    serializer_class = StorySerializer

# The view for get detail info by a story
class StoryDetailAPIView(generics.RetrieveAPIView):
    queryset = Story.objects.all()
    serializer_class = StorySerializer