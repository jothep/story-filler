# core/forms.py
# Provide custom forms for Django admin to enhance data validation.
from django import forms
from django.core.exceptions import ValidationError
import re 
from .models import BlankLink, Paragraph 

class BlankLinkForm(forms.ModelForm):
    class Meta:
        model = BlankLink
        fields = '__all__' 

    def clean_placeholder(self):
        """
        自定义验证逻辑，检查 placeholder 是否在 paragraph.text 中。
        """
        placeholder = self.cleaned_data.get('placeholder')
        paragraph = self.cleaned_data.get('paragraph')

        if paragraph and placeholder:

            if not re.search(re.escape(placeholder), paragraph.text):
                raise ValidationError(
                    f"Placeholder '{placeholder}' was not found in the selected paragraph's text. "
                    f"Please ensure it exactly matches a placeholder (like __BLANK_name__) in the text below."
                )


        return placeholder 