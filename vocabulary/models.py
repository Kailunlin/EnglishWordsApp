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

    DIFFICULTY_CHOICES = [
        ('easy', '簡單 (Easy)'),
        ('medium', '中等 (Medium)'),
        ('hard', '困難 (Hard)'),
    ]
    difficulty = models.CharField(
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default='medium',
        verbose_name="難度"
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


class SecurityQuestion(models.Model):
    """儲存使用者的安全問題與答案（用於忘記密碼流程）"""
    QUESTION_CHOICES = [
        ('pet', '您第一隻寵物的名字是？'),
        ('school', '您就讀的第一所小學名稱是？'),
        ('city', '您出生的城市是？'),
        ('mother', '您母親的娘家姓氏是？'),
        ('friend', '您最好朋友的名字是？'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='security_question')
    question = models.CharField(max_length=20, choices=QUESTION_CHOICES, verbose_name='安全問題')
    # 使用 Django 密碼 hash 函式儲存答案，增加安全性
    answer_hash = models.CharField(max_length=128, verbose_name='答案（雜湊）')

    def set_answer(self, raw_answer):
        """將答案轉為小寫後進行 hash 儲存"""
        from django.contrib.auth.hashers import make_password
        self.answer_hash = make_password(raw_answer.strip().lower())

    def check_answer(self, raw_answer):
        """驗證答案是否正確"""
        from django.contrib.auth.hashers import check_password
        return check_password(raw_answer.strip().lower(), self.answer_hash)

    def __str__(self):
        return f"{self.user.username} - {self.get_question_display()}"