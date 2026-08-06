"""Vistas de «¿Lo quiero?».

Vistas basadas en funciones: las mutaciones usan POST y redirigen para
evitar reenvíos, y la lógica de negocio vive en ``services``.
"""

from decimal import Decimal
from itertools import chain

from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import (
    AlternativeForm,
    CategoryRenameForm,
    OwnedItemForm,
    PriceSnapshotForm,
    ProductForm,
    ReviewForm,
)
from .models import Alternative, OwnedItem, Product
from .services import (
    best_combined_alternative,
    cheapest_alternative,
    combined_score,
    compute_stats,
    price_comparison,
    product_recommendation,
)

DASHBOARD_GROUPS = [
    Product.Status.NEW,
    Product.Status.WAITING,
    Product.Status.COMPARING,
    Product.Status.POSSIBLE_PURCHASE,
    Product.Status.PURCHASED,
    Product.Status.DISCARDED,
]


def _products_queryset():
    return Product.objects.prefetch_related("alternatives", "reviews")


def _product_grouped_products():
    groups = {status: [] for status in Product.Status}
    for product in _products_queryset():
        groups[product.status].append(product)
    return groups


# ---------------------------------------------------------------------------
# Panel principal
# ---------------------------------------------------------------------------


def dashboard(request):
    groups = _product_grouped_products()

    due_products = [
        p for p in chain.from_iterable(groups.values()) if p.is_due_for_review
    ]

    spent = sum(
        (p.current_price or Decimal("0")) for p in groups[Product.Status.PURCHASED]
    )
    discarded_value = sum(
        (p.current_price or Decimal("0")) for p in groups[Product.Status.DISCARDED]
    )

    board = [
        {
            "status": status,
            "label": status.label,
            "products": groups[status],
            "empty_hint": (
                "Ya has decidido sobre este producto."
                if status in (Product.Status.PURCHASED, Product.Status.DISCARDED)
                else f"Todavía no hay productos «{status.label}»."
            ),
        }
        for status in DASHBOARD_GROUPS
    ]

    context = {
        "board": board,
        "waiting_count": len(groups[Product.Status.WAITING]),
        "due_count": len(due_products),
        "comparing_count": len(groups[Product.Status.COMPARING]),
        "candidate_count": len(groups[Product.Status.POSSIBLE_PURCHASE]),
        "discarded_count": len(groups[Product.Status.DISCARDED]),
        "money_spent": spent,
        "discarded_value": discarded_value,
    }
    return render(request, "wishlist/dashboard.html", context)


# ---------------------------------------------------------------------------
# Productos
# ---------------------------------------------------------------------------


def product_list(request):
    products = _products_queryset().all()
    search = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    category = request.GET.get("category", "")
    order = request.GET.get("order", "created")

    if search:
        products = products.filter(name__icontains=search)
    if status in Product.Status.values:
        products = products.filter(status=status)
    if category:
        products = products.filter(category__iexact=category)

    ordering = {
        "created": "-created_at",
        "name": "name",
        "price": "current_price",
        "review": "review_date",
    }.get(order, "-created_at")
    products = products.order_by(ordering)

    categories = (
        Product.objects.exclude(category="")
        .values_list("category", flat=True)
        .distinct()
        .order_by("category")
    )

    context = {
        "products": products,
        "categories": categories,
        "query": search,
        "current_status": status,
        "current_category": category,
        "current_order": order,
        "statuses": Product.Status.choices,
    }
    return render(request, "wishlist/product_list.html", context)


def product_detail(request, pk):
    product = get_object_or_404(_products_queryset(), pk=pk)

    recommendation = product_recommendation(product)

    comparisons = []
    alternatives = list(product.alternatives.all())
    for alt in alternatives:
        difference, savings = price_comparison(product.current_price, alt.price)
        comparisons.append(
            {
                "alternative": alt,
                "difference": difference,
                "savings": savings,
                "combined": combined_score(alt),
            }
        )

    owned_items = (
        OwnedItem.objects.filter(category__iexact=product.category)
        if product.category
        else OwnedItem.objects.none()
    )

    context = {
        "product": product,
        "recommendation": recommendation,
        "comparisons": comparisons,
        "cheapest": cheapest_alternative(alternatives),
        "best": best_combined_alternative(alternatives),
        "owned_items": owned_items,
    }
    return render(request, "wishlist/product_detail.html", context)


def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, f"Producto «{product.name}» creado.")
            return redirect("product_detail", pk=product.pk)
    else:
        form = ProductForm()
    return render(
        request,
        "wishlist/product_form.html",
        {"form": form, "title": "Nuevo producto", "submit_label": "Crear"},
    )


def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f"Producto «{product.name}» actualizado.")
            return redirect("product_detail", pk=product.pk)
    else:
        form = ProductForm(instance=product)
    return render(
        request,
        "wishlist/product_form.html",
        {"form": form, "title": f"Editar «{product.name}»", "product": product},
    )


def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        name = product.name
        product.delete()
        messages.success(request, f"Producto «{name}» eliminado.")
        return redirect("product_list")
    return render(
        request,
        "wishlist/confirm_delete.html",
        {
            "title": "Eliminar producto",
            "object_name": product.name,
            "detail": (
                "Se eliminarán también sus alternativas, revisiones y "
                "precios registrados. Esta acción no se puede deshacer."
            ),
            "back_url": "product_detail",
            "back_arg": product.pk,
            "delete_url": "product_delete",
            "delete_arg": product.pk,
        },
    )


@require_POST
def product_purchase(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.mark_as_purchased()
    messages.success(request, f"«{product.name}» marcado como comprado.")
    return redirect("product_detail", pk=pk)


@require_POST
def product_discard(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.mark_as_discarded()
    messages.success(request, f"«{product.name}» marcado como descartado.")
    return redirect("product_detail", pk=pk)


@require_POST
def product_postpone(request, pk):
    product = get_object_or_404(Product, pk=pk)
    try:
        days = int(request.POST.get("days", "7"))
    except (TypeError, ValueError):
        days = 7
    if days < 1:
        days = 7
    product.postpone(days)
    messages.success(request, f"Revisión de «{product.name}» pospuesta {days} días.")
    return redirect("product_detail", pk=pk)


# ---------------------------------------------------------------------------
# Categorías
# ---------------------------------------------------------------------------


def category_manage(request):
    """Lista las categorías en uso con opciones de renombrar o eliminar."""
    categories = (
        Product.objects.exclude(category="")
        .values("category")
        .annotate(count=Count("id"))
        .order_by("category")
    )
    return render(
        request,
        "wishlist/category_manage.html",
        {"categories": categories},
    )


@require_POST
def category_rename(request, name):
    """Renombra una categoría en todos los productos que la usan."""
    form = CategoryRenameForm(request.POST)
    if form.is_valid():
        new_name = form.cleaned_data["name"].strip()
        if not new_name:
            messages.error(request, "El nuevo nombre no puede estar vacío.")
        elif new_name.lower() == name.lower():
            messages.info(request, "El nombre no ha cambiado.")
        else:
            count = Product.objects.filter(category=name).update(category=new_name)
            messages.success(
                request,
                f"Categoría «{name}» renombrada a «{new_name}» en {count} producto(s).",
            )
    else:
        messages.error(request, "Nombre de categoría no válido.")
    return redirect("category_manage")


def category_delete(request, name):
    """Elimina una categoría conservando los productos (quedan sin ella)."""
    count = Product.objects.filter(category=name).count()
    if request.method == "POST":
        Product.objects.filter(category=name).update(category="")
        messages.success(
            request,
            f"Categoría «{name}» eliminada de {count} producto(s). "
            "Los productos se conservan, sin categoría.",
        )
        return redirect("category_manage")
    return render(
        request,
        "wishlist/confirm_delete.html",
        {
            "title": "Eliminar categoría",
            "object_name": name,
            "detail": (
                f"{count} producto(s) usarán esta categoría. Se eliminará "
                "solo la etiqueta; los productos no se borran."
            ),
            "back_url": "category_manage",
            "delete_url": "category_delete",
            "delete_arg": name,
        },
    )


# ---------------------------------------------------------------------------
# Alternativas
# ---------------------------------------------------------------------------


def alternative_create(request, product_pk):
    product = get_object_or_404(Product, pk=product_pk)
    if request.method == "POST":
        form = AlternativeForm(request.POST)
        if form.is_valid():
            alternative = form.save(commit=False)
            alternative.product = product
            alternative.save()
            messages.success(request, f"Alternativa «{alternative.name}» añadida.")
            return redirect("product_detail", pk=product.pk)
    else:
        form = AlternativeForm()
    return render(
        request,
        "wishlist/alternative_form.html",
        {
            "form": form,
            "product": product,
            "title": f"Nueva alternativa para «{product.name}»",
        },
    )


def alternative_edit(request, product_pk, pk):
    product = get_object_or_404(Product, pk=product_pk)
    alternative = get_object_or_404(Alternative, pk=pk, product=product)
    if request.method == "POST":
        form = AlternativeForm(request.POST, instance=alternative)
        if form.is_valid():
            form.save()
            messages.success(request, f"Alternativa «{alternative.name}» actualizada.")
            return redirect("product_detail", pk=product.pk)
    else:
        form = AlternativeForm(instance=alternative)
    return render(
        request,
        "wishlist/alternative_form.html",
        {
            "form": form,
            "product": product,
            "title": f"Editar «{alternative.name}»",
        },
    )


def alternative_delete(request, product_pk, pk):
    product = get_object_or_404(Product, pk=product_pk)
    alternative = get_object_or_404(Alternative, pk=pk, product=product)
    if request.method == "POST":
        name = alternative.name
        alternative.delete()
        messages.success(request, f"Alternativa «{name}» eliminada.")
        return redirect("product_detail", pk=product.pk)
    return render(
        request,
        "wishlist/confirm_delete.html",
        {
            "title": "Eliminar alternativa",
            "object_name": alternative.name,
            "detail": "La alternativa se eliminará definitivamente.",
            "back_url": "product_detail",
            "back_arg": product.pk,
            "delete_url": "alternative_delete",
            "delete_arg": [product.pk, alternative.pk],
        },
    )


# ---------------------------------------------------------------------------
# Revisiones y precios
# ---------------------------------------------------------------------------


def review_create(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.save()
            messages.success(request, "Revisión guardada.")
            return redirect("product_detail", pk=product.pk)
    else:
        form = ReviewForm()
    return render(
        request,
        "wishlist/review_form.html",
        {"form": form, "product": product},
    )


@require_POST
def price_snapshot_create(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = PriceSnapshotForm(request.POST)
    if form.is_valid():
        snapshot = form.save(commit=False)
        snapshot.product = product
        snapshot.save()
        messages.success(request, "Precio registrado.")
    else:
        messages.error(request, "No se pudo registrar el precio.")
    return redirect("product_detail", pk=product.pk)


# ---------------------------------------------------------------------------
# Inventario
# ---------------------------------------------------------------------------


def inventory_list(request):
    items = OwnedItem.objects.all()
    category = request.GET.get("category", "")
    if category:
        items = items.filter(category__iexact=category)
    categories = (
        OwnedItem.objects.exclude(category="")
        .values_list("category", flat=True)
        .distinct()
        .order_by("category")
    )
    return render(
        request,
        "wishlist/inventory_list.html",
        {"items": items, "categories": categories, "current_category": category},
    )


def inventory_create(request):
    if request.method == "POST":
        form = OwnedItemForm(request.POST)
        if form.is_valid():
            item = form.save()
            messages.success(request, f"Objeto «{item.name}» añadido al inventario.")
            return redirect("inventory_list")
    else:
        form = OwnedItemForm()
    return render(
        request,
        "wishlist/inventory_form.html",
        {"form": form, "title": "Nuevo objeto"},
    )


def inventory_edit(request, pk):
    item = get_object_or_404(OwnedItem, pk=pk)
    if request.method == "POST":
        form = OwnedItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f"Objeto «{item.name}» actualizado.")
            return redirect("inventory_list")
    else:
        form = OwnedItemForm(instance=item)
    return render(
        request,
        "wishlist/inventory_form.html",
        {"form": form, "title": f"Editar «{item.name}»", "item": item},
    )


def inventory_delete(request, pk):
    item = get_object_or_404(OwnedItem, pk=pk)
    if request.method == "POST":
        name = item.name
        item.delete()
        messages.success(request, f"Objeto «{name}» eliminado.")
        return redirect("inventory_list")
    return render(
        request,
        "wishlist/confirm_delete.html",
        {
            "title": "Eliminar objeto",
            "object_name": item.name,
            "detail": "El objeto se eliminará definitivamente del inventario.",
            "back_url": "inventory_list",
            "delete_url": "inventory_delete",
            "delete_arg": pk,
        },
    )


# ---------------------------------------------------------------------------
# Estadísticas
# ---------------------------------------------------------------------------


def stats(request):
    return render(
        request,
        "wishlist/stats.html",
        {"stats": compute_stats()},
    )
