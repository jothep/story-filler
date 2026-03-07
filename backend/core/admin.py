# core/admin.py
# Configure the Django admin interface for all core models.
# Improve usability using inlines, filter_horizontal, and custom forms.
from django.contrib import admin
from django.utils.html import format_html
from .models import Story, Paragraph, Word, BackgroundMusic, BlankLink, StoryPicture, AppConfig
from .forms import BlankLinkForm

class ParagraphInline(admin.StackedInline):
    """
    Allows to add and edit Paragraphs in a stacked form within the Story edit page.
    """
    model = Paragraph
    extra = 1 
    fields = ('order', 'text', 'audio')

@admin.register(Story) 
class StoryAdmin(admin.ModelAdmin):
    """
    Main menu of "Story"
    """
    list_display = ('title',)
    inlines = [ParagraphInline]
    filter_horizontal = ('word_bank',)
    search_fields = ('title',) 

@admin.register(AppConfig)
class AppConfigAdmin(admin.ModelAdmin):
    """
    Application Configuration
    """
    list_display = ('key', 'value', 'description', 'updated_at')
    search_fields = ('key', 'description')
    readonly_fields = ('updated_at',)

@admin.register(StoryPicture)
class StoryPictureAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('title',)

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
    list_display = ('english_translation', 'maori_word', 'image', 'maori_audio', 'english_audio')
    search_fields = ('english_translation', 'maori_word')

@admin.register(BlankLink)
class BlankLinkAdmin(admin.ModelAdmin):
    """
    Mannage links between Placeholder and Word Bank 
    """
    form = BlankLinkForm
    list_display = ('paragraph', 'placeholder', 'word')
    list_filter = ('paragraph__story__title',) 
    
    
    autocomplete_fields = ('word',) 
    
   
    readonly_fields = ('display_paragraph_text',) 
    
    fieldsets = (
        (None, {
            'fields': ('paragraph', 'display_paragraph_text', 'placeholder', 'word')
        }),
    )

    def display_paragraph_text(self, obj):
        if obj.paragraph:

            return format_html("<pre>{}</pre>", obj.paragraph.text)
        return "N/A (Please select a paragraph first)"
    display_paragraph_text.short_description = "Paragraph Text Preview"