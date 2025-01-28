from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from .views import *
from rest_framework import routers


router = routers.SimpleRouter()

router.register(r'universities', UniversityViewSet)
router.register(r'faculties', FacultyViewSet)
router.register(r'departments', DepartmentViewSet)
router.register(r'discipline', DisciplineViewSet)
router.register(r'education-forms', FormOfStudyViewSet)
router.register(r'customer-feedback', CustomerFeedbackViewSet)
router.register(r'portfolio', PortfolioViewSet)
router.register(r'student-card-comment', StudentCardCommentViewSet)
# Получение всей информации
router.register(r'student-card', StudentCardViewSet)


urlpatterns = [
    # регистрация user
    path('registration/general-info/', RegisterGeneralInfoAPIView.as_view(), name='register-general-info'),
    # регистрация profile
    path('registration/profile', RegisterProfileInfoAPIView.as_view(), name='register-profile'),
    # регистрация заявки на верификацию
    path('registration/education-info/', RegisterEducationInfoAPIView.as_view(), name='register-education-info'),
    # Добавление обратной связи для исполнителей
    path('registration/customer-feedback-info/', RegisterCustomerFeedbackInfoAPIView.as_view(),
         name='register-customer-feedback-info'),
    # Добавление портфолио для исполнителей
    path('registration/portfolio-info/', RegisterPortfolioInfoAPIView.as_view(),
         name='register-portfolio-info'),

    path('student-card-verification/<int:student_card_id>/', StudentCardVerificationAPIView.as_view(),
         name='student-card-verification'),
    path('student-card/update/', StudentCardUpdateView.as_view(), name='student-card/update/'),
    # Логирование пользователя
    path('login/', LoginAPIView.as_view(), name='login'),

    # TODO Обновленная регистрация, пока не работает
    path('registration/', UnifiedRegistrationAPIView.as_view(), name='unified-registration'),


    path('', include(router.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)