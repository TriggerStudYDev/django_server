from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from .views import *
from rest_framework import routers




router = SimpleRouter()
router.register(r'user-withdrawal', UserWithdrawalRequests, basename='user-withdrawal')
router.register(r'finance-withdrawal', FinanceWithdrawalRequests, basename='finance-withdrawal')
router.register(r'balance', BalanceViewSet, basename='user-balance')

urlpatterns = [
    path('', include(router.urls)),
    path('create-withdrawal/', CreateWithdrawalRequest.as_view(), name='create-withdrawal'),
    path('approve-reject-withdrawal/<int:pk>/', ApproveRejectWithdrawalRequest.as_view(),
         name='approve-reject-withdrawal/'),
    path('bonus-transfer/', BonusTransferView.as_view(), name='bonus-transfer'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)