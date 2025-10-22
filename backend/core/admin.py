# core/admin.py
from django.contrib import admin
from .models import Story, Paragraph, Word, BackgroundMusic

class WordInline(admin.TabularInline):
    """
    Allows to add and edit Word documents in batches, within the Paragraph edit page.
    """
    model = Word 
    extra = 1 

class ParagraphInline(admin.StackedInline):
    """
    Allows to add and edit Paragraphs in a stacked form within the Story edit page.
    """
    model = Paragraph
    extra = 1 
    inlines = [WordInline] 

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