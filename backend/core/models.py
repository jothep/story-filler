from django.db import models


class Story(models.Model):
    title = models.CharField(max_length=200, verbose_name="Title")
    full_text = models.TextField(verbose_name="Contents")

    def __str__(self):
        return self.title


class Word(models.Model):
    story = models.ForeignKey(
        Story,
        related_name="words",
        on_delete=models.CASCADE,
        verbose_name="Belonging story",
    )
    maori_word = models.CharField(max_length=100, verbose_name="Maori word")
    english_translation = models.CharField(max_length=100, verbose_name="English word")

    def __str__(self):
        return self.maori_word
