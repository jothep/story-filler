"""Serialize story relationships and optional media URLs for the public API."""

import logging

from rest_framework import serializers

from .models import Story, Paragraph, Word, BackgroundMusic, BlankLink

logger = logging.getLogger(__name__)


def file_url(file, description):
    """Return a stored file's URL, or None when it is missing or unreadable."""
    if not file:
        return None
    try:
        return file.url
    except (ValueError, AttributeError) as e:
        logger.warning("Failed to get URL for %s: %s", description, e)
        return None


def language_data(language):
    return {"code": language.code, "name": language.name} if language else None


def form_in(word, language_id):
    """Return the word's form in a language, using prefetched forms."""
    for form in word.forms.all():
        if form.language_id == language_id:
            return form
    return None


def word_data(instance, story):
    """Return a word as ``story`` uses it.

    ``text`` and ``audio`` are in the story's learning language;
    ``translation`` and ``translation_audio`` are in the story language, and
    null when the two are the same.

    The ``maori_*`` and ``english_*`` names are kept for game bundles that
    predate these fields: the learning language fills the ``maori_*`` names
    and the story language the ``english_*`` names.
    """
    learning_id = story.learning_language_id if story else None
    story_language_id = story.language_id if story else None
    learning = form_in(instance, learning_id)
    translation = (
        form_in(instance, story_language_id)
        if story_language_id != learning_id
        else None
    )
    text = learning.text if learning else None
    audio = file_url(learning and learning.audio, f"Word {instance.id} audio")
    translation_text = translation.text if translation else None
    translation_audio = file_url(
        translation and translation.audio, f"Word {instance.id} translation audio"
    )
    return {
        "id": instance.id,
        "key": instance.key,
        "image": file_url(instance.image, f"Word {instance.id} image"),
        "text": text,
        "audio": audio,
        "translation": translation_text,
        "translation_audio": translation_audio,
        "maori_word": text,
        "english_translation": translation_text if translation else text,
        "maori_audio": audio,
        "english_audio": translation_audio if translation else audio,
    }


class BlankLinkSerializer(serializers.ModelSerializer):
    word = serializers.SerializerMethodField()

    class Meta:
        model = BlankLink
        fields = ["id", "placeholder", "word"]

    def get_word(self, obj):
        """Serialize associated word if it exists."""
        if obj.word:
            return word_data(obj.word, self.context.get("story"))
        return None


class ParagraphSerializer(serializers.ModelSerializer):
    blank_links = serializers.SerializerMethodField()
    audio = serializers.SerializerMethodField()

    class Meta:
        model = Paragraph
        fields = ["id", "order", "text", "audio", "blank_links"]

    def get_blank_links(self, obj):
        """Get all blank links for this paragraph."""
        links = obj.blank_links.all()
        return BlankLinkSerializer(links, many=True, context=self.context).data

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
    words_in_bank = serializers.SerializerMethodField(method_name="get_linked_words")
    background_music_url = serializers.SerializerMethodField()
    picture_url = serializers.SerializerMethodField()
    language = serializers.SerializerMethodField()
    learning_language = serializers.SerializerMethodField()

    class Meta:
        model = Story
        fields = [
            "id",
            "title",
            "language",
            "learning_language",
            "background_music_url",
            "paragraphs",
            "words_in_bank",
            "picture_url",
        ]

    def to_representation(self, instance):
        # Nested word serializers pick their language forms for this story.
        self.context["story"] = instance
        return super().to_representation(instance)

    def get_language(self, obj):
        return language_data(obj.language)

    def get_learning_language(self, obj):
        return language_data(obj.learning_language)

    def get_background_music_url(self, obj):
        """Get background music URL with error handling."""
        if obj.background_music and obj.background_music.audio_file:
            try:
                return obj.background_music.audio_file.url
            except (ValueError, AttributeError) as e:
                logger.warning(
                    f"Failed to get background music URL for Story {obj.id}: {e}"
                )
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
        """Get all words used in this story's blank links."""
        linked_word_ids = BlankLink.objects.filter(
            paragraph__story=obj, word__isnull=False
        ).values_list("word_id", flat=True)

        words = (
            Word.objects.filter(id__in=linked_word_ids)
            .distinct()
            .prefetch_related("forms")
        )
        story = self.context.get("story")
        return [word_data(word, story) for word in words]


class StoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Story
        fields = ["id", "title"]


class BackgroundMusicSerializer(serializers.ModelSerializer):
    """Serializer for BackgroundMusic model."""

    audio_url = serializers.SerializerMethodField()

    class Meta:
        model = BackgroundMusic
        fields = ["id", "title", "audio_url"]

    def get_audio_url(self, obj):
        """Get audio URL with error handling."""
        if obj.audio_file:
            try:
                return obj.audio_file.url
            except (ValueError, AttributeError) as e:
                logger.warning(f"Failed to get audio URL for BGM {obj.id}: {e}")
                return None
        return None


class AppConfigSerializer(serializers.Serializer):
    """
    Serializer for application configuration.
    Returns menu BGM information for frontend use.
    """

    menu_bgm = BackgroundMusicSerializer(allow_null=True, required=False)
