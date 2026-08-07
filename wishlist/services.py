"""Reglas de negocio de «¿Lo quiero?».

Toda la lógica de decisión vive aquí, separada de las vistas, para que
sea fácil de probar y de reutilizar.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate

from .models import Product

# ---------------------------------------------------------------------------
# Periodo de reflexión
# ---------------------------------------------------------------------------


def suggested_waiting_days(price: Decimal | None) -> int:
    """Días de reflexión recomendados según el precio.

    - Menos de 15 €: 7 días.
    - Entre 15,00 € y 35 €: 15 días (borde 15,00 € incluido).
    - Entre 35,00 € y 50 €: 30 días (borde 35,00 € incluido).
    - 50 € o más: 45 días.
    """
    if price is None:
        return 7
    if price < 0:
        raise ValueError("El precio no puede ser negativo.")
    if price < Decimal("15"):
        return 7
    if price < Decimal("35"):
        return 15
    if price < Decimal("50"):
        return 30
    return 45


def compute_review_date(reference_date: date, waiting_days: int) -> date:
    """Fecha de revisión a partir de una fecha de referencia."""
    if waiting_days < 0:
        raise ValueError("Los días de espera no pueden ser negativos.")
    return reference_date + timedelta(days=waiting_days)


# ---------------------------------------------------------------------------
# Recomendación de compra
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Recommendation:
    """Orientación de compra. Es una ayuda, no una decisión automática."""

    label: str
    code: str
    description: str


def purchase_recommendation(need_score: int, interest_score: int) -> Recommendation:
    """Matriz de recomendación a partir de la última revisión."""
    if not 1 <= need_score <= 10:
        raise ValueError("La necesidad debe estar entre 1 y 10.")
    if not 1 <= interest_score <= 10:
        raise ValueError("El interés debe estar entre 1 y 10.")

    high_need = need_score >= 7
    high_interest = interest_score >= 7

    if high_need and high_interest:
        return Recommendation(
            label="Considerar compra",
            code="considerar",
            description=(
                "La necesidad y el interés son altos. "
                "Puede ser un buen momento para comprarlo."
            ),
        )
    if high_need and not high_interest:
        return Recommendation(
            label="Buscar una alternativa",
            code="alternativa",
            description=(
                "La necesidad es alta, pero el interés es bajo. "
                "Revisa los «dupes» y alternativas antes de comprar."
            ),
        )
    if not high_need and high_interest:
        return Recommendation(
            label="Esperar: puede ser un capricho",
            code="esperar",
            description=(
                "Te atrae, pero no lo necesitas. Espera un poco más antes de decidir."
            ),
        )
    return Recommendation(
        label="Descartar",
        code="descartar",
        description=("Ni lo necesitas ni te interesa. Lo más sensato es descartarlo."),
    )


def product_recommendation(product: Product) -> Recommendation | None:
    """Recomendación basada en la última revisión del producto."""
    review = product.last_review()
    if review is None:
        return None
    return purchase_recommendation(review.need_score, review.interest_score)


# ---------------------------------------------------------------------------
# Comparación de alternativas
# ---------------------------------------------------------------------------


def price_comparison(product_price, alternative_price):
    """Diferencia de precio y porcentaje de ahorro frente al original.

    Devuelve (diferencia, porcentaje_ahorro). Ambos pueden ser None cuando
    falta algún precio, y el porcentaje se omite si el precio original es 0
    para evitar divisiones por cero.
    """
    if product_price is None or alternative_price is None:
        return None, None

    difference = alternative_price - product_price
    if product_price == 0:
        return difference, None

    savings = (product_price - alternative_price) / product_price * 100
    savings = savings.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return difference.quantize(Decimal("0.01")), savings


def combined_score(alternative) -> Decimal:
    """Puntuación combinada de una alternativa, en escala 0-10.

    Fórmula documentada (orientativa, no objetiva):

        similitud (0-100, normalizada a 0-10) con peso 40 %
        + calidad (1-10) con peso 35 %
        + durabilidad (1-10) con peso 25 %

    Devuelve un decimal con un solo dígito.
    """
    similarity = alternative.similarity_score / 10
    combined = (
        Decimal(similarity) * Decimal("0.4")
        + Decimal(alternative.quality_score) * Decimal("0.35")
        + Decimal(alternative.durability_score) * Decimal("0.25")
    )
    return combined.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def best_combined_alternative(alternatives):
    """Alternativa con mejor puntuación combinada, o None."""
    if not alternatives:
        return None
    return max(alternatives, key=combined_score)


def cheapest_alternative(alternatives):
    """Alternativa más barata, o None."""
    priced = [a for a in alternatives if a.price is not None]
    if not priced:
        return None
    return min(priced, key=lambda a: a.price)


# ---------------------------------------------------------------------------
# Estadísticas
# ---------------------------------------------------------------------------


def _format(value, digits=1):
    if value is None:
        return None
    return round(value, digits)


def compute_stats():
    """Resumen estadístico global. Controla la ausencia de datos."""
    products = Product.objects.all()
    total = products.count()
    purchased = products.filter(status=Product.Status.PURCHASED)
    discarded = products.filter(status=Product.Status.DISCARDED)

    purchased_count = purchased.count()
    discarded_count = discarded.count()
    money_spent = purchased.aggregate(total=Sum("current_price"))["total"] or Decimal(
        "0"
    )
    discarded_value = discarded.aggregate(total=Sum("current_price"))[
        "total"
    ] or Decimal("0")

    discarded_percent = (discarded_count / total * 100) if total else 0

    category_counts = (
        products.exclude(category="")
        .values("category")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    top_category = category_counts.first()["category"] if category_counts else None

    avg_days_to_purchase = _format(_average_days(purchased, "purchased_at"))
    avg_days_to_discard = _format(_average_days(discarded, "discarded_at"))

    return {
        "total_products": total,
        "purchased_count": purchased_count,
        "discarded_count": discarded_count,
        "discarded_percent": round(discarded_percent, 1),
        "money_spent": money_spent,
        "discarded_value": discarded_value,
        "top_category": top_category,
        "avg_days_to_purchase": avg_days_to_purchase,
        "avg_days_to_discard": avg_days_to_discard,
    }


def _average_days(queryset, finished_field):
    """Días medios entre la creación y la finalización de un producto."""
    rows = queryset.exclude(**{f"{finished_field}__isnull": True}).annotate(
        finished_date=TruncDate(finished_field)
    )
    if not rows:
        return None
    total_days = 0
    count = 0
    for row in rows:
        finished = row.finished_date
        if finished is None:
            continue
        total_days += (finished - row.created_at.date()).days
        count += 1
    if count == 0:
        return None
    return total_days / count
