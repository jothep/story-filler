# core/serializers.py
from rest_framework import serializers
from .models import Story, Paragraph, Word, BackgroundMusic, BlankLink

class WordSerializer(serializers.ModelSerializer):
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

class BlankLinkSerializer(serializers.ModelSerializer):
    word = WordSerializer(read_only=True)

    class Meta:
        model = BlankLink
        fields = [
            "id",
            "placeholder", 
            "word"         
        ]

class ParagraphSerializer(serializers.ModelSerializer):
    blank_links = BlankLinkSerializer(many=True, read_only=True)
    class Meta:
        model = Paragraph
        fields = [
            "id",
            "order",
            "text",
            "audio",
            "blank_links"
        ]

class StoryDetailSerializer(serializers.ModelSerializer):

    paragraphs = ParagraphSerializer(many=True, read_only=True)

    words_in_bank = serializers.SerializerMethodField(method_name='get_linked_words')

    background_music_url = serializers.ReadOnlyField(source='background_music.audio_file.url')

    class Meta:
        model = Story
        fields = [
            "id",
            "title",
            "background_music_url",
            "paragraphs",
            "words_in_bank"
        ]
    def get_linked_words(self, obj):
        linked_word_ids = BlankLink.objects.filter(paragraph__story=obj, word__isnull=False).values_list('word_id', flat=True)

        words = Word.objects.filter(id__in=linked_word_ids).distinct()
        serializer = WordSerializer(words, many=True)
        return serializer.data
    
class StoryListSerializer(serializers.ModelSerializer):
     class Meta:
        model = Story
        fields = ["id", "title"]