import random
import json
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from .models import Vocabulary, WrongAnswer, FavoriteWord, UserLearningProfile, WordProgress, SecurityQuestion
from .forms import SecurityQuestionSetupForm, ForgotPasswordStep1Form, SecurityAnswerForm, ResetPasswordForm

from django.core.paginator import Paginator
from django.db.models import Q

def register_view(request):
    """用戶註冊視圖（含安全問題設定）"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        sq_form = SecurityQuestionSetupForm(request.POST)
        if form.is_valid() and sq_form.is_valid():
            # 建立新用戶
            user = form.save()
            # 儲存安全問題與答案
            sq = SecurityQuestion(user=user, question=sq_form.cleaned_data['question'])
            sq.set_answer(sq_form.cleaned_data['answer'])
            sq.save()
            # 自動登入並跳轉
            login(request, user)
            return redirect('word_list')
    else:
        form = UserCreationForm()
        sq_form = SecurityQuestionSetupForm()
    return render(request, 'vocabulary/register.html', {'form': form, 'sq_form': sq_form})

def login_view(request):
    """用戶登入視圖"""
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            # 驗證用戶並登入，重定向到返回頁面或單字列表
            user = form.get_user()
            login(request, user)
            return redirect(request.GET.get('next', 'word_list'))
    else:
        form = AuthenticationForm()
    return render(request, 'vocabulary/login.html', {'form': form})

def logout_view(request):
    """用戶登出視圖"""
    if request.method == 'POST':
        # 登出用戶並重定向到單字列表
        logout(request)
    return redirect('word_list')

def word_list(request):
    """單字列表視圖 - 顯示所有單字並支援搜尋、篩選和分頁"""
    query = request.GET.get('q', '')
    tab = request.GET.get('tab', 'all')  # all: 全部, learning: 學習中, unlearned: 未學習
    difficulty = request.GET.get('difficulty', 'all')
    
    words = Vocabulary.objects.all()

    if difficulty and difficulty != 'all':
        words = words.filter(difficulty=difficulty)

    # 根據搜尋關鍵字篩選（英文或中文）
    if query:
        words = words.filter(
            Q(english__icontains=query) | Q(chinese__icontains=query)
        )
        
    # 已登入用戶可使用標籤篩選
    if request.user.is_authenticated:
        if tab == 'learning':
            # 顯示用戶已開始學習的單字
            words = words.filter(progresses__user=request.user).distinct()
        elif tab == 'unlearned':
            # 顯示用戶尚未學習的單字
            words = words.exclude(progresses__user=request.user).distinct()

    words = words.order_by('english')

    # 分頁處理（每頁 25 個單字）
    paginator = Paginator(words, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 取得用戶的最愛單字 ID
    favorite_word_ids = set()
    if request.user.is_authenticated:
        favorite_word_ids = set(request.user.favorites.values_list('word_id', flat=True))

    return render(request, "vocabulary/word_list.html", {
        "page_obj": page_obj,
        "query": query,
        "tab": tab,
        "difficulty": difficulty,
        "favorite_word_ids": favorite_word_ids,
    })

@login_required
def quiz_start(request):
    """測驗開始視圖 - 初始化測驗並隨機選擇 10 個單字"""
    mode = request.GET.get('mode')
    
    if mode == 'wrong':
        all_words = list(WrongAnswer.objects.filter(user=request.user).values_list('word_id', flat=True).distinct())
        if not all_words:
            return render(request, "vocabulary/quiz_start.html", {"error": "錯題本目前沒有單字！", "mode": mode})
    else:
        difficulty = request.GET.get('difficulty', 'all')
        words_query = Vocabulary.objects.all()
        if difficulty and difficulty != 'all':
            words_query = words_query.filter(difficulty=difficulty)
            
        all_words = list(words_query.values_list('id', flat=True))
        if not all_words:
            return render(request, "vocabulary/quiz_start.html", {"error": "這個難度目前沒有單字！", "mode": mode, "difficulty": difficulty})
    
    # 隨機抽取最多 10 個單字
    sample_size = min(10, len(all_words))
    quiz_word_ids = random.sample(all_words, sample_size)
    
    # 初始化 session 中的測驗狀態
    request.session['quiz_word_ids'] = quiz_word_ids
    request.session['quiz_index'] = 0
    request.session['quiz_score'] = 0
    
    return render(request, "vocabulary/quiz_start.html", {
        "total_questions": sample_size,
        "mode": mode,
        "difficulty": request.GET.get('difficulty', 'all')
    })

@login_required
def quiz_question(request):
    """測驗問題視圖 - 顯示英文單字並提供 4 個中文選項（1 個正確 + 3 個混淆選項）"""
    quiz_word_ids = request.session.get('quiz_word_ids')
    quiz_index = request.session.get('quiz_index')
    
    # 檢查 session 狀態
    if quiz_word_ids is None or quiz_index is None:
        return redirect('quiz_start')
        
    # 檢查是否已完成所有題目
    if quiz_index >= len(quiz_word_ids):
        return redirect('quiz_result')
        
    # 取得目前題目的單字
    current_word_id = quiz_word_ids[quiz_index]
    word = Vocabulary.objects.get(id=current_word_id)
    
    # 取得 3 個不同的混淆選項（中文意思不同）
    other_words = list(Vocabulary.objects.exclude(chinese=word.chinese).values_list('chinese', flat=True).distinct())
    distractors = random.sample(other_words, min(3, len(other_words)))
    
    # 組合正確答案和混淆選項，並隨機排序
    options = distractors + [word.chinese]
    random.shuffle(options)
    
    # 將目前單字 ID 儲存到 session 以驗證答案
    request.session['current_word_id'] = current_word_id
    
    return render(request, "vocabulary/quiz_question.html", {
        "word": word,
        "options": options,
        "current_q": quiz_index + 1,
        "total_q": len(quiz_word_ids)
    })

@login_required
def quiz_answer(request):
    """測驗答案視圖 - 驗證用戶答案並顯示結果"""
    if request.method != "POST":
        return redirect('quiz_question')
        
    quiz_word_ids = request.session.get('quiz_word_ids')
    quiz_index = request.session.get('quiz_index')
    current_word_id = request.session.get('current_word_id')
    
    # 驗證題目索引是否匹配，防止答題順序錯誤
    submitted_q_index = request.POST.get("q_index")
    if submitted_q_index and submitted_q_index != str(quiz_index + 1):
        return redirect('quiz_question')
    
    if not current_word_id:
        return redirect('quiz_start')
        
    # 取得單字和用戶答案
    word = Vocabulary.objects.get(id=current_word_id)
    user_answer = request.POST.get("answer")
    
    # 檢查答案是否正確
    is_correct = (user_answer == word.chinese)
    
    # 計算正確答案數
    if is_correct:
        request.session['quiz_score'] = request.session.get('quiz_score', 0) + 1
    else:
        # 記錄錯誤答案用於後續複習
        WrongAnswer.objects.create(
            user=request.user,
            word=word,
            user_answer=user_answer or "未作答"
        )
        
        # 將答錯或不知道的單字加回測驗佇列的最後面
        quiz_word_ids.append(current_word_id)
        request.session['quiz_word_ids'] = quiz_word_ids
        
    # 移動到下一題
    request.session['quiz_index'] = quiz_index + 1
    
    # 檢查是否為最後一題
    is_last = (request.session['quiz_index'] >= len(quiz_word_ids))
    
    return render(request, "vocabulary/quiz_answer.html", {
        "word": word,
        "user_answer": user_answer,
        "is_correct": is_correct,
        "is_last": is_last,
    })

@login_required
def quiz_result(request):
    """測驗結果視圖 - 顯示測驗成績並清除 session 資料"""
    quiz_word_ids = request.session.get('quiz_word_ids', [])
    
    # 計算每個 word_id 出現的次數
    from collections import Counter
    id_counts = Counter(quiz_word_ids)
    unique_ids = list(id_counts.keys())
    
    # 取得對應的單字
    words_query = Vocabulary.objects.filter(id__in=unique_ids)
    
    tested_words = []
    for word_id in unique_ids:
        word_obj = next((w for w in words_query if w.id == word_id), None)
        if word_obj:
            tested_words.append({
                'word': word_obj,
                'is_wrong': id_counts[word_id] > 1
            })
            
    # 清除 session 中的測驗資料
    for key in ['quiz_word_ids', 'quiz_index', 'quiz_score', 'current_word_id']:
        if key in request.session:
            del request.session[key]
            
    return render(request, "vocabulary/quiz_result.html", {
        "tested_words": tested_words,
    })

@login_required
def wrong_list(request):
    """錯誤列表視圖 - 顯示用戶答錯的單字及其答案記錄（帶分頁）"""
    wrongs = WrongAnswer.objects.filter(user=request.user).order_by("-created_at")

    # 分頁處理（每頁 25 個錯誤記錄）
    paginator = Paginator(wrongs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "vocabulary/wrong_list.html", {
        "page_obj": page_obj
    })

@login_required
def toggle_favorite(request, word_id):
    """切換最愛視圖 - 使用 POST 請求新增或移除最愛單字（API）"""
    if request.method == "POST":
        word = get_object_or_404(Vocabulary, id=word_id)
        # 嘗試取得或建立最愛記錄
        favorite, created = FavoriteWord.objects.get_or_create(user=request.user, word=word)
        if not created:
            # 如果已存在，則移除該最愛
            favorite.delete()
            return JsonResponse({"status": "removed"})
        return JsonResponse({"status": "added"})
    return JsonResponse({"error": "Invalid request method"}, status=400)

@login_required
def favorite_list(request):
    """最愛列表視圖 - 顯示用戶收藏的單字並支援搜尋和分頁"""
    query = request.GET.get('q', '')
    # 取得該用戶的所有最愛單字，並關聯單字詳情
    favorites_qs = FavoriteWord.objects.filter(user=request.user).select_related('word')
    
    # 根據搜尋關鍵字篩選（英文或中文）
    if query:
        favorites_qs = favorites_qs.filter(
            Q(word__english__icontains=query) | Q(word__chinese__icontains=query)
        )
    
    # 分頁處理（每頁 25 個最愛單字）
    paginator = Paginator(favorites_qs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "vocabulary/favorite_list.html", {
        "page_obj": page_obj,
        "query": query,
    })

# === 儀表板與閃卡視圖 ===

@login_required
def dashboard_view(request):
    """儀表板視圖 - 顯示用戶的學習統計、連鎖日數、今日進度"""
    # 取得或建立用戶的學習檔案
    profile, created = UserLearningProfile.objects.get_or_create(user=request.user)
    
    today = timezone.localdate()
    # 如果今天還沒活動，檢查連鎖日數（如果超過 1 天沒活動則清零）
    if profile.last_activity_date != today:
        if profile.last_activity_date and profile.last_activity_date < today - timedelta(days=1):
            # 超過 1 天沒活動，連鎖日數重設為 0
            profile.streak_days = 0
        # 新的一天，重設今日學習數
        profile.words_learned_today = 0
        profile.save()

    # 計算待複習的單字數（根據間隔重複法）
    now = timezone.now()
    review_due_count = WordProgress.objects.filter(user=request.user, next_review_date__lte=now, is_mastered=False).count()

    # 計算今日進度百分比
    progress_percentage = min(100, int((profile.words_learned_today / profile.daily_goal) * 100)) if profile.daily_goal else 0

    context = {
        'profile': profile,
        'review_due_count': review_due_count,
        'progress_percentage': progress_percentage,
    }
    return render(request, "vocabulary/dashboard.html", context)

@login_required
@require_POST
def update_daily_goal_api(request):
    """更新每日目標 API - 接收 JSON 請求並更新用戶的每日學習目標"""
    try:
        data = json.loads(request.body)
        new_goal = int(data.get('goal', 20))
        # 只允許特定的目標值
        if new_goal in [5, 10, 15, 20]:
            profile, _ = UserLearningProfile.objects.get_or_create(user=request.user)
            profile.daily_goal = new_goal
            profile.save()
            return JsonResponse({'status': 'success', 'goal': new_goal})
    except Exception:
        pass
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def flashcard_study_view(request):
    """閃卡學習視圖 - 使用間隔重複法進行單字複習
    
    優先顯示：
    1. 待複習的單字（根據間隔重複法判定）
    2. 新單字（用戶尚未學習）
    最多顯示用戶的每日目標數量
    """
    # 取得用戶的學習檔案
    profile, _ = UserLearningProfile.objects.get_or_create(user=request.user)
    now = timezone.now()
    difficulty = request.GET.get('difficulty', 'all')
    
    # 取得所有待複習的單字
    due_progresses_qs = WordProgress.objects.filter(user=request.user, next_review_date__lte=now, is_mastered=False).select_related('word')
    if difficulty and difficulty != 'all':
        due_progresses_qs = due_progresses_qs.filter(word__difficulty=difficulty)
        
    due_progresses = list(due_progresses_qs)
    due_words = [p.word for p in due_progresses]
    
    # 如果待複習單字不足，補充新單字
    batch_size = profile.daily_goal  # 按用戶的每日目標補充
    if len(due_words) < batch_size:
        # 取得用戶已學習的單字 ID
        progress_word_ids = WordProgress.objects.filter(user=request.user).values_list('word_id', flat=True)
        # 取得新單字並補充到達目標數量
        new_words_qs = Vocabulary.objects.exclude(id__in=progress_word_ids)
        if difficulty and difficulty != 'all':
            new_words_qs = new_words_qs.filter(difficulty=difficulty)
            
        new_words = list(new_words_qs[:batch_size - len(due_words)])
        due_words.extend(new_words)

    # 隨機排列單字
    random.shuffle(due_words)

    # 將單字資料轉換為 JSON 格式
    words_data = []
    for w in due_words:
        words_data.append({
            'id': w.id,
            'english': w.english,
            'chinese': w.chinese,
            'part_of_speech': w.part_of_speech,
            'example': w.example,
            'example_translation': w.example_translation,
            'difficulty': w.difficulty,
        })
    
    return render(request, "vocabulary/flashcard.html", {'words_json': json.dumps(words_data)})

@login_required
@require_POST
def api_swipe_word(request):
    """滑動單字 API - 處理用戶在閃卡中的「記得」或「忘記」動作
    
    根據用戶的回應更新單字的學習進度（間隔重複法）：
    - 記得 (remembered): 增加複習間隔，延後下次複習時間
    - 忘記 (forgot): 重設間隔為 0，10 分鐘後需要複習
    同時更新用戶的學習檔案（今日學習數、連鎖日數）
    """
    try:
        data = json.loads(request.body)
        word_id = data.get('word_id')
        action = data.get('action')  # 'remembered' 或 'forgot'
        
        word = get_object_or_404(Vocabulary, id=word_id)
        # 取得或建立該單字的學習進度
        progress, created = WordProgress.objects.get_or_create(user=request.user, word=word)
        
        now = timezone.now()
        
        if action == 'remembered':
            # 用戶記得了，增加複習間隔
            progress.interval += 1
            # 定義間隔時間（日數）：[1, 3, 7, 14, 30]
            intervals = [1, 3, 7, 14, 30]
            days_to_add = intervals[min(progress.interval - 1, len(intervals) - 1)]
            progress.next_review_date = now + timedelta(days=days_to_add)
            # 達到 5 次複習則標記為掌握
            if progress.interval >= 5:
                progress.is_mastered = True
        else:
            # 用戶忘記了，重設間隔
            progress.interval = 0
            progress.next_review_date = now + timedelta(minutes=10)  # 10 分鐘後複習
            progress.is_mastered = False
            
        progress.save()
        
        # 更新用戶學習檔案
        profile, _ = UserLearningProfile.objects.get_or_create(user=request.user)
        today = timezone.localdate()
        if profile.last_activity_date != today:
            # 新的一天，更新活動日期和連鎖日數
            profile.last_activity_date = today
            profile.streak_days += 1
            profile.words_learned_today = 1
        else:
            # 同一天，累加學習單字數
            profile.words_learned_today += 1
        profile.save()
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'msg': str(e)}, status=400)


# === 忘記密碼流程視圖 ===

def forgot_password_view(request):
    """忘記密碼 - 第一步：輸入帳號，確認帳號是否存在且已設定安全問題"""
    if request.method == 'POST':
        form = ForgotPasswordStep1Form(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            try:
                user = User.objects.get(username=username)
                # 確認該帳號有設定安全問題
                if hasattr(user, 'security_question'):
                    # 將帳號儲存到 session，進入下一步
                    request.session['reset_username'] = username
                    return redirect('security_question')
                else:
                    form.add_error('username', '此帳號尚未設定安全問題，無法透過此方式重設密碼。')
            except User.DoesNotExist:
                # 不明確告知帳號不存在（防止帳號枚舉攻擊）
                form.add_error('username', '找不到此帳號，請確認輸入是否正確。')
    else:
        form = ForgotPasswordStep1Form()
    return render(request, 'vocabulary/forgot_password.html', {'form': form})


def security_question_view(request):
    """忘記密碼 - 第二步：顯示安全問題並驗證答案"""
    username = request.session.get('reset_username')
    if not username:
        return redirect('forgot_password')

    try:
        user = User.objects.get(username=username)
        sq = user.security_question
    except (User.DoesNotExist, SecurityQuestion.DoesNotExist):
        return redirect('forgot_password')

    if request.method == 'POST':
        form = SecurityAnswerForm(request.POST)
        if form.is_valid():
            if sq.check_answer(form.cleaned_data['answer']):
                # 答案正確，標記已驗證，進入重設密碼步驟
                request.session['reset_verified'] = True
                return redirect('reset_password')
            else:
                form.add_error('answer', '答案不正確，請再試一次。')
    else:
        form = SecurityAnswerForm()

    return render(request, 'vocabulary/security_question.html', {
        'form': form,
        'question_display': sq.get_question_display(),
    })


def reset_password_view(request):
    """忘記密碼 - 第三步：輸入並儲存新密碼"""
    username = request.session.get('reset_username')
    verified = request.session.get('reset_verified', False)

    # 必須先完成前兩步才能到這裡
    if not username or not verified:
        return redirect('forgot_password')

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return redirect('forgot_password')

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            # 設定新密碼
            user.set_password(form.cleaned_data['new_password1'])
            user.save()
            # 清除 session 中的重設標記
            for key in ['reset_username', 'reset_verified']:
                request.session.pop(key, None)
            return redirect('reset_password_done')
    else:
        form = ResetPasswordForm()

    return render(request, 'vocabulary/reset_password.html', {'form': form})


def reset_password_done_view(request):
    """忘記密碼 - 完成頁面"""
    return render(request, 'vocabulary/reset_password_done.html')