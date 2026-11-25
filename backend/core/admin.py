# core/admin.py
# Configure the Django admin interface for all core models.
# Improve usability using inlines, media previews and custom forms.
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html, format_html_join
from .blanks import build_word_index, link_placeholders, remove_stale_links
from .completeness import check_story
from .models import (
    Story,
    Paragraph,
    Word,
    WordForm,
    Language,
    BackgroundMusic,
    BlankLink,
    StoryPicture,
    AppConfig,
)
from .forms import BlankLinkForm, ParagraphForm, StoryAdminForm, UploadFilesForm
from .uploads import save_narration, save_word_files
from .pages import apply_pages

AUDIO_MIME_TYPES = {
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".aac": "audio/aac",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
}


def audio_mime_type(url):
    """Return the MIME type for an audio URL, from its file extension."""
    for extension, mime_type in AUDIO_MIME_TYPES.items():
        if url.endswith(extension):
            return mime_type
    return "audio/mpeg"


def audio_player(file, width=300):
    """Return an audio player for a stored file, or None when there is none."""
    if not file:
        return None
    file_url = file.url
    return format_html(
        '<audio controls style="width:100%; max-width:{}px;">'
        '<source src="{}" type="{}">'
        "Your browser does not support the audio element.</audio>",
        width,
        file_url,
        audio_mime_type(file_url),
    )


# Cloud Run accepts requests up to 32 MiB.
UPLOAD_LIMIT = "Upload at most about 30 MB at a time; split larger sets."
MP3_RULE = (
    "Audio must be MP3. Convert other formats first with scripts/convert_audio.py."
)


def upload_page(model_admin, request, page):
    """Render a many-file upload page and save the files on POST."""
    form = UploadFilesForm(request.POST or None, request.FILES or None)
    report = None
    if request.method == "POST" and form.is_valid():
        report = page["save"](form.cleaned_data["files"])
    context = {
        **model_admin.admin_site.each_context(request),
        "opts": model_admin.model._meta,
        "form": form,
        "report": report,
        **{key: value for key, value in page.items() if key != "save"},
    }
    return TemplateResponse(request, "admin/core/upload_files.html", context)


class ParagraphInline(admin.StackedInline):
    """
    Allows to add and edit Paragraphs in a stacked form within the Story edit page.
    """

    model = Paragraph
    form = ParagraphForm
    extra = 1
    fields = ("order", "text", "audio")


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    """
    Main menu of "Story"
    """

    form = StoryAdminForm
    change_form_template = "admin/core/story/change_form.html"
    list_display = ("title", "status", "completeness", "preview_picture")
    list_filter = ("status",)
    inlines = [ParagraphInline]
    search_fields = ("title",)
    readonly_fields = ("completeness_report", "picture_preview", "music_preview")

    fieldsets = (
        (
            "Story Information",
            {"fields": ("title", "status", ("language", "learning_language"))},
        ),
        ("Before publishing", {"fields": ("completeness_report",)}),
        ("Pages", {"fields": ("story_text", "story_text_version")}),
        (
            "Media",
            {
                "fields": (
                    "story_picture",
                    "picture_preview",
                    "background_music",
                    "music_preview",
                )
            },
        ),
    )

    def save_related(self, request, form, formsets, change):
        """Bring Blank Links in line with the saved paragraph text.

        Links whose placeholder left the text are removed for editors who may
        delete Blank Links; new placeholders are linked for editors who may add
        them.
        """
        super().save_related(request, form, formsets, change)
        self.apply_story_text(request, form, formsets)
        can_add = request.user.has_perm("core.add_blanklink")
        can_delete = request.user.has_perm("core.delete_blanklink")
        if not (can_add or can_delete):
            self.keep_unplayable_stories_in_draft(request, form.instance)
            return
        index = build_word_index() if can_add else None
        removed = []
        unlinked = []
        for paragraph in form.instance.paragraphs.all():
            if can_delete:
                removed.extend(remove_stale_links(paragraph))
            if can_add:
                unlinked.extend(link_placeholders(paragraph, index))
        if removed:
            self.message_user(
                request,
                "Removed Blank Links for blanks no longer in the text: "
                + ", ".join(dict.fromkeys(removed))
                + ".",
                level=messages.INFO,
            )
        if unlinked:
            self.message_user(
                request,
                "No single word matched "
                + ", ".join(dict.fromkeys(unlinked))
                + ". Add these on the Blank Links page.",
                level=messages.WARNING,
            )
        self.keep_unplayable_stories_in_draft(request, form.instance)

    def get_urls(self):
        upload = path(
            "<int:story_id>/narration/",
            self.admin_site.admin_view(self.narration_view),
            name="core_story_narration",
        )
        return [upload] + super().get_urls()

    def narration_view(self, request, story_id):
        """Upload narration for many pages at once, matched by page number."""
        story = get_object_or_404(Story, pk=story_id)
        if not (
            self.has_change_permission(request, story)
            and request.user.has_perm("core.change_paragraph")
        ):
            raise PermissionDenied
        return upload_page(
            self,
            request,
            {
                "title": f"Upload narration: {story.title}",
                "rules": [
                    "End each file name with its page number, in the order the pages "
                    "appear: page-01.mp3, 2.mp3 or Rona_moon_03.mp3 (after -, _, a "
                    "space or 'page').",
                    MP3_RULE,
                    "A page that already has narration gets the new file.",
                    UPLOAD_LIMIT,
                ],
                "back": reverse("admin:core_story_change", args=[story.pk]),
                "back_label": story.title,
                "save": lambda files: save_narration(story, files),
            },
        )

    def keep_unplayable_stories_in_draft(self, request, story):
        """Return a published story with problems to draft, and say why."""
        if story.status != Story.PUBLISHED:
            return
        problems = check_story(story).problems
        if problems:
            Story.objects.filter(pk=story.pk).update(status=Story.DRAFT)
            story.status = Story.DRAFT
            self.message_user(
                request,
                "Kept as a draft until these are fixed: " + " ".join(problems),
                level=messages.ERROR,
            )

    def completeness(self, obj):
        return check_story(obj).summary

    completeness.short_description = "Completeness"

    def completeness_report(self, obj):
        if not obj.pk:
            return "Save the story to check what it is missing."
        report = check_story(obj)
        if not report.problems and not report.warnings:
            return "Ready to publish: nothing is missing."
        items = [
            ("Problem (keeps the story in draft)", text) for text in report.problems
        ]
        items += [("Warning", text) for text in report.warnings]
        return format_html(
            "<ul style='margin:0; padding-left:1.2em'>{}</ul>",
            format_html_join("", "<li><strong>{}:</strong> {}</li>", items),
        )

    completeness_report.short_description = "Completeness"

    def apply_story_text(self, request, form, formsets):
        """Replace the pages with the whole-story text, if it changed."""
        pages = form.new_pages()
        if pages is None:
            return
        needed = ("add", "change", "delete")
        if not all(request.user.has_perm(f"core.{a}_paragraph") for a in needed):
            self.message_user(
                request,
                "The whole-story text was not applied: replacing pages needs "
                "permission to add, change and delete paragraphs.",
                level=messages.WARNING,
            )
            return
        if any(formset.has_changed() for formset in formsets):
            # The page forms were saved first; mapping narration by position
            # onto pages that just moved could attach it to the wrong page.
            self.message_user(
                request,
                "The whole-story text was not applied because pages were also "
                "edited below. The page edits were saved; apply the whole story "
                "in a separate save.",
                level=messages.WARNING,
            )
            return
        changed, removed = apply_pages(form.instance, pages)
        self.message_user(
            request, f"The story now has {len(pages)} pages.", level=messages.INFO
        )
        notes = []
        if changed:
            notes.append(
                "check the narration of pages "
                + ", ".join(map(str, changed))
                + ", whose text changed"
            )
        if removed:
            notes.append(
                "pages "
                + ", ".join(map(str, removed))
                + " had narration and were removed"
            )
        if notes:
            self.message_user(
                request, "Audio: " + "; ".join(notes) + ".", level=messages.WARNING
            )

    def preview_picture(self, obj):
        """Show thumbnail in list view"""
        if obj.story_picture and obj.story_picture.image_file:
            return format_html(
                '<img src="{}" style="max-width:50px; max-height:50px;" />',
                obj.story_picture.image_file.url,
            )
        return "-"

    preview_picture.short_description = "Preview"

    def picture_preview(self, obj):
        """Show full preview in edit form"""
        if obj.story_picture and obj.story_picture.image_file:
            return format_html(
                '<img src="{}" style="max-width:400px; max-height:300px; '
                'border:1px solid #ddd; padding:5px;" />',
                obj.story_picture.image_file.url,
            )
        return "No image selected"

    picture_preview.short_description = "Picture Preview"

    def music_preview(self, obj):
        """Show audio player"""
        if obj.background_music and obj.background_music.audio_file:
            file_url = obj.background_music.audio_file.url
            audio_type = audio_mime_type(file_url)
            return format_html(
                """
                <audio controls style="width:100%; max-width:400px;">
                    <source src="{}" type="{}">
                    Your browser does not support the audio element.
                </audio>
                """,
                file_url,
                audio_type,
            )
        return "No music selected"

    music_preview.short_description = "Music Preview"


@admin.register(AppConfig)
class AppConfigAdmin(admin.ModelAdmin):
    """
    Application Configuration - Global settings
    """

    list_display = ("__str__", "menu_bgm", "updated_at")
    readonly_fields = ("updated_at", "menu_bgm_preview")

    fieldsets = (
        ("Menu Settings", {"fields": ("menu_bgm", "menu_bgm_preview")}),
        ("System", {"fields": ("updated_at",)}),
    )

    def menu_bgm_preview(self, obj):
        """Show audio player for menu BGM"""
        if obj.menu_bgm and obj.menu_bgm.audio_file:
            file_url = obj.menu_bgm.audio_file.url
            # Detect audio type from file extension
            audio_type = audio_mime_type(file_url)
            return format_html(
                """
                <audio controls style="width:100%; max-width:400px;">
                    <source src="{}" type="{}">
                    Your browser does not support the audio element.
                </audio>
                <p><strong>Selected:</strong> {}</p>
                """,
                file_url,
                audio_type,
                obj.menu_bgm.title,
            )
        return "No menu music selected"

    menu_bgm_preview.short_description = "Menu BGM Preview"

    def has_add_permission(self, request):
        # Creating the singleton still requires the normal model permission.
        return super().has_add_permission(request) and not AppConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of the config
        return False


@admin.register(StoryPicture)
class StoryPictureAdmin(admin.ModelAdmin):
    list_display = ("title", "image_thumbnail")
    search_fields = ("title",)
    readonly_fields = ("image_preview",)

    fieldsets = ((None, {"fields": ("title", "image_file", "image_preview")}),)

    def image_thumbnail(self, obj):
        """Show small thumbnail in list"""
        if obj.image_file:
            return format_html(
                '<img src="{}" style="max-width:60px; max-height:60px;" />',
                obj.image_file.url,
            )
        return "-"

    image_thumbnail.short_description = "Preview"

    def image_preview(self, obj):
        """Show full preview in edit form"""
        if obj.image_file:
            return format_html(
                '<img src="{}" style="max-width:600px; max-height:400px; '
                'border:1px solid #ddd; padding:5px;" />',
                obj.image_file.url,
            )
        return "No image uploaded yet"

    image_preview.short_description = "Image Preview"


@admin.register(BackgroundMusic)
class BackgroundMusicAdmin(admin.ModelAdmin):
    """
    Background Music Library
    """

    list_display = ("title", "audio_file")
    search_fields = ("title",)
    readonly_fields = ("audio_preview",)

    fieldsets = ((None, {"fields": ("title", "audio_file", "audio_preview")}),)

    def audio_preview(self, obj):
        """Show audio player"""
        if obj.audio_file:
            file_url = obj.audio_file.url
            audio_type = audio_mime_type(file_url)
            return format_html(
                """
                <audio controls style="width:100%; max-width:500px;">
                    <source src="{}" type="{}">
                    Your browser does not support the audio element.
                </audio>
                <p><em>File: {}</em></p>
                """,
                file_url,
                audio_type,
                obj.audio_file.name.split("/")[-1],
            )
        return "No audio uploaded yet"

    audio_preview.short_description = "Audio Preview"


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")


class WordFormInline(admin.TabularInline):
    """The word's text and audio in each language."""

    model = WordForm
    extra = 1
    fields = ("language", "text", "audio", "audio_preview")
    readonly_fields = ("audio_preview",)

    def audio_preview(self, obj):
        return audio_player(obj.audio) or "-"

    audio_preview.short_description = "Listen"


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    """
    Manage word entries (Word Bank)
    """

    change_list_template = "admin/core/word/change_list.html"
    list_display = ("key", "forms_summary", "has_image", "has_audio")
    search_fields = ("key", "forms__text")
    readonly_fields = ("image_preview",)
    inlines = [WordFormInline]

    fieldsets = (
        (None, {"fields": ("key",)}),
        ("Image", {"fields": ("image", "image_preview")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("forms__language")

    def get_urls(self):
        upload = path(
            "upload/",
            self.admin_site.admin_view(self.upload_view),
            name="core_word_upload",
        )
        return [upload] + super().get_urls()

    def upload_view(self, request):
        """Upload pictures and audio for many words at once, matched by name."""
        if not (
            self.has_change_permission(request)
            and request.user.has_perm("core.change_wordform")
        ):
            raise PermissionDenied
        return upload_page(
            self,
            request,
            {
                "title": "Upload word files",
                "rules": [
                    "Name a picture by the word's key: moon.jpg (or .png, .webp).",
                    "Name audio by key and language code: moon.mi.mp3, moon.en.mp3. "
                    "The word needs a form in that language first.",
                    MP3_RULE,
                    "A word that already has the picture or audio gets the new file.",
                    UPLOAD_LIMIT,
                ],
                "back": reverse("admin:core_word_changelist"),
                "back_label": "Word Bank",
                "save": save_word_files,
            },
        )

    def forms_summary(self, obj):
        return ", ".join(
            f"{form.language.code}: {form.text}" for form in obj.forms.all()
        )

    forms_summary.short_description = "Forms"

    def has_image(self, obj):
        return "✓" if obj.image else "-"

    has_image.short_description = "Image"

    def has_audio(self, obj):
        return "✓" if any(form.audio for form in obj.forms.all()) else "-"

    has_audio.short_description = "Audio"

    def image_preview(self, obj):
        """Show image preview"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:300px; max-height:300px; '
                'border:1px solid #ddd; padding:5px;" />',
                obj.image.url,
            )
        return "No image uploaded yet"

    image_preview.short_description = "Image Preview"


@admin.register(BlankLink)
class BlankLinkAdmin(admin.ModelAdmin):
    """
    Manage links between Placeholder and Word Bank
    """

    form = BlankLinkForm
    list_display = ("paragraph", "placeholder", "word")
    list_filter = ("paragraph__story__title",)
    autocomplete_fields = ("word",)
    readonly_fields = ("display_paragraph_text",)

    fieldsets = (
        (
            None,
            {"fields": ("paragraph", "display_paragraph_text", "placeholder", "word")},
        ),
    )

    def display_paragraph_text(self, obj):
        if obj.paragraph:
            return format_html("<pre>{}</pre>", obj.paragraph.text)
        return "N/A (Please select a paragraph first)"

    display_paragraph_text.short_description = "Paragraph Text Preview"
