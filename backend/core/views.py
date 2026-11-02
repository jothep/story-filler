"""Public read-only APIs for stories and application configuration."""

import logging

from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import generics, status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AppConfig, Story
from .serializers import StoryListSerializer, StoryDetailSerializer, AppConfigSerializer

logger = logging.getLogger(__name__)


class StoryListAPIView(generics.ListAPIView):
    """
    API endpoint for listing all stories.
    Returns a simple list with id and title only.
    """

    queryset = Story.objects.all().order_by("-id")
    serializer_class = StoryListSerializer

    def list(self, request, *args, **kwargs):
        """
        Override list method to add logging and error handling.
        """
        try:
            logger.info(
                "Story list requested from %s",
                request.META.get("REMOTE_ADDR", "unknown"),
            )
            response = super().list(request, *args, **kwargs)
            logger.info(f"Story list returned {len(response.data)} stories")
            return response
        except (Http404, PermissionDenied, APIException):
            raise
        except Exception:
            logger.exception("Error listing stories")
            return Response(
                {
                    "error": "Failed to retrieve stories",
                    "detail": "An unexpected error occurred. Please try again later.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class StoryDetailAPIView(generics.RetrieveAPIView):
    """
    API endpoint for retrieving a single story with all related data.

    Related data is prefetched to avoid per-paragraph and per-blank queries.
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
            "background_music", "story_picture"
        ).prefetch_related(
            "word_bank",
            "paragraphs",
            "paragraphs__blank_links",
            "paragraphs__blank_links__word",
        )

    def retrieve(self, request, *args, **kwargs):
        """
        Override retrieve method to add logging and error handling.
        """
        story_id = kwargs.get("pk")

        try:
            logger.info(
                "Story detail requested: id=%s, ip=%s",
                story_id,
                request.META.get("REMOTE_ADDR", "unknown"),
            )

            instance = self.get_object()
            serializer = self.get_serializer(instance)
            data = serializer.data

            logger.info(
                "Story detail retrieved successfully: id=%s, title=%r",
                story_id,
                instance.title,
            )
            return Response(data)

        except Http404:
            # Let 404 errors pass through naturally (DRF will handle the response)
            logger.warning(f"Story not found: id={story_id}")
            raise
        except (PermissionDenied, APIException):
            raise
        except Exception:
            logger.exception("Error retrieving story %s", story_id)
            return Response(
                {
                    "error": "Failed to retrieve story",
                    "detail": "An unexpected error occurred. Please try again later.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AppConfigAPIView(APIView):
    """
    API endpoint for retrieving application configuration.
    Returns settings like menu BGM path.
    """

    def get(self, request):
        """
        Get application configuration for frontend.
        """
        try:
            logger.info(
                "App config requested from %s",
                request.META.get("REMOTE_ADDR", "unknown"),
            )
            config = AppConfig.objects.select_related("menu_bgm").first()
            data = (
                AppConfigSerializer(config).data
                if config is not None
                else {"menu_bgm": None}
            )
            logger.info("App config retrieved successfully")
            return Response(data, status=status.HTTP_200_OK)
        except (Http404, PermissionDenied, APIException):
            raise
        except Exception:
            logger.exception("Error retrieving app config")
            return Response(
                {"error": "Failed to retrieve configuration"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
