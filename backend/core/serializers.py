from rest_framework import serializers
from .models import Story, Word, Paragraph

class WordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Word
        fields = [
            "id",
            "maori_word",
            "english_translation",
            "image",
            "maori_audio",
            "english_audio",
            "placeholder"
        ]

class ParagraphSerializer(serializers.ModelSerializer):
    words = WordSerializer(many=True, read_only=True)
    class Meta:
        model = Paragraph
        fields = [
            "id",
            "order",
            "text",
            "audio",
            "words"
        ]

class StoryDetailSerializer(serializers.ModelSerializer):
    # 使用嵌套序列化器来包含所有段落
    paragraphs = ParagraphSerializer(many=True, read_only=True)
    # 同时包含这个故事需要的所有单词（用于填空选择）
    # 这里我们假设 Word 通过 placeholder 关联到 Story，实际需要调整模型关系或查询
    # 或者，前端可以根据 paragraphs 中的 text 自己提取需要的单词信息
    # 为了简化，我们先直接返回所有关联的 Word (通过 Paragraph)
    words = serializers.SerializerMethodField()

    background_music_url = serializers.ReadOnlyField(source='background_music.audio_file.url')

    class Meta:
        model = Story
        fields = [
            "id",
            "title",
            "background_music_url",
            "paragraphs",
            "words"
        ]
    def get_words(self, obj):
        words = Word.objects.filter(paragraph__story=obj).distinct()
        serializer = WordSerializer(words, many=True)
        return serializer.data
    
class StoryListSerializer(serializers.ModelSerializer):
     class Meta:
        model = Story
        fields = ["id", "title"]