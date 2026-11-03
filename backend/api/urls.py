from django.contrib import admin
from django.urls import path

from trips import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/trips', views.trips),
    path('api/places', views.places),
]
