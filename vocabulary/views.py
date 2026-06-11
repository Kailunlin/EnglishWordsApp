import random
import json
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Vocabulary, WrongAnswer, FavoriteWord, UserLearningProfile, WordProgress

from django.core.paginator import Paginator
from django.db.models import Q

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('word_list')
    else:
        form = UserCreationForm()
    return render(request, 'vocabulary/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect(request.GET.get('next', 'word_list'))
    else:
        form = AuthenticationForm()
    return render(request, 'vocabulary/login.html', {'form': form})

def logout_view(request):
    if request.method == 'POST':
        logout(request)
    return redirect('word_list')

def word_list(request):
    query = request.GET.get('q', '')
    tab = request.GET.get('tab', 'all')
    
    words = Vocabulary.objects.all()

    if query:
        words = words.filter(
            Q(english__icontains=query) | Q(chinese__icontains=query)
        )
        
    if request.user.is_authenticated:
        if tab == 'learning':
            words = words.filter(progresses__user=request.user).distinct()
        elif tab == 'unlearned':
            words = words.exclude(progresses__user=request.user).distinct()

    words = words.order_by('english')

    paginator = Paginator(words, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    favorite_word_ids = set()
    if request.user.is_authenticated:
        favorite_word_ids = set(request.user.favorites.values_list('word_id', flat=True))

    return render(request, "vocabulary/word_list.html", {
        "page_obj": page_obj,
        "query": query,
        "tab": tab,
        "favorite_word_ids": favorite_word_ids,
    })

@login_required
def quiz_start(request):
    # Get up to 10 random words
    all_words = list(Vocabulary.objects.values_list('id', flat=True))
    if not all_words:
        return render(request, "vocabulary/quiz_start.html", {"error": "尚未建立任何單字"})
    
    sample_size = min(10, len(all_words))
    quiz_word_ids = random.sample(all_words, sample_size)
    
    # Initialize session state
    request.session['quiz_word_ids'] = quiz_word_ids
    request.session['quiz_index'] = 0
    request.session['quiz_score'] = 0
    
    return render(request, "vocabulary/quiz_start.html", {"total_questions": sample_size})

@login_required
def quiz_question(request):
    quiz_word_ids = request.session.get('quiz_word_ids')
    quiz_index = request.session.get('quiz_index')
    
    if quiz_word_ids is None or quiz_index is None:
        return redirect('quiz_start')
        
    if quiz_index >= len(quiz_word_ids):
        return redirect('quiz_result')
        
    current_word_id = quiz_word_ids[quiz_index]
    word = Vocabulary.objects.get(id=current_word_id)
    
    # Get 3 distinct distractors
    other_words = list(Vocabulary.objects.exclude(chinese=word.chinese).values_list('chinese', flat=True).distinct())
    distractors = random.sample(other_words, min(3, len(other_words)))
    
    options = distractors + [word.chinese]
    random.shuffle(options)
    
    # Store current options and correct answer in session for the answer view to verify
    request.session['current_word_id'] = current_word_id
    
    return render(request, "vocabulary/quiz_question.html", {
        "word": word,
        "options": options,
        "current_q": quiz_index + 1,
        "total_q": len(quiz_word_ids)
    })

@login_required
def quiz_answer(request):
    if request.method != "POST":
        return redirect('quiz_question')
        
    quiz_word_ids = request.session.get('quiz_word_ids')
    quiz_index = request.session.get('quiz_index')
    current_word_id = request.session.get('current_word_id')
    
    submitted_q_index = request.POST.get("q_index")
    if submitted_q_index and submitted_q_index != str(quiz_index + 1):
        return redirect('quiz_question')
    
    if not current_word_id:
        return redirect('quiz_start')
        
    word = Vocabulary.objects.get(id=current_word_id)
    user_answer = request.POST.get("answer")
    
    is_correct = (user_answer == word.chinese)
    
    if is_correct:
        request.session['quiz_score'] = request.session.get('quiz_score', 0) + 1
    else:
        WrongAnswer.objects.create(
            user=request.user,
            word=word,
            user_answer=user_answer or "未作答"
        )
        
    # Increment index for next question
    request.session['quiz_index'] = quiz_index + 1
    
    is_last = (request.session['quiz_index'] >= len(quiz_word_ids))
    
    return render(request, "vocabulary/quiz_answer.html", {
        "word": word,
        "user_answer": user_answer,
        "is_correct": is_correct,
        "is_last": is_last,
    })

@login_required
def quiz_result(request):
    score = request.session.get('quiz_score', 0)
    quiz_word_ids = request.session.get('quiz_word_ids', [])
    total = len(quiz_word_ids)
    
    # Clear session
    for key in ['quiz_word_ids', 'quiz_index', 'quiz_score', 'current_word_id']:
        if key in request.session:
            del request.session[key]
            
    return render(request, "vocabulary/quiz_result.html", {
        "score": score,
        "total": total
    })

@login_required
def wrong_list(request):
    wrongs = WrongAnswer.objects.filter(user=request.user).order_by("-created_at")

    paginator = Paginator(wrongs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "vocabulary/wrong_list.html", {
        "page_obj": page_obj
    })

@login_required
def toggle_favorite(request, word_id):
    if request.method == "POST":
        word = get_object_or_404(Vocabulary, id=word_id)
        favorite, created = FavoriteWord.objects.get_or_create(user=request.user, word=word)
        if not created:
            favorite.delete()
            return JsonResponse({"status": "removed"})
        return JsonResponse({"status": "added"})
    return JsonResponse({"error": "Invalid request method"}, status=400)

@login_required
def favorite_list(request):
    query = request.GET.get('q', '')
    favorites_qs = FavoriteWord.objects.filter(user=request.user).select_related('word')
    
    if query:
        favorites_qs = favorites_qs.filter(
            Q(word__english__icontains=query) | Q(word__chinese__icontains=query)
        )
    
    # We want to paginate the FavoriteWord objects
    paginator = Paginator(favorites_qs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "vocabulary/favorite_list.html", {
        "page_obj": page_obj,
        "query": query,
    })

# --- Dashboard & Flashcard Views ---

@login_required
def dashboard_view(request):
    profile, created = UserLearningProfile.objects.get_or_create(user=request.user)
    
    today = timezone.localdate()
    if profile.last_activity_date != today:
        if profile.last_activity_date and profile.last_activity_date < today - timedelta(days=1):
            profile.streak_days = 0
        profile.words_learned_today = 0
        profile.save()

    now = timezone.now()
    review_due_count = WordProgress.objects.filter(user=request.user, next_review_date__lte=now, is_mastered=False).count()

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
    try:
        data = json.loads(request.body)
        new_goal = int(data.get('goal', 20))
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
    profile, _ = UserLearningProfile.objects.get_or_create(user=request.user)
    now = timezone.now()
    due_progresses = list(WordProgress.objects.filter(user=request.user, next_review_date__lte=now, is_mastered=False).select_related('word'))
    
    due_words = [p.word for p in due_progresses]
    
    batch_size = profile.daily_goal  # Respect user's daily goal setting
    if len(due_words) < batch_size:
        progress_word_ids = WordProgress.objects.filter(user=request.user).values_list('word_id', flat=True)
        new_words = list(Vocabulary.objects.exclude(id__in=progress_word_ids)[:batch_size - len(due_words)])
        due_words.extend(new_words)

    random.shuffle(due_words)

    words_data = []
    for w in due_words:
        words_data.append({
            'id': w.id,
            'english': w.english,
            'chinese': w.chinese,
            'part_of_speech': w.part_of_speech,
            'example': w.example,
            'example_translation': w.example_translation,
        })
    
    return render(request, "vocabulary/flashcard.html", {'words_json': json.dumps(words_data)})

@login_required
@require_POST
def api_swipe_word(request):
    try:
        data = json.loads(request.body)
        word_id = data.get('word_id')
        action = data.get('action') 
        
        word = get_object_or_404(Vocabulary, id=word_id)
        progress, created = WordProgress.objects.get_or_create(user=request.user, word=word)
        
        now = timezone.now()
        
        if action == 'remembered':
            progress.interval += 1
            intervals = [1, 3, 7, 14, 30]
            days_to_add = intervals[min(progress.interval - 1, len(intervals) - 1)]
            progress.next_review_date = now + timedelta(days=days_to_add)
            if progress.interval >= 5:
                progress.is_mastered = True
        else:
            progress.interval = 0
            progress.next_review_date = now + timedelta(minutes=10)
            progress.is_mastered = False
            
        progress.save()
        
        profile, _ = UserLearningProfile.objects.get_or_create(user=request.user)
        today = timezone.localdate()
        if profile.last_activity_date != today:
            profile.last_activity_date = today
            profile.streak_days += 1
            profile.words_learned_today = 1
        else:
            profile.words_learned_today += 1
        profile.save()
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'msg': str(e)}, status=400)