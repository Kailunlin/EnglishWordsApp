# 📖 EnglishWordsApp (英文單字學習系統)

這是一個基於 Django 開發的現代化全端英文單字學習應用程式。透過**間隔重複法 (Spaced Repetition)**、直覺的閃卡互動、測驗挑戰，以及個人化的進度追蹤，幫助使用者以最高效率建立並鞏固長期記憶中的英文單字庫。

---

## ✨ 核心功能特色

- **🧠 間隔重複學習演算法 (SRS)**：根據您的熟悉程度，自動推算每個單字最佳的複習時間，將學習效率最大化。
- **🗂️ 互動式閃卡學習**：採用類似 Tinder 的左右滑動手勢（左滑不熟、右滑記住），搭配單字發音與自動翻轉動畫，打造沉浸式學習體驗。
- **📝 智慧測驗系統**：自訂難度進行測驗，答錯的題目會自動進入「無限輪迴」直到答對為止，測驗後直接將錯題重點標示。
- **📈 個人學習儀表板**：追蹤您的**連續登入天數 (Streak)**、今日學習進度、並顯示當日待複習的單字數量。
- **🎯 難度分級與篩選**：將單字分為 Easy、Medium、Hard，讓您可以針對目前的程度進行特訓。
- **⭐ 最愛收藏 & ❌ 專屬錯題本**：輕鬆標記想重點加強的單字，並隨時針對錯題本進行重點複習。
- **🔐 完整會員系統**：獨立的個人進度追蹤，並支援「安全問題 (Security Question)」忘記密碼還原機制。

---

## 🚀 快速開始

### 1. 建立虛擬環境 (Virtual Environment)

```powershell
# 建立 Python 虛擬環境
python -m venv .venv

# 啟動虛擬環境 (Windows PowerShell)
.\.venv\Scripts\Activate.ps1
# macOS/Linux 請使用: source .venv/bin/activate
```

### 2. 安裝依賴套件

```powershell
pip install django
```

### 3. 初始化資料庫

執行以下指令建立資料庫與資料表：
```powershell
python manage.py makemigrations
python manage.py migrate
```

### 4. 匯入初始單字庫

我們準備了自動匯入指令，可以快速將預設的單字庫匯入您的資料庫中：
```powershell
python manage.py seed_vocabulary
```

### 5. 建立管理者帳號 (可選)

```powershell
python manage.py createsuperuser
```

### 6. 啟動應用程式

啟動本地端開發伺服器：
```powershell
python manage.py runserver
```

---

## 📂 專案架構概覽

- `config/` — Django 專案核心設定、環境配置與根路由 (`urls.py`)。
- `vocabulary/` — 主要的應用程式 (App)，包含：
  - **`models.py`**: 定義資料庫模型（單字庫 `Vocabulary`、學習檔案 `UserLearningProfile`、進度追蹤 `WordProgress` 等）。
  - **`views.py` & `urls.py`**: 處理所有的頁面邏輯、路由分配以及前端互動的 API。
  - **`middleware.py`**: 負責每次請求的攔截處理，包含自動結算「連續登入天數」與每日任務進度。
  - **`templates/`**: 採用 Bootstrap 5 與玻璃擬物化 (Glassmorphism) 設計的精美 HTML 介面。
  - **`management/commands/`**: 方便開發與部署的腳本（例如資料匯入指令）。
- `db.sqlite3` — 開發環境所使用的本地 SQLite 資料庫檔案。

---
*Happy Learning! 祝您學習愉快！* 🎉
