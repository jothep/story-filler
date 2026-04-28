# core/models.py
# Define all data models for the application, including Story, Paragraph, Word,
# and all relationships between them (such as BlankLink).
import logging
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.db import models

logger = logging.getLogger(__name__)


# ===== File Validators =====

def validate_image_file_size(file):
    """Validate image file size (max 10MB)."""
    max_size_mb = 10
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f'Image file size cannot exceed {max_size_mb}MB. Current size: {file.size / 1024 / 1024:.2f}MB')


def validate_audio_file_size(file):
    """Validate audio file size (max 20MB)."""
    max_size_mb = 20
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f'Audio file size cannot exceed {max_size_mb}MB. Current size: {file.size / 1024 / 1024:.2f}MB')


# ===== Helper Functions =====

def compress_image(image_file, max_width=1920, max_height=1080, quality=85):
    """
    Compress and optimize image file.

    Args:
        image_file: Django UploadedFile or ImageField
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels
        quality: JPEG quality (1-100)

    Returns:
        ContentFile with compressed image
    """
    try:
        # Open image
        img = Image.open(image_file)

        # Convert RGBA to RGB (for PNG with transparency)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background

        # Resize if needed
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        # Save to BytesIO
        output = BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)

        # Get original filename and change extension to .jpg
        original_name = image_file.name
        name_without_ext = '.'.join(original_name.split('.')[:-1])
        new_name = f"{name_without_ext}.jpg"

        logger.info(f"Compressed image: {original_name} -> {new_name} (quality={quality})")

        return ContentFile(output.read()), new_name

    except Exception as e:
        logger.error(f"Failed to compress image {image_file.name}: {e}")
        raise ValidationError(f"Failed to process image: {str(e)}")


# ===== Models =====

class AppConfig(models.Model):
    """
    Global application configuration.
    Currently only stores menu background music.
    """
    menu_bgm = models.ForeignKey(
        'BackgroundMusic',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Menu Background Music",
        help_text="Select background music for the main menu"
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Last Updated")

    class Meta:
        verbose_name = "Application Configuration"
        verbose_name_plural = "Application Configuration"

    def __str__(self):
        return f"App Config (Last updated: {self.updated_at.strftime('%Y-%m-%d')})"

    def save(self, *args, **kwargs):
        # Ensure only one config instance exists
        if not self.pk and AppConfig.objects.exists():
            raise ValidationError('Only one Application Configuration can exist.')
        return super().save(*args, **kwargs)


class BackgroundMusic(models.Model):
    title = models.CharField(max_length=200, verbose_name="BGM Title", help_text="Name of a BGM")
    audio_file = models.FileField(
        upload_to="bgm/",
        verbose_name="BGM file (.m4a, .mp3)",
        validators=[
            FileExtensionValidator(['mp3', 'm4a', 'aac', 'wav', 'ogg']),
            validate_audio_file_size
        ]
    )

    class Meta:
        verbose_name = "Background Music"
        verbose_name_plural = "Background Music Library"

    def __str__(self):
        return self.title


class StoryPicture(models.Model):
    title = models.CharField(max_length=200, verbose_name="Picture Title", help_text="A recognizable name for this picture")
    image_file = models.ImageField(
        upload_to="story_pictures/",
        verbose_name="Picture file",
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_image_file_size
        ]
    )

    class Meta:
        verbose_name = "Story Picture"
        verbose_name_plural = "Story Picture Library"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """Override save to compress images automatically."""
        if self.image_file and not kwargs.pop('skip_compression', False):
            try:
                # Check if this is a new upload or changed file
                if not self.pk or self._state.adding:
                    compressed_image, new_name = compress_image(self.image_file)
                    self.image_file.save(new_name, compressed_image, save=False)
                    logger.info(f"Story picture compressed: {new_name}")
            except Exception as e:
                logger.error(f"Failed to compress story picture: {e}")
                # Continue saving even if compression fails
        super().save(*args, **kwargs)


class Story(models.Model):
    title = models.CharField(max_length=200, verbose_name="Title")
    background_music = models.ForeignKey(
        BackgroundMusic,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Background Music"
    )

    story_picture = models.ForeignKey(
        StoryPicture,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Story Picture"
    )

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
    text = models.TextField(verbose_name="Paragraph Text")  # Paragraph like __BLANK_water__
    audio = models.FileField(
        upload_to="paragraph_audio/",
        blank=True,
        null=True,
        verbose_name="Paragraph Audio",
        validators=[
            FileExtensionValidator(['mp3', 'm4a', 'aac', 'wav', 'ogg']),
            validate_audio_file_size
        ]
    )

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.story.title} - Paragraph {self.order}"


class Word(models.Model):
    """Word Bank"""

    maori_word = models.CharField(max_length=100, verbose_name="Maori word", unique=True)
    english_translation = models.CharField(max_length=100, verbose_name="English word")
    image = models.ImageField(
        upload_to="word_images/",
        blank=True,
        null=True,
        verbose_name="Word Image",
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_image_file_size
        ]
    )
    maori_audio = models.FileField(
        upload_to="word_audio_maori/",
        blank=True,
        null=True,
        verbose_name="Maori Audio",
        validators=[
            FileExtensionValidator(['mp3', 'm4a', 'aac', 'wav', 'ogg']),
            validate_audio_file_size
        ]
    )
    english_audio = models.FileField(
        upload_to="word_audio_english/",
        blank=True,
        null=True,
        verbose_name="English Audio",
        validators=[
            FileExtensionValidator(['mp3', 'm4a', 'aac', 'wav', 'ogg']),
            validate_audio_file_size
        ]
    )

    class Meta:
        verbose_name = "Word (in Bank)"
        verbose_name_plural = "Word Bank"

    def __str__(self):
        return f"{self.maori_word} ({self.english_translation})"

    def save(self, *args, **kwargs):
        """Override save to compress images automatically."""
        if self.image and not kwargs.pop('skip_compression', False):
            try:
                # Check if this is a new upload or changed file
                if not self.pk or self._state.adding:
                    # Use smaller size for word images
                    compressed_image, new_name = compress_image(
                        self.image,
                        max_width=800,
                        max_height=800,
                        quality=80
                    )
                    self.image.save(new_name, compressed_image, save=False)
                    logger.info(f"Word image compressed: {new_name}")
            except Exception as e:
                logger.error(f"Failed to compress word image: {e}")
                # Continue saving even if compression fails
        super().save(*args, **kwargs)


class BlankLink(models.Model):
    """Link Paragraph blanks and words in Word Bank"""

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
