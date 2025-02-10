from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from .views import *
from rest_framework import routers





urlpatterns = [
    path('create-withdrawal/', CreateWithdrawalRequest.as_view(), name='create-withdrawal'),
    # path('user-withdrawal/', UserWithdrawalRequests.as_view(), name='user-withdrawal'),
    # path('finance-withdrawal/', FinanceWithdrawalRequests.as_view(), name='finance-withdrawal'),
    path('approve-reject-withdrawal/<int:pk>/', ApproveRejectWithdrawalRequest.as_view(), name='approve-reject-withdrawal/'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)