# 📖 EnglishWordsApp

A comprehensive Django-based vocabulary learning application designed to help users efficiently build and retain their English vocabulary through spaced repetition, flashcards, quizzes, and personalized learning tracking.

## ✨ Key Features

- **🧠 Spaced Repetition Learning**: Tracks your mastery of words and schedules them for review at optimal intervals.
- **🗂️ Flashcard Study Mode**: Swipe through words with a dynamic flashcard UI for intuitive memorization.
- **📝 Interactive Quizzes**: Test your knowledge and track wrong answers automatically for focused review.
- **📈 Learning Profiles**: Keep track of daily learning goals, streaks, and overall progress.
- **⭐ Favorites & ❌ Wrong Answers**: Easily bookmark important words and revisit mistakes.
- **🔐 User Accounts**: Dedicated user progress tracking with secure registration and login.

## 🚀 Quick Start

### 1. Set Up Virtual Environment

```powershell
# Create a Python virtual environment
python -m venv .venv

# Activate the virtual environment (Windows)
.\.venv\Scripts\Activate.ps1
# On macOS/Linux use: source .venv/bin/activate
```

### 2. Install Dependencies

```powershell
pip install django
```
*(If a `requirements.txt` is added later, run `pip install -r requirements.txt` instead)*

### 3. Initialize Database

Run the following commands to create the database schema:
```powershell
python manage.py migrate
```

### 4. Seed Vocabulary Data

You can easily populate your database with initial vocabulary words using the provided management commands:
```powershell
python manage.py seed_vocabulary
```

### 5. Create an Admin User (Optional)

```powershell
python manage.py createsuperuser
```

### 6. Run the Application

Start the local development server:
```powershell
python manage.py runserver
```

Open your browser and navigate to [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

## 📂 Project Structure

- `config/` — Django project configuration, settings, and root routing.
- `vocabulary/` — The core application containing:
  - **Models**: Defines database schema (`Vocabulary`, `UserLearningProfile`, `WordProgress`, etc.).
  - **Views & URLs**: Handles page logic, routing, and API endpoints for UI interactions.
  - **Templates**: HTML files containing the frontend user interface.
  - **Management Commands**: Utility scripts for data import (`seed_vocabulary`, `import_vocab`).
- `db.sqlite3` — The local SQLite database file used for development.

---
*Happy Learning!* 🎉
