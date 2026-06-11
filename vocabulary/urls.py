from django.urls import path
from django.views.generic.base import RedirectView
from . import views

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.dashboard_view, name="dashboard"),
    path("words/", views.word_list, name="word_list"),
    path("quiz/", RedirectView.as_view(url='/quiz/start/', permanent=False)),
    path("quiz/start/", views.quiz_start, name="quiz_start"),
    path("quiz/question/", views.quiz_question, name="quiz_question"),
    path("quiz/answer/", views.quiz_answer, name="quiz_answer"),
    path("quiz/result/", views.quiz_result, name="quiz_result"),
    path("wrong/", views.wrong_list, name="wrong_list"),
    path("favorites/", views.favorite_list, name="favorite_list"),
    path("favorites/toggle/<int:word_id>/", views.toggle_favorite, name="toggle_favorite"),
    path("study/", views.flashcard_study_view, name="flashcard_study"),
    path("api/swipe/", views.api_swipe_word, name="api_swipe_word"),
    path("api/goal/", views.update_daily_goal_api, name="update_daily_goal"),
]