"""Configuración de URLs del proyecto «¿Lo quiero?»."""

from django.contrib import admin
from django.urls import include, path

handler404 = "config.views.page_not_found"
handler500 = "config.views.server_error"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("wishlist.urls")),
]
