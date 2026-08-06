"""Configuración de URLs del proyecto «¿Lo quiero?»."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("wishlist.urls")),
]
