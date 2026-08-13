"""Categorías globales compartidas entre productos e inventario."""

from django.db.models import Count

from .models import OwnedItem, Product


def all_categories():
    """Nombres de todas las categorías en uso (productos e inventario), ordenados."""
    names = set(
        Product.objects.exclude(category="")
        .values_list("category", flat=True)
        .distinct()
    )
    names.update(
        OwnedItem.objects.exclude(category="")
        .values_list("category", flat=True)
        .distinct()
    )
    return sorted(names, key=str.lower)


def categories_with_counts():
    """Cada categoría con cuántos productos y objetos la usan."""
    product_counts = {
        row["category"]: row["count"]
        for row in (
            Product.objects.exclude(category="")
            .values("category")
            .annotate(count=Count("id"))
        )
    }
    owned_counts = {
        row["category"]: row["count"]
        for row in (
            OwnedItem.objects.exclude(category="")
            .values("category")
            .annotate(count=Count("id"))
        )
    }
    return [
        {
            "category": name,
            "products": product_counts.get(name, 0),
            "owned": owned_counts.get(name, 0),
        }
        for name in sorted(set(product_counts) | set(owned_counts), key=str.lower)
    ]


def rename_category(old_name, new_name):
    """Renombra una categoría en productos e inventario.

    Devuelve una tupla (productos, objetos) con los registros afectados.
    """
    product_count = Product.objects.filter(category=old_name).update(category=new_name)
    owned_count = OwnedItem.objects.filter(category=old_name).update(category=new_name)
    return product_count, owned_count


def delete_category(name):
    """Elimina la categoría dejando sin etiqueta los registros que la usaban.

    Devuelve una tupla (productos, objetos) con los registros afectados.
    """
    product_count = Product.objects.filter(category=name).update(category="")
    owned_count = OwnedItem.objects.filter(category=name).update(category="")
    return product_count, owned_count
