# core/forms.py
# Provide custom forms for Django admin to enhance data validation.
import re

from django import forms
from django.core.exceptions import ValidationError

from .blanks import expand_inline_blanks
from .models import BlankLink, Paragraph, Story
from .pages import PAGE_LENGTH, split_pages, story_text


class StoryAdminForm(forms.ModelForm):
    """A story, with its pages editable as one text."""

    story_text = forms.CharField(
        label="Whole story",
        required=False,
        widget=forms.Textarea(attrs={"rows": 16, "style": "width: 95%"}),
        help_text=(
            "Paste or edit the whole story. A blank line starts a new page, and a "
            f"page longer than {PAGE_LENGTH} characters is split at sentence ends. "
            "Write blanks as {{key}}. Saving a change here replaces the pages "
            "below; each page keeps the narration at its position. Leaving the "
            "box empty changes nothing."
        ),
    )

    class Meta:
        model = Story
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.story_text_initial = story_text(self.instance) if self.instance.pk else ""
        self.fields["story_text"].initial = self.story_text_initial

    def clean_story_text(self):
        text = (self.cleaned_data.get("story_text") or "").replace("\r\n", "\n")
        try:
            expand_inline_blanks(text)
        except ValueError as error:
            raise ValidationError(str(error)) from error
        return text

    def new_pages(self):
        """Return the pages from the whole-story text, or None if unchanged."""
        text = self.cleaned_data.get("story_text", "")
        if not text.strip() or text.strip() == self.story_text_initial.strip():
            return None
        return split_pages(expand_inline_blanks(text))


class ParagraphForm(forms.ModelForm):
    """A story page. Blanks can be written as {{key}}."""

    class Meta:
        model = Paragraph
        fields = ("order", "text", "audio")
        help_texts = {
            "text": "Write each blank as {{key}}, for example {{moon}}. Saving "
            "stores it as __BLANK_moon__ and links it to the word with that key."
        }

    def clean_text(self):
        try:
            return expand_inline_blanks(self.cleaned_data.get("text"))
        except ValueError as error:
            raise ValidationError(str(error)) from error


class BlankLinkForm(forms.ModelForm):
    class Meta:
        model = BlankLink
        fields = "__all__"

    def clean_placeholder(self):
        """
        自定义验证逻辑，检查 placeholder 是否在 paragraph.text 中。
        """
        placeholder = self.cleaned_data.get("placeholder")
        paragraph = self.cleaned_data.get("paragraph")

        if paragraph and placeholder:

            if not re.search(re.escape(placeholder), paragraph.text):
                raise ValidationError(
                    f"Placeholder '{placeholder}' was not found in the selected "
                    "paragraph's text. Please ensure it exactly matches a "
                    "placeholder (like __BLANK_name__) in the text below."
                )

        return placeholder
