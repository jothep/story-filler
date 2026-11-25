# core/forms.py
# Provide custom forms for Django admin to enhance data validation.
import re

from django import forms
from django.core.exceptions import ValidationError

from .blanks import expand_inline_blanks
from .models import BlankLink, Paragraph


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
