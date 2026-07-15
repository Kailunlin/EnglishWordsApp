from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Vocabulary(models.Model):
    """
    單字庫模型
    儲存系統中所有的英文單字及其相關資訊。
    """
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
        auto_now_add=True,
        verbose_name="建立時間"
    )

    def __str__(self):
        """回傳單字的英文，方便在 Django Admin 或終端機中辨識"""
        return self.english
    
class WrongAnswer(models.Model):
    """
    答錯紀錄模型
    記錄使用者在測驗中答錯的單字與他們當時輸入的錯誤答案。
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="使用者")
    word = models.ForeignKey(Vocabulary, on_delete=models.CASCADE, verbose_name="答錯的單字")
    user_answer = models.CharField(max_length=100, verbose_name="使用者輸入的答案")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="答錯時間")

    def __str__(self):
        return self.word.english

class FavoriteWord(models.Model):
    """
    最愛單字模型
    記錄使用者加入收藏（最愛）的單字。
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites', verbose_name="使用者")
    word = models.ForeignKey(Vocabulary, on_delete=models.CASCADE, related_name='favorited_by', verbose_name="收藏的單字")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="收藏時間")

    class Meta:
        # 確保同一個使用者不會重複收藏同一個單字
        unique_together = ('user', 'word')
        # 預設排序為最新收藏的排在最前面
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.word.english}"

class UserLearningProfile(models.Model):
    """
    使用者學習檔案模型
    記錄使用者的學習目標、連續登入天數等個人化學習數據。
    與 User 模型是一對一的關係。
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='learning_profile', verbose_name="使用者")
    streak_days = models.IntegerField(default=0, verbose_name="連續登入/學習天數")
    last_activity_date = models.DateField(null=True, blank=True, verbose_name="最後活動日期")
    
    GOAL_CHOICES = [
        (5, '5 個單字'),
        (10, '10 個單字'),
        (15, '15 個單字'),
        (20, '20 個單字')
    ]
    daily_goal = models.IntegerField(default=20, choices=GOAL_CHOICES, verbose_name="每日學習目標")
    words_learned_today = models.IntegerField(default=0, verbose_name="今日已學習單字數")

    def __str__(self):
        return f"{self.user.username} Profile"

class WordProgress(models.Model):
    """
    單字學習進度模型（間隔重複法核心）
    記錄每個使用者對每個單字的熟悉程度、下次複習時間等。
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='word_progresses', verbose_name="使用者")
    word = models.ForeignKey(Vocabulary, on_delete=models.CASCADE, related_name='progresses', verbose_name="單字")
    next_review_date = models.DateTimeField(default=timezone.now, verbose_name="下次應複習時間")
    last_reviewed_date = models.DateTimeField(default=timezone.now, verbose_name="上次複習時間")
    interval = models.IntegerField(default=0, verbose_name="間隔等級 (Spaced Repetition Interval)") # 代表間隔重複的階段
    is_mastered = models.BooleanField(default=False, verbose_name="是否已精熟")
    
    class Meta:
        # 確保每個使用者對每個單字只會有一筆進度紀錄
        unique_together = ('user', 'word')

    def __str__(self):
        return f"{self.user.username} - {self.word.english}"


class SecurityQuestion(models.Model):
    """
    安全問題模型
    儲存使用者的安全問題與答案（用於忘記密碼時的驗證流程）。
    """
    QUESTION_CHOICES = [
        ('pet', '您第一隻寵物的名字是？'),
        ('school', '您就讀的第一所小學名稱是？'),
        ('city', '您出生的城市是？'),
        ('mother', '您母親的娘家姓氏是？'),
        ('friend', '您最好朋友的名字是？'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='security_question', verbose_name="使用者")
    question = models.CharField(max_length=20, choices=QUESTION_CHOICES, verbose_name='安全問題')
    # 使用 Django 密碼 hash 函式儲存答案，避免明文儲存增加安全性
    answer_hash = models.CharField(max_length=128, verbose_name='答案（雜湊）')

    def set_answer(self, raw_answer):
        """將答案字串去除前後空白並轉為小寫後，進行 hash 加密儲存"""
        from django.contrib.auth.hashers import make_password
        self.answer_hash = make_password(raw_answer.strip().lower())

    def check_answer(self, raw_answer):
        """驗證使用者輸入的答案是否與資料庫中的 hash 相符"""
        from django.contrib.auth.hashers import check_password
        return check_password(raw_answer.strip().lower(), self.answer_hash)

    def __str__(self):
        return f"{self.user.username} - {self.get_question_display()}"