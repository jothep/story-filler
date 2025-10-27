# core/serializers.py
from rest_framework import serializers
from .models import Story, Paragraph, Word, BackgroundMusic, BlankLink

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
        if obj.image:
            return obj.image.url
        return None

    def get_maori_audio(self, obj):
        if obj.maori_audio:
            return obj.maori_audio.url
        return None

    def get_english_audio(self, obj):
        if obj.english_audio:
            return obj.english_audio.url
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
        if obj.word:
            return WordSerializer(obj.word).data
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
        links = obj.blank_links.all()
        return BlankLinkSerializer(links, many=True).data

    def get_audio(self, obj):
        if obj.audio:
            return obj.audio.url
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
        if obj.background_music and obj.background_music.audio_file:
            return obj.background_music.audio_file.url
        return None
    
    def get_picture_url(self, obj):
        if obj.story_picture and obj.story_picture.image_file:
            return obj.story_picture.image_file.url
        return None
    
    def get_linked_words(self, obj):
        linked_word_ids = BlankLink.objects.filter(paragraph__story=obj, word__isnull=False).values_list('word_id', flat=True)

        words = Word.objects.filter(id__in=linked_word_ids).distinct()

        serializer = WordSerializer(words, many=True)
        return serializer.data
    
class StoryListSerializer(serializers.ModelSerializer):
     class Meta:
        model = Story
        fields = ["id", "title"]