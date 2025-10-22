# core/admin.py
from django.contrib import admin
from .models import Story, Paragraph, Word, BackgroundMusic, BlankLink

class BlankLinkInline(admin.TabularInline):
    """
    Allows to manage placeholder links to words in the Word Bank within the Paragraph editing page.
    """
    model = BlankLink
    extra = 1

class ParagraphInline(admin.StackedInline):
    """
    Allows to add and edit Paragraphs in a stacked form within the Story edit page.
    """
    model = Paragraph
    extra = 1 
    inlines = [BlankLinkInline]

@admin.register(Story) 
class StoryAdmin(admin.ModelAdmin):
    """
    Main menu of "Story"
    """
    list_display = ('title',)
    inlines = [ParagraphInline] 

@admin.register(BackgroundMusic)
class BackgroundMusicAdmin(admin.ModelAdmin):
    """
    BGM
    """
    list_display = ('title', 'audio_file')
    search_fields = ('title',)

@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    """
    Manage words (Word Bank)
    """
    list_display = ('maori_word', 'english_translation', 'image', 'maori_audio', 'english_audio')
    search_fields = ('maori_word', 'english_translation')
