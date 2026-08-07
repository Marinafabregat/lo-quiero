"""Reasigna a «comparando» los productos con el estado eliminado «possible_purchase»."""

from django.db import migrations


def move_possible_purchase_to_comparing(apps, schema_editor):
    Product = apps.get_model("wishlist", "Product")
    Product.objects.filter(status="possible_purchase").update(status="comparing")


class Migration(migrations.Migration):
    dependencies = [
        ("wishlist", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            move_possible_purchase_to_comparing,
            migrations.RunPython.noop,
        ),
    ]
