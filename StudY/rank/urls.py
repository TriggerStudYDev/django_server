from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from rest_framework.routers import SimpleRouter
from .views import *
from rest_framework import routers

router = SimpleRouter()
router.register(r'all-ranks', RankViewSet, basename='rank')

urlpatterns = [
    path('', include(router.urls)),
    path('payment-rank/', RankPurchaseAPIView.as_view(), name='payment-rank'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)