from django.urls import path
from django.views.generic.base import RedirectView
from . import views

urlpatterns = [
    # === 使用者帳號與驗證 ===
    path("register/", views.register_view, name="register"),  # 註冊帳號頁面
    path("login/", views.login_view, name="login"),           # 登入系統頁面
    path("logout/", views.logout_view, name="logout"),        # 登出系統動作
    
    # === 首頁與主要儀表板 ===
    path("", views.dashboard_view, name="dashboard"),         # 學習儀表板（顯示每日進度與連鎖天數）
    
    # === 單字與學習資源清單 ===
    path("words/", views.word_list, name="word_list"),        # 總單字庫列表（支援搜尋與難度篩選）
    path("wrong/", views.wrong_list, name="wrong_list"),      # 錯題本（記錄過去測驗中答錯的單字）
    path("favorites/", views.favorite_list, name="favorite_list"),  # 我的最愛單字列表
    path("favorites/toggle/<int:word_id>/", views.toggle_favorite, name="toggle_favorite"),  # 切換加入/移除最愛的 API 端點
    
    # === 閃卡學習系統（間隔重複法） ===
    path("study/", views.flashcard_study_view, name="flashcard_study"),  # 閃卡學習主頁面
    path("api/swipe/", views.api_swipe_word, name="api_swipe_word"),     # 接收閃卡左右滑動結果並更新記憶進度的 API
    path("api/goal/", views.update_daily_goal_api, name="update_daily_goal"), # 更新每日學習目標數量的 API
    
    # === 單字測驗流程 ===
    path("quiz/", RedirectView.as_view(url='/quiz/start/', permanent=False)),  # 進入 /quiz/ 時自動導向到測驗開始頁面
    path("quiz/start/", views.quiz_start, name="quiz_start"),           # 測驗開始前的設定畫面（例如選擇難度）
    path("quiz/question/", views.quiz_question, name="quiz_question"),  # 顯示目前測驗的題目與選項
    path("quiz/answer/", views.quiz_answer, name="quiz_answer"),        # 接收測驗答案並判斷對錯（如果答錯會塞回題庫）
    path("quiz/result/", views.quiz_result, name="quiz_result"),        # 測驗結束後顯示錯題總結與複習
    
    # === 忘記密碼與安全問題還原流程 ===
    path("forgot-password/", views.forgot_password_view, name="forgot_password"),                  # 忘記密碼流程：輸入要找回的帳號
    path("forgot-password/question/", views.security_question_view, name="security_question"),     # 忘記密碼流程：回答該帳號設定的安全問題
    path("forgot-password/reset/", views.reset_password_view, name="reset_password"),              # 忘記密碼流程：回答正確後設定新的密碼
    path("forgot-password/done/", views.reset_password_done_view, name="reset_password_done"),     # 忘記密碼流程：密碼重設完成的成功提示畫面
]