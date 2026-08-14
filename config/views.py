"""Vistas de errores globales del proyecto."""

from django.shortcuts import render


def page_not_found(request, exception=None):
    """Página genérica para URLs que no existen (404)."""
    return render(
        request,
        "404.html",
        status=404,
    )


def server_error(request):
    """Página genérica para errores internos (500)."""
    return render(
        request,
        "500.html",
        status=500,
    )
