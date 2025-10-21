from rest_framework import generics
from .models import Story
from .serializers import StorySerializer


class StoryListAPIView(generics.ListAPIView):
    queryset = Story.objects.all()
    serializer_class = StorySerializer


class StoryDetailAPIView(generics.RetrieveAPIView):
    queryset = Story.objects.all()
    serializer_class = StorySerializer
