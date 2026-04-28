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
    list_display = ('title', 'preview_picture')
    inlines = [ParagraphInline]
    filter_horizontal = ('word_bank',)
    search_fields = ('title',)
    readonly_fields = ('picture_preview', 'music_preview')

    fieldsets = (
        ('Story Information', {
            'fields': ('title',)
        }),
        ('Media', {
            'fields': ('story_picture', 'picture_preview', 'background_music', 'music_preview')
        }),
        ('Word Bank', {
            'fields': ('word_bank',)
        }),
    )

    def preview_picture(self, obj):
        """Show thumbnail in list view"""
        if obj.story_picture and obj.story_picture.image_file:
            return format_html(
                '<img src="{}" style="max-width:50px; max-height:50px;" />',
                obj.story_picture.image_file.url
            )
        return "-"
    preview_picture.short_description = "Preview"

    def picture_preview(self, obj):
        """Show full preview in edit form"""
        if obj.story_picture and obj.story_picture.image_file:
            return format_html(
                '<img src="{}" style="max-width:400px; max-height:300px; border:1px solid #ddd; padding:5px;" />',
                obj.story_picture.image_file.url
            )
        return "No image selected"
    picture_preview.short_description = "Picture Preview"

    def music_preview(self, obj):
        """Show audio player"""
        if obj.background_music and obj.background_music.audio_file:
            file_url = obj.background_music.audio_file.url
            audio_type = self._get_audio_type(file_url)
            return format_html(
                '''
                <audio controls style="width:100%; max-width:400px;">
                    <source src="{}" type="{}">
                    Your browser does not support the audio element.
                </audio>
                ''',
                file_url,
                audio_type
            )
        return "No music selected"
    music_preview.short_description = "Music Preview"

    def _get_audio_type(self, url):
        """Determine MIME type from file extension"""
        if url.endswith('.mp3'):
            return 'audio/mpeg'
        elif url.endswith('.m4a'):
            return 'audio/mp4'
        elif url.endswith('.aac'):
            return 'audio/aac'
        elif url.endswith('.wav'):
            return 'audio/wav'
        elif url.endswith('.ogg'):
            return 'audio/ogg'
        return 'audio/mpeg'


@admin.register(AppConfig)
class AppConfigAdmin(admin.ModelAdmin):
    """
    Application Configuration - Global settings
    """
    list_display = ('__str__', 'menu_bgm', 'updated_at')
    readonly_fields = ('updated_at', 'menu_bgm_preview')

    fieldsets = (
        ('Menu Settings', {
            'fields': ('menu_bgm', 'menu_bgm_preview')
        }),
        ('System', {
            'fields': ('updated_at',)
        }),
    )

    def menu_bgm_preview(self, obj):
        """Show audio player for menu BGM"""
        if obj.menu_bgm and obj.menu_bgm.audio_file:
            file_url = obj.menu_bgm.audio_file.url
            # Detect audio type from file extension
            audio_type = self._get_audio_type(file_url)
            return format_html(
                '''
                <audio controls style="width:100%; max-width:400px;">
                    <source src="{}" type="{}">
                    Your browser does not support the audio element.
                </audio>
                <p><strong>Selected:</strong> {}</p>
                ''',
                file_url,
                audio_type,
                obj.menu_bgm.title
            )
        return "No menu music selected"
    menu_bgm_preview.short_description = "Menu BGM Preview"

    def _get_audio_type(self, url):
        """Determine MIME type from file extension"""
        if url.endswith('.mp3'):
            return 'audio/mpeg'
        elif url.endswith('.m4a'):
            return 'audio/mp4'
        elif url.endswith('.aac'):
            return 'audio/aac'
        elif url.endswith('.wav'):
            return 'audio/wav'
        elif url.endswith('.ogg'):
            return 'audio/ogg'
        return 'audio/mpeg'  # default

    def has_add_permission(self, request):
        # Only allow one config instance
        return not AppConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of the config
        return False


@admin.register(StoryPicture)
class StoryPictureAdmin(admin.ModelAdmin):
    list_display = ('title', 'image_thumbnail')
    search_fields = ('title',)
    readonly_fields = ('image_preview',)

    fieldsets = (
        (None, {
            'fields': ('title', 'image_file', 'image_preview')
        }),
    )

    def image_thumbnail(self, obj):
        """Show small thumbnail in list"""
        if obj.image_file:
            return format_html(
                '<img src="{}" style="max-width:60px; max-height:60px;" />',
                obj.image_file.url
            )
        return "-"
    image_thumbnail.short_description = "Preview"

    def image_preview(self, obj):
        """Show full preview in edit form"""
        if obj.image_file:
            return format_html(
                '<img src="{}" style="max-width:600px; max-height:400px; border:1px solid #ddd; padding:5px;" />',
                obj.image_file.url
            )
        return "No image uploaded yet"
    image_preview.short_description = "Image Preview"


@admin.register(BackgroundMusic)
class BackgroundMusicAdmin(admin.ModelAdmin):
    """
    Background Music Library
    """
    list_display = ('title', 'audio_file')
    search_fields = ('title',)
    readonly_fields = ('audio_preview',)

    fieldsets = (
        (None, {
            'fields': ('title', 'audio_file', 'audio_preview')
        }),
    )

    def audio_preview(self, obj):
        """Show audio player"""
        if obj.audio_file:
            file_url = obj.audio_file.url
            audio_type = self._get_audio_type(file_url)
            return format_html(
                '''
                <audio controls style="width:100%; max-width:500px;">
                    <source src="{}" type="{}">
                    Your browser does not support the audio element.
                </audio>
                <p><em>File: {}</em></p>
                ''',
                file_url,
                audio_type,
                obj.audio_file.name.split('/')[-1]
            )
        return "No audio uploaded yet"
    audio_preview.short_description = "Audio Preview"

    def _get_audio_type(self, url):
        """Determine MIME type from file extension"""
        if url.endswith('.mp3'):
            return 'audio/mpeg'
        elif url.endswith('.m4a'):
            return 'audio/mp4'
        elif url.endswith('.aac'):
            return 'audio/aac'
        elif url.endswith('.wav'):
            return 'audio/wav'
        elif url.endswith('.ogg'):
            return 'audio/ogg'
        return 'audio/mpeg'


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    """
    Manage words (Word Bank)
    """
    list_display = ('english_translation', 'maori_word', 'has_image', 'has_audio')
    search_fields = ('english_translation', 'maori_word')
    readonly_fields = ('image_preview', 'maori_audio_preview', 'english_audio_preview')

    fieldsets = (
        ('Word Information', {
            'fields': ('maori_word', 'english_translation')
        }),
        ('Image', {
            'fields': ('image', 'image_preview')
        }),
        ('Audio', {
            'fields': (
                ('maori_audio', 'maori_audio_preview'),
                ('english_audio', 'english_audio_preview')
            )
        }),
    )

    def has_image(self, obj):
        return "✓" if obj.image else "-"
    has_image.short_description = "Image"

    def has_audio(self, obj):
        return "✓" if (obj.maori_audio or obj.english_audio) else "-"
    has_audio.short_description = "Audio"

    def image_preview(self, obj):
        """Show image preview"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:300px; max-height:300px; border:1px solid #ddd; padding:5px;" />',
                obj.image.url
            )
        return "No image uploaded yet"
    image_preview.short_description = "Image Preview"

    def maori_audio_preview(self, obj):
        """Show Maori audio player"""
        if obj.maori_audio:
            file_url = obj.maori_audio.url
            audio_type = self._get_audio_type(file_url)
            return format_html(
                '''
                <audio controls style="width:100%; max-width:300px;">
                    <source src="{}" type="{}">
                    Your browser does not support the audio element.
                </audio>
                ''',
                file_url,
                audio_type
            )
        return "No Maori audio"
    maori_audio_preview.short_description = "Maori Audio"

    def english_audio_preview(self, obj):
        """Show English audio player"""
        if obj.english_audio:
            file_url = obj.english_audio.url
            audio_type = self._get_audio_type(file_url)
            return format_html(
                '''
                <audio controls style="width:100%; max-width:300px;">
                    <source src="{}" type="{}">
                    Your browser does not support the audio element.
                </audio>
                ''',
                file_url,
                audio_type
            )
        return "No English audio"
    english_audio_preview.short_description = "English Audio"

    def _get_audio_type(self, url):
        """Determine MIME type from file extension"""
        if url.endswith('.mp3'):
            return 'audio/mpeg'
        elif url.endswith('.m4a'):
            return 'audio/mp4'
        elif url.endswith('.aac'):
            return 'audio/aac'
        elif url.endswith('.wav'):
            return 'audio/wav'
        elif url.endswith('.ogg'):
            return 'audio/ogg'
        return 'audio/mpeg'


@admin.register(BlankLink)
class BlankLinkAdmin(admin.ModelAdmin):
    """
    Manage links between Placeholder and Word Bank
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