from django import forms
from .models import SecurityQuestion


class SecurityQuestionSetupForm(forms.Form):
    """注册时设定安全问题的表单"""
    question = forms.ChoiceField(
        choices=SecurityQuestion.QUESTION_CHOICES,
        label='安全問題',
        widget=forms.Select(attrs={'class': 'form-select rounded-4 border-0 shadow-sm py-2'})
    )
    answer = forms.CharField(
        label='您的答案',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control rounded-4 shadow-sm border-0 py-2',
            'placeholder': '請輸入答案（不區分大小寫）',
            'autocomplete': 'off',
        })
    )

    def clean_answer(self):
        answer = self.cleaned_data.get('answer', '').strip()
        if len(answer) < 2:
            raise forms.ValidationError('答案至少需要 2 個字元。')
        return answer


class ForgotPasswordStep1Form(forms.Form):
    """忘記密碼 - 第一步：輸入帳號"""
    username = forms.CharField(
        label='帳號',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control rounded-4 shadow-sm border-0 py-2',
            'placeholder': '請輸入您的帳號',
            'autofocus': True,
        })
    )


class SecurityAnswerForm(forms.Form):
    """忘記密碼 - 第二步：回答安全問題"""
    answer = forms.CharField(
        label='您的答案',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control rounded-4 shadow-sm border-0 py-2',
            'placeholder': '請輸入您當初設定的答案',
            'autocomplete': 'off',
        })
    )


class ResetPasswordForm(forms.Form):
    """忘記密碼 - 第三步：設定新密碼"""
    new_password1 = forms.CharField(
        label='新密碼',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control rounded-4 shadow-sm border-0 py-2',
            'placeholder': '請輸入新密碼（至少 8 個字元）',
        })
    )
    new_password2 = forms.CharField(
        label='確認新密碼',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control rounded-4 shadow-sm border-0 py-2',
            'placeholder': '請再次輸入新密碼',
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password1', '')
        p2 = cleaned_data.get('new_password2', '')

        if p1 and len(p1) < 8:
            raise forms.ValidationError('密碼長度至少需要 8 個字元。')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('兩次輸入的密碼不一致，請重新確認。')
        return cleaned_data
