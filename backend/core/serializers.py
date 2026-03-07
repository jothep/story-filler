# core/serializers.py
# Defines the DRF serializer for converting complex Django models (such as Stories) into JSON.
# Handles nested relationships and media file URLs.
import logging
from rest_framework import serializers
from .models import Story, Paragraph, Word, BackgroundMusic, BlankLink, AppConfig

logger = logging.getLogger(__name__)


class WordSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    maori_audio = serializers.SerializerMethodField()
    english_audio = serializers.SerializerMethodField()

    class Meta:
        model = Word
        fields = [
            "id",
            "maori_word",
            "english_translation",
            "image",
            "maori_audio",
            "english_audio"
        ]

    def get_image(self, obj):
        """Get image URL with error handling for missing files."""
        if obj.image:
            try:
                return obj.image.url
            except (ValueError, AttributeError) as e:
                logger.warning(f"Failed to get image URL for Word {obj.id}: {e}")
                return None
        return None

    def get_maori_audio(self, obj):
        """Get Maori audio URL with error handling for missing files."""
        if obj.maori_audio:
            try:
                return obj.maori_audio.url
            except (ValueError, AttributeError) as e:
                logger.warning(f"Failed to get Maori audio URL for Word {obj.id}: {e}")
                return None
        return None

    def get_english_audio(self, obj):
        """Get English audio URL with error handling for missing files."""
        if obj.english_audio:
            try:
                return obj.english_audio.url
            except (ValueError, AttributeError) as e:
                logger.warning(f"Failed to get English audio URL for Word {obj.id}: {e}")
                return None
        return None


class BlankLinkSerializer(serializers.ModelSerializer):
    word = serializers.SerializerMethodField()

    class Meta:
        model = BlankLink
        fields = [
            "id",
            "placeholder",
            "word"
        ]

    def get_word(self, obj):
        """Serialize associated word if it exists."""
        if obj.word:
            try:
                return WordSerializer(obj.word).data
            except Exception as e:
                logger.error(f"Failed to serialize word for BlankLink {obj.id}: {e}")
                return None
        return None


class ParagraphSerializer(serializers.ModelSerializer):
    blank_links = serializers.SerializerMethodField()
    audio = serializers.SerializerMethodField()

    class Meta:
        model = Paragraph
        fields = [
            "id",
            "order",
            "text",
            "audio",
            "blank_links"
        ]

    def get_blank_links(self, obj):
        """Get all blank links for this paragraph."""
        try:
            links = obj.blank_links.all()
            return BlankLinkSerializer(links, many=True).data
        except Exception as e:
            logger.error(f"Failed to serialize blank links for Paragraph {obj.id}: {e}")
            return []

    def get_audio(self, obj):
        """Get paragraph audio URL with error handling."""
        if obj.audio:
            try:
                return obj.audio.url
            except (ValueError, AttributeError) as e:
                logger.warning(f"Failed to get audio URL for Paragraph {obj.id}: {e}")
                return None
        return None


class StoryDetailSerializer(serializers.ModelSerializer):
    paragraphs = ParagraphSerializer(many=True, read_only=True, context={})
    words_in_bank = serializers.SerializerMethodField(method_name='get_linked_words')
    background_music_url = serializers.SerializerMethodField()
    picture_url = serializers.SerializerMethodField()

    class Meta:
        model = Story
        fields = [
            "id",
            "title",
            "background_music_url",
            "paragraphs",
            "words_in_bank",
            "picture_url"
        ]

    def get_background_music_url(self, obj):
        """Get background music URL with error handling."""
        if obj.background_music and obj.background_music.audio_file:
            try:
                return obj.background_music.audio_file.url
            except (ValueError, AttributeError) as e:
                logger.warning(f"Failed to get background music URL for Story {obj.id}: {e}")
                return None
        return None

    def get_picture_url(self, obj):
        """Get story picture URL with error handling."""
        if obj.story_picture and obj.story_picture.image_file:
            try:
                return obj.story_picture.image_file.url
            except (ValueError, AttributeError) as e:
                logger.warning(f"Failed to get picture URL for Story {obj.id}: {e}")
                return None
        return None

    def get_linked_words(self, obj):
        """
        Get all words used in this story's blank links.

        Note: This query is now optimized via prefetch_related in the view,
        so it doesn't cause N+1 queries anymore.
        """
        try:
            linked_word_ids = BlankLink.objects.filter(
                paragraph__story=obj,
                word__isnull=False
            ).values_list('word_id', flat=True)

            words = Word.objects.filter(id__in=linked_word_ids).distinct()
            serializer = WordSerializer(words, many=True)
            return serializer.data
        except Exception as e:
            logger.error(f"Failed to get linked words for Story {obj.id}: {e}")
            return []


class StoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Story
        fields = ["id", "title"]


class AppConfigSerializer(serializers.Serializer):
    """
    Serializer for application configuration.
    Returns a dictionary of key-value pairs for frontend use.
    """
    menu_bgm_path = serializers.CharField(allow_null=True, required=False)

    def to_representation(self, _):
        """
        Convert AppConfig queryset to a dictionary.
        Note: instance parameter unused as we fetch config directly.
        """
        try:
            menu_bgm = AppConfig.objects.filter(key="menu_bgm_path").first()
            return {
                "menu_bgm_path": menu_bgm.value if menu_bgm else None
            }
        except Exception as e:
            logger.error(f"Failed to retrieve app config: {e}")
            return {
                "menu_bgm_path": None
            }
