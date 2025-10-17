# stories/serializers.py
from rest_framework import serializers
from .models import Story, Word

class WordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Word
        fields = ['id', 'maori_word', 'english_translation']

class StorySerializer(serializers.ModelSerializer):
    # 将所有词汇嵌套在它们所属的故事中
    words = WordSerializer(many=True, read_only=True) 

    class Meta:
        model = Story
        fields = ['id', 'title', 'full_text', 'words']