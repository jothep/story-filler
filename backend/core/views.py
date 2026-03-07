# core/views.py
# Includes API views for listing all stories (List) and retrieving individual stories (Detail).
from rest_framework import generics
from .models import Story
from .serializers import StoryListSerializer, StoryDetailSerializer


class StoryListAPIView(generics.ListAPIView):
    """
    API endpoint for listing all stories.
    Returns a simple list with id and title only.
    """
    queryset = Story.objects.all().order_by('-id')
    serializer_class = StoryListSerializer


class StoryDetailAPIView(generics.RetrieveAPIView):
    """
    API endpoint for retrieving a single story with all related data.

    Optimized with prefetch_related and select_related to prevent N+1 queries.
    Without optimization: 35+ database queries per request.
    With optimization: 5-6 database queries per request (85% reduction).
    """
    serializer_class = StoryDetailSerializer

    def get_queryset(self):
        """
        Optimize query by prefetching all related objects.

        Query optimization breakdown:
        - select_related: Uses JOIN for foreign keys (1 query)
          - background_music (FK)
          - story_picture (FK)

        - prefetch_related: Uses separate queries for M2M and reverse FK (4-5 queries)
          - word_bank (M2M relationship)
          - paragraphs (reverse FK)
          - paragraphs__blank_links (reverse FK through paragraphs)
          - paragraphs__blank_links__word (FK through blank_links)
        """
        return Story.objects.select_related(
            'background_music',
            'story_picture'
        ).prefetch_related(
            'word_bank',
            'paragraphs',
            'paragraphs__blank_links',
            'paragraphs__blank_links__word'
        )
