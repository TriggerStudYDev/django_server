from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from .views import *
from rest_framework import routers


router = routers.SimpleRouter()

router.register(r'auth/universities', UniversityViewSet)
router.register(r'auth/faculties', FacultyViewSet)
router.register(r'auth/departments', DepartmentViewSet)
router.register(r'auth/discipline', DisciplineViewSet)

router.register(r'auth/education-forms', FormOfStudyViewSet)
router.register(r'auth/customer-feedback', CustomerFeedbackViewSet)
router.register(r'auth/portfolio', PortfolioViewSet)
router.register(r'auth/student-card-comment', StudentCardCommentViewSet)
# Получение всей информации
router.register(r'auth/student-card', StudentCardViewSet)
# router.register(r'', ReferralTokenCheckAPIView)


urlpatterns = [
    # регистрация user
    path('auth/registration/general-info/', RegisterGeneralInfoAPIView.as_view(), name='register-general-info'),
    # регистрация profile
    path('auth/registration/profile', RegisterProfileInfoAPIView.as_view(), name='register-profile'),
    # регистрация заявки на верификацию
    path('auth/registration/education-info/', RegisterEducationInfoAPIView.as_view(), name='register-education-info'),
    # Добавление обратной связи для исполнителей
    path('auth/registration/customer-feedback-info/', RegisterCustomerFeedbackInfoAPIView.as_view(),
         name='register-customer-feedback-info'),
    # Добавление портфолио для исполнителей
    path('auth/registration/portfolio-info/', RegisterPortfolioInfoAPIView.as_view(),
         name='register-portfolio-info'),
    # Обновленная регистрация (через транзакции)
    path('auth/register', RegisterUserView.as_view(), name='register'),

    # Изменить статус анкеты
    path('auth/student-card-verification/<int:student_card_id>/', StudentCardVerificationAPIView.as_view(),
         name='student-card-verification'),
    # Обновление анкеты
    path('auth/student-card/update/', StudentCardUpdateView.as_view(), name='student-card/update/'),
    # Авторизация
    path('auth/login/', LoginAPIView.as_view(), name='login'),

    path('auth/referral-check/', ReferralTokenCheckAPIView.as_view(), name="referal-user-get"),


    path('', include(router.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)