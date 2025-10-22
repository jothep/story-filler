from django.db import models

class BackgroundMusic(models.Model):
    """
    BGM management
    """
    title = models.CharField(max_length=200, verbose_name="BGM Title", help_text="BGM Title")
    audio_file = models.FileField(
        upload_to="bgm/", 
        verbose_name="BGM audio file (.m4a)"
    )

    class Meta:
        verbose_name = "Background Music"
        verbose_name_plural = "Background Music Library" 

    def __str__(self):
        return self.title
class Story(models.Model):
    title = models.CharField(max_length=200, verbose_name="Title")
    background_music = models.ForeignKey(
        BackgroundMusic,
        on_delete=models.SET_NULL, 
        blank=True,
        null=True,
        verbose_name="Background Music"
    )
    def __str__(self):
        return self.title

class Paragraph(models.Model):
    """
    Paragraph of a story
    """
    story = models.ForeignKey(
        Story,
        related_name="paragraphs",
        on_delete=models.CASCADE,
        verbose_name="Belonging Story",
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Paragraph Order")
    text = models.TextField(verbose_name="Paragraph Text")

    audio = models.FileField(
        upload_to="paragraph_audio/",
        blank=True,
        null=True,
        verbose_name="Paragraph Audio"
    )

    class Meta:
        ordering = ['order'] 

    def __str__(self):
        return f"{self.story.title} - Paragraph {self.order}"

class Word(models.Model):
    paragraph = models.ForeignKey(
        Paragraph,
        related_name="words",
        on_delete=models.CASCADE,
        verbose_name="Belonging Paragraph",
        null=True
    )
    maori_word = models.CharField(max_length=100, verbose_name="Maori word")
    english_translation = models.CharField(max_length=100, verbose_name="English word")

    image = models.ImageField(
        upload_to="word_images/",
        blank=True,
        null=True,
        verbose_name="Word Image"
    )
    maori_audio = models.FileField(
        upload_to="word_audio_maori/",
        blank=True,
        null=True,
        verbose_name="Maori Audio"
    )
    english_audio = models.FileField(
        upload_to="word_audio_english/",
        blank=True,
        null=True,
        verbose_name="English Audio"
    )

    # Placeholder like "__BLANK_1__", "__BLANK_ika__"
    placeholder = models.CharField(
        max_length=50,
        unique=True, 
        blank=True,
        null=True,
        verbose_name="Placeholder in Text (e.g., __BLANK_1__)"
    )

    def __str__(self):
        return self.maori_word
