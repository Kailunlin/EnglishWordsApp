# EnglishWordsApp

A Django-based vocabulary learning app with flashcards, quizzes, favorites, and wrong-answer tracking.

## Features

- Vocabulary list management
- Quiz mode with questions and answer review
- Flashcards for study practice
- Favorite words and wrong-answer tracking
- User registration and login

## Setup

1. Create and activate a Python virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install django
```

> If you have a `requirements.txt` file later, use:
> ```powershell
> pip install -r requirements.txt
> ```

3. Run migrations:

```powershell
python manage.py migrate
```

4. Create a superuser (optional):

```powershell
python manage.py createsuperuser
```

5. Run the development server:

```powershell
python manage.py runserver
```

Then open `http://127.0.0.1:8000/` in your browser.

## Project structure

- `config/` — Django project settings and URL configuration
- `vocabulary/` — main app with models, views, templates, and management commands
- `db.sqlite3` — local SQLite database file

## GitHub

This repository is linked to:

`https://github.com/Kailunlin/EnglishWordsApp`
