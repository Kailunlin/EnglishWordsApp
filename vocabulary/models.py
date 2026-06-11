from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Vocabulary(models.Model):
    english = models.CharField(
        max_length=100,
        verbose_name="英文單字"
    )

    chinese = models.CharField(
        max_length=100,
        verbose_name="中文意思"
    )

    part_of_speech = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="詞性"
    )

    example = models.TextField(
        blank=True,
        verbose_name="例句"
    )

    example_translation = models.TextField(
        blank=True,
        verbose_name="例句翻譯"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.english
    
class WrongAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    word = models.ForeignKey(Vocabulary, on_delete=models.CASCADE)
    user_answer = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.word.english

class FavoriteWord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    word = models.ForeignKey(Vocabulary, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'word')
        ordering = ['-created_at']
    def __str__(self):
        return f"{self.user.username} - {self.word.english}"

class UserLearningProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='learning_profile')
    streak_days = models.IntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)
    
    GOAL_CHOICES = [
        (5, '5 個單字'),
        (10, '10 個單字'),
        (15, '15 個單字'),
        (20, '20 個單字')
    ]
    daily_goal = models.IntegerField(default=20, choices=GOAL_CHOICES)
    words_learned_today = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} Profile"

class WordProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='word_progresses')
    word = models.ForeignKey(Vocabulary, on_delete=models.CASCADE, related_name='progresses')
    next_review_date = models.DateTimeField(default=timezone.now)
    interval = models.IntegerField(default=0) # Represents spaced repetition interval
    is_mastered = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('user', 'word')

    def __str__(self):
        return f"{self.user.username} - {self.word.english}"