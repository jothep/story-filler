# core/models.py
# Define all data models for the application, including Story, Paragraph, Word,
# and all relationships between them (such as BlankLink).
import logging
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
from django.core.validators import FileExtensionValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.db import models

logger = logging.getLogger(__name__)


# ===== File Validators =====


def validate_image_file_size(file):
    """Validate image file size (max 10MB)."""
    max_size_mb = 10
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(
            f"Image file size cannot exceed {max_size_mb}MB. "
            f"Current size: {file.size / 1024 / 1024:.2f}MB"
        )


def validate_audio_file_size(file):
    """Validate audio file size (max 20MB)."""
    max_size_mb = 20
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(
            f"Audio file size cannot exceed {max_size_mb}MB. "
            f"Current size: {file.size / 1024 / 1024:.2f}MB"
        )


AUDIO_EXTENSIONS = ["mp3", "m4a", "aac", "wav", "ogg"]

# Word keys appear in placeholders such as __BLANK_moon__, which the game
# parser matches with [A-Za-z0-9_]+. Keys are already in the normalised form
# that blank matching uses (no leading, trailing or repeated underscores), and
# at most 40 characters, so the placeholder fits BlankLink.placeholder (50).
WORD_KEY_LENGTH = 40
WORD_KEY_VALIDATOR = RegexValidator(
    r"^[a-z0-9]+(_[a-z0-9]+)*$",
    "Use lowercase letters and digits, with single underscores between them.",
)
LANGUAGE_CODE_VALIDATOR = RegexValidator(
    r"^[a-z]{2,3}(-[A-Za-z0-9]{2,8})*$",
    "Use a language code such as en, mi or zh-Hans.",
)


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
        if img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = background

        # Resize if needed
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        # Save to BytesIO
        output = BytesIO()
        img.save(output, format="JPEG", quality=quality, optimize=True)
        output.seek(0)

        # Get original filename and change extension to .jpg
        original_name = image_file.name
        name_without_ext = ".".join(original_name.split(".")[:-1])
        new_name = f"{name_without_ext}.jpg"

        logger.info(
            f"Compressed image: {original_name} -> {new_name} (quality={quality})"
        )

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
        "BackgroundMusic",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Menu Background Music",
        help_text="Select background music for the main menu",
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
            raise ValidationError("Only one Application Configuration can exist.")
        return super().save(*args, **kwargs)


class BackgroundMusic(models.Model):
    title = models.CharField(
        max_length=200, verbose_name="BGM Title", help_text="Name of a BGM"
    )
    audio_file = models.FileField(
        upload_to="bgm/",
        verbose_name="BGM file (.m4a, .mp3)",
        validators=[
            FileExtensionValidator(["mp3", "m4a", "aac", "wav", "ogg"]),
            validate_audio_file_size,
        ],
    )

    class Meta:
        verbose_name = "Background Music"
        verbose_name_plural = "Background Music Library"

    def __str__(self):
        return self.title


class StoryPicture(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name="Picture Title",
        help_text="A recognizable name for this picture",
    )
    image_file = models.ImageField(
        upload_to="story_pictures/",
        verbose_name="Picture file",
        validators=[
            FileExtensionValidator(["jpg", "jpeg", "png", "webp"]),
            validate_image_file_size,
        ],
    )

    class Meta:
        verbose_name = "Story Picture"
        verbose_name_plural = "Story Picture Library"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """Override save to compress images automatically."""
        skip_compression = kwargs.pop("skip_compression", False)
        if self.image_file and not skip_compression:
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


class Language(models.Model):
    """A language that stories are written in or teach."""

    code = models.CharField(
        max_length=35,
        unique=True,
        validators=[LANGUAGE_CODE_VALIDATOR],
        help_text="Language code, such as en, mi or zh-Hans",
    )
    name = models.CharField(
        max_length=100, help_text="Name shown to players, such as Māori or 中文"
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Story(models.Model):
    DRAFT = "draft"
    PUBLISHED = "published"
    STATUS_CHOICES = [(DRAFT, "Draft"), (PUBLISHED, "Published")]

    title = models.CharField(max_length=200, verbose_name="Title")
    # The database default lets the previous release keep creating stories
    # between the migration and this release.
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=DRAFT,
        db_default=DRAFT,
        help_text="Only published stories are shown to players. A story with "
        "problems that break play stays a draft.",
    )
    # Nullable in the database until the old word columns are removed, so the
    # previous release can still create stories; the admin requires both.
    language = models.ForeignKey(
        Language,
        on_delete=models.PROTECT,
        null=True,
        blank=False,
        related_name="stories_written_in",
        verbose_name="Story language",
        help_text="The language the story is written in",
    )
    learning_language = models.ForeignKey(
        Language,
        on_delete=models.PROTECT,
        null=True,
        blank=False,
        related_name="stories_teaching",
        verbose_name="Learning language",
        help_text="The language of the words players fill in",
    )
    background_music = models.ForeignKey(
        BackgroundMusic,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Background Music",
    )

    story_picture = models.ForeignKey(
        StoryPicture,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Story Picture",
    )

    def __str__(self):
        return self.title


class Paragraph(models.Model):
    story = models.ForeignKey(
        Story,
        related_name="paragraphs",
        on_delete=models.CASCADE,
        verbose_name="Belonging Story",
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Paragraph Order")
    text = models.TextField(
        verbose_name="Paragraph Text"
    )  # Paragraph like __BLANK_water__
    audio = models.FileField(
        upload_to="paragraph_audio/",
        blank=True,
        null=True,
        verbose_name="Paragraph Audio",
        validators=[
            FileExtensionValidator(["mp3", "m4a", "aac", "wav", "ogg"]),
            validate_audio_file_size,
        ],
    )

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.story.title} - Paragraph {self.order}"


class Word(models.Model):
    """A word entry: one meaning, with an image shared by every language.

    Its forms hold the text and audio in each language. The Māori and English
    columns are legacy: the 0011 migration copies them into forms, nothing
    reads or writes them afterwards, and a later release removes them.
    """

    # Nullable in the database until the legacy columns are removed, so the
    # previous release can still create words; the admin requires it.
    key = models.CharField(
        max_length=WORD_KEY_LENGTH,
        unique=True,
        null=True,
        blank=False,
        validators=[WORD_KEY_VALIDATOR],
        help_text="Used in blanks: the key moon matches __BLANK_moon__",
    )
    maori_word = models.CharField(
        max_length=100,
        verbose_name="Maori word (legacy)",
        unique=True,
        null=True,
        blank=True,
    )
    english_translation = models.CharField(
        max_length=100, verbose_name="English word (legacy)", blank=True, default=""
    )
    image = models.ImageField(
        upload_to="word_images/",
        blank=True,
        null=True,
        verbose_name="Word Image",
        validators=[
            FileExtensionValidator(["jpg", "jpeg", "png", "webp"]),
            validate_image_file_size,
        ],
    )
    maori_audio = models.FileField(
        upload_to="word_audio_maori/",
        blank=True,
        null=True,
        verbose_name="Maori Audio (legacy)",
        validators=[
            FileExtensionValidator(["mp3", "m4a", "aac", "wav", "ogg"]),
            validate_audio_file_size,
        ],
    )
    english_audio = models.FileField(
        upload_to="word_audio_english/",
        blank=True,
        null=True,
        verbose_name="English Audio (legacy)",
        validators=[
            FileExtensionValidator(["mp3", "m4a", "aac", "wav", "ogg"]),
            validate_audio_file_size,
        ],
    )

    class Meta:
        verbose_name = "Word (in Bank)"
        verbose_name_plural = "Word Bank"

    def __str__(self):
        return self.key or f"Word {self.pk}"

    def save(self, *args, **kwargs):
        """Override save to compress images automatically."""
        skip_compression = kwargs.pop("skip_compression", False)
        if self.image and not skip_compression:
            try:
                # Check if this is a new upload or changed file
                if not self.pk or self._state.adding:
                    # Use smaller size for word images
                    compressed_image, new_name = compress_image(
                        self.image, max_width=800, max_height=800, quality=80
                    )
                    self.image.save(new_name, compressed_image, save=False)
                    logger.info(f"Word image compressed: {new_name}")
            except Exception as e:
                logger.error(f"Failed to compress word image: {e}")
                # Continue saving even if compression fails
        super().save(*args, **kwargs)


class WordForm(models.Model):
    """How a word entry is written, and optionally spoken, in one language."""

    word = models.ForeignKey(Word, related_name="forms", on_delete=models.CASCADE)
    language = models.ForeignKey(
        Language, related_name="word_forms", on_delete=models.PROTECT
    )
    text = models.CharField(max_length=100)
    audio = models.FileField(
        upload_to="word_audio/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(AUDIO_EXTENSIONS),
            validate_audio_file_size,
        ],
    )

    class Meta:
        ordering = ["language__code"]
        constraints = [
            models.UniqueConstraint(
                fields=["word", "language"], name="unique_word_form_per_language"
            )
        ]

    def __str__(self):
        return f"{self.text} ({self.language.code})"


class BlankLink(models.Model):
    """Link Paragraph blanks and words in Word Bank"""

    paragraph = models.ForeignKey(
        Paragraph,
        related_name="blank_links",
        on_delete=models.CASCADE,
        verbose_name="Paragraph",
    )

    placeholder = models.CharField(
        max_length=50, verbose_name="Placeholder in Text (e.g., __BLANK_water__)"
    )

    word = models.ForeignKey(
        Word,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Linked Word from Bank",
    )

    class Meta:
        unique_together = ("paragraph", "placeholder")
        verbose_name = "Blank Link"
        verbose_name_plural = "Blank Links"

    def __str__(self):
        word_str = self.word.maori_word if self.word else "Not Linked"
        return f"{self.paragraph}: {self.placeholder} -> {word_str}"
