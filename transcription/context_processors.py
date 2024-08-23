# your_app_name/context_processors.py

from .models import UserClassEnrollment

def user_class_code(request):
    if request.user.is_authenticated:
        user_class_enrollment = UserClassEnrollment.objects.filter(user=request.user).last()
        return {'user_class_code': user_class_enrollment.class_code if user_class_enrollment else None}
    return {}
