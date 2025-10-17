# stories/models.py
from django.db import models

class Story(models.Model):
    title = models.CharField(max_length=200, verbose_name="Title")
    # Whole story and using {{BLANK}} for blank
    full_text = models.TextField(verbose_name="Contents")

    def __str__(self):
        return self.title

class Word(models.Model):
    # The story which the word belonging
    story = models.ForeignKey(Story, related_name='words', on_delete=models.CASCADE, verbose_name="Belonging story")
    maori_word = models.CharField(max_length=100, verbose_name="Maori word")
    english_translation = models.CharField(max_length=100, verbose_name="English word")
    # Can add path for images and audio
    # visual_cue = models.ImageField(upload_to='images/')
    # audio_file = models.FileField(upload_to='audio/')

    def __str__(self):
        return self.maori_word