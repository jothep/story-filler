# core/models.py
from django.db import models

class BackgroundMusic(models.Model):
    title = models.CharField(max_length=200, verbose_name="BGM Title", help_text="Name of a BGM")
    audio_file = models.FileField(upload_to="bgm/", verbose_name="BGM file (.m4a)")
    class Meta: verbose_name = "Background Music"; verbose_name_plural = "Background Music Library"
    def __str__(self): return self.title

class Story(models.Model):
    title = models.CharField(max_length=200, verbose_name="Title")
    background_music = models.ForeignKey(BackgroundMusic, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Background Music")

    word_bank = models.ManyToManyField(
        'Word', 
        blank=True, 
        related_name="stories", 
        verbose_name="Select Words for this Story's Bank"
    )

    def __str__(self):
        return self.title

class Paragraph(models.Model):
    story = models.ForeignKey(Story, related_name="paragraphs", on_delete=models.CASCADE, verbose_name="Belonging Story")
    order = models.PositiveIntegerField(default=0, verbose_name="Paragraph Order")
    text = models.TextField(verbose_name="Paragraph Text") # Paragraph like __BLANK_water__
    audio = models.FileField(upload_to="paragraph_audio/", blank=True, null=True, verbose_name="Paragraph Audio")
    class Meta: ordering = ['order']
    def __str__(self): return f"{self.story.title} - Paragraph {self.order}"

class Word(models.Model):
    """
    Word Bank
    """

    maori_word = models.CharField(max_length=100, verbose_name="Maori word", unique=True) 
    english_translation = models.CharField(max_length=100, verbose_name="English word")
    image = models.ImageField(upload_to="word_images/", blank=True, null=True, verbose_name="Word Image")
    maori_audio = models.FileField(upload_to="word_audio_maori/", blank=True, null=True, verbose_name="Maori Audio")
    english_audio = models.FileField(upload_to="word_audio_english/", blank=True, null=True, verbose_name="English Audio")

    class Meta:
        verbose_name = "Word (in Bank)"
        verbose_name_plural = "Word Bank"

    def __str__(self):
        return f"{self.maori_word} ({self.english_translation})"
class BlankLink(models.Model):
    """
    Link Paragraph blanks and words in Word Bank
    """
    paragraph = models.ForeignKey(
        Paragraph,
        related_name="blank_links",
        on_delete=models.CASCADE,
        verbose_name="Paragraph"
    )

    placeholder = models.CharField(
        max_length=50,
        verbose_name="Placeholder in Text (e.g., __BLANK_water__)"
    )

    word = models.ForeignKey(
        Word,
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True,  
        verbose_name="Linked Word from Bank"
    )

    class Meta:
        unique_together = ('paragraph', 'placeholder') 
        verbose_name = "Blank Link"
        verbose_name_plural = "Blank Links"

    def __str__(self):
        word_str = self.word.maori_word if self.word else "Not Linked"
        return f"{self.paragraph}: {self.placeholder} -> {word_str}"
