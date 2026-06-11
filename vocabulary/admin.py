from django.contrib import admin
from .models import Vocabulary


@admin.register(Vocabulary)
class VocabularyAdmin(admin.ModelAdmin):
    list_display = ("english", "chinese", "example")
    search_fields = ("english", "chinese")
    list_filter = ("created_at",)