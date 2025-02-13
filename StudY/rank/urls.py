from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from rest_framework.routers import SimpleRouter
from .views import *
from rest_framework import routers

router = SimpleRouter()


urlpatterns = [



] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)