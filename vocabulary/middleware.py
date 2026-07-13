from django.utils import timezone
from datetime import timedelta
from vocabulary.models import UserLearningProfile

class DailyActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                profile = request.user.learning_profile
                today = timezone.localdate()
                if profile.last_activity_date != today:
                    if profile.last_activity_date == today - timedelta(days=1):
                        profile.streak_days += 1
                    else:
                        profile.streak_days = 1
                    
                    profile.last_activity_date = today
                    profile.words_learned_today = 0
                    profile.save()
            except UserLearningProfile.DoesNotExist:
                pass
                
        response = self.get_response(request)
        return response
