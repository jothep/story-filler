from rest_framework import serializers
from .models import Story, Word


class WordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Word
        fields = ["id", "maori_word", "english_translation"]


class StorySerializer(serializers.ModelSerializer):
    words = WordSerializer(many=True, read_only=True)

    class Meta:
        model = Story
        fields = ["id", "title", "full_text", "words"]
