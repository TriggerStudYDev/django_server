from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from .views import *
from rest_framework import routers


urlpatterns = [

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)