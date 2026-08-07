"""Filtros y etiquetas de plantilla de «¿Lo quiero?»."""

from django import template

register = template.Library()

STATUS_CLASSES = {
    "new": "bg-sky-100 text-sky-800 border-sky-200",
    "waiting": "bg-amber-100 text-amber-800 border-amber-200",
    "comparing": "bg-violet-100 text-violet-800 border-violet-200",
    "purchased": "bg-green-100 text-green-800 border-green-200",
    "discarded": "bg-slate-200 text-slate-600 border-slate-300",
}

REC_CLASSES = {
    "considerar": "bg-emerald-50 text-emerald-800 border-emerald-300",
    "alternativa": "bg-violet-50 text-violet-800 border-violet-300",
    "esperar": "bg-amber-50 text-amber-800 border-amber-300",
    "descartar": "bg-red-50 text-red-700 border-red-300",
}

PRIORITY_CLASSES = {
    "low": "bg-slate-100 text-slate-600",
    "medium": "bg-amber-100 text-amber-800",
    "high": "bg-red-100 text-red-700",
}


@register.filter
def add_class(field, css_class):
    """Devuelve el campo con una clase extra (para marcar errores)."""
    current = field.field.widget.attrs.get("class", "")
    return field.as_widget(attrs={"class": f"{current} {css_class}"})


@register.filter
def status_class(status):
    return STATUS_CLASSES.get(status, "bg-slate-100 text-slate-700")


@register.filter
def rec_class(code):
    return REC_CLASSES.get(code, "bg-slate-100 text-slate-700")


@register.filter
def priority_class(priority):
    return PRIORITY_CLASSES.get(priority, "bg-slate-100 text-slate-600")
