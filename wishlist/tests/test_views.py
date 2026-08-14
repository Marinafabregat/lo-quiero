from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from wishlist.models import (
    Alternative,
    AppSettings,
    DecisionReview,
    OwnedItem,
    Product,
)


class DashboardTests(TestCase):
    def test_dashboard_loads_when_empty(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Todavía no has añadido ningún producto")

    def test_dashboard_shows_products_grouped(self):
        Product.objects.create(name="En espera", status=Product.Status.WAITING)
        Product.objects.create(name="Comprado", status=Product.Status.PURCHASED)
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "En espera")
        self.assertContains(response, "Comprado")


class ProductViewTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Auriculares",
            current_price=Decimal("100.00"),
            category="Auriculares",
        )

    def test_product_list_page(self):
        response = self.client.get(reverse("product_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Auriculares")

    def test_product_detail_page(self):
        response = self.client.get(reverse("product_detail", args=[self.product.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Auriculares")

    def test_create_product(self):
        response = self.client.post(
            reverse("product_create"),
            {
                "name": "Mochila",
                "url": "",
                "image_url": "",
                "current_price": "45.00",
                "target_price": "",
                "category": "Mochilas",
                "reason": "La necesito",
                "priority": "medium",
                "waiting_days": "",
                "status": "waiting",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Product.objects.filter(name="Mochila", waiting_days=30).exists()
        )

    def test_edit_product(self):
        response = self.client.post(
            reverse("product_edit", args=[self.product.pk]),
            {
                "name": "Auriculares nuevos",
                "url": "",
                "image_url": "",
                "current_price": "120.00",
                "target_price": "",
                "category": "Auriculares",
                "reason": "",
                "priority": "high",
                "waiting_days": "45",
                "status": "waiting",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, "Auriculares nuevos")

    def test_delete_product_requires_confirmation(self):
        response = self.client.post(reverse("product_delete", args=[self.product.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())

    def test_mark_as_purchased(self):
        response = self.client.post(reverse("product_purchase", args=[self.product.pk]))
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.status, Product.Status.PURCHASED)

    def test_mark_as_discarded(self):
        response = self.client.post(reverse("product_discard", args=[self.product.pk]))
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.status, Product.Status.DISCARDED)

    def test_postpone_review(self):
        response = self.client.post(
            reverse("product_postpone", args=[self.product.pk]), {"days": 30}
        )
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(
            self.product.review_date,
            timezone.localdate() + timedelta(days=30),
        )

    def test_postpone_review_clamps_overflow_days(self):
        response = self.client.post(
            reverse("product_postpone", args=[self.product.pk]),
            {"days": "999999999999"},
        )
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(
            self.product.review_date,
            timezone.localdate() + timedelta(days=3650),
        )

    def test_postpone_review_invalid_days_defaults(self):
        response = self.client.post(
            reverse("product_postpone", args=[self.product.pk]), {"days": "abc"}
        )
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(
            self.product.review_date,
            timezone.localdate() + timedelta(days=7),
        )

    def test_detail_shows_recommendation_from_last_review(self):
        DecisionReview.objects.create(
            product=self.product,
            need_score=8,
            interest_score=9,
        )
        response = self.client.get(reverse("product_detail", args=[self.product.pk]))
        self.assertContains(response, "Considerar compra")

    def test_detail_shows_alternative_comparison(self):
        Alternative.objects.create(
            product=self.product,
            name="Alternativa barata",
            price=Decimal("50.00"),
            similarity_score=80,
            quality_score=7,
            durability_score=6,
        )
        response = self.client.get(reverse("product_detail", args=[self.product.pk]))
        self.assertContains(response, "Alternativa barata")
        self.assertContains(response, "Más barata")

    def test_detail_warns_about_owned_item_with_same_category(self):
        OwnedItem.objects.create(name="Auriculares viejos", category="Auriculares")
        response = self.client.get(reverse("product_detail", args=[self.product.pk]))
        self.assertContains(response, "Ya tienes algo similar")


class ReviewAndAlternativeViewsTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name="Auriculares")

    def test_create_review(self):
        response = self.client.post(
            reverse("review_create", args=[self.product.pk]),
            {
                "need_score": "8",
                "interest_score": "9",
                "notes": "",
                "q1": "Respuesta",
                "q2": "",
                "q3": "",
                "q4": "",
                "q5": "",
                "q6": "",
                "q7": "",
                "q8": "",
                "q9": "",
                "q10": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.product.reviews.count(), 1)

    def test_review_with_invalid_scores_is_rejected(self):
        response = self.client.post(
            reverse("review_create", args=[self.product.pk]),
            {
                "need_score": "15",
                "interest_score": "9",
                "notes": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.product.reviews.count(), 0)

    def test_create_alternative(self):
        response = self.client.post(
            reverse("alternative_create", args=[self.product.pk]),
            {
                "name": "Dupes baratos",
                "url": "",
                "image_url": "",
                "price": "30.00",
                "similarity_score": "80",
                "quality_score": "6",
                "durability_score": "5",
                "warranty_months": "12",
                "is_second_hand": "on",
                "notes": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.product.alternatives.count(), 1)


class StatsViewTests(TestCase):
    def test_stats_page_without_data(self):
        response = self.client.get(reverse("stats"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Todavía no hay datos suficientes")

    def test_stats_page_with_data(self):
        purchased = Product.objects.create(
            name="Comprado",
            status=Product.Status.PURCHASED,
            current_price=Decimal("99.00"),
            purchased_at=timezone.now() - timedelta(days=10),
        )
        discarded = Product.objects.create(
            name="Descartado",
            status=Product.Status.DISCARDED,
            current_price=Decimal("40.00"),
            discarded_at=timezone.now() - timedelta(days=5),
        )
        Product.objects.filter(pk=purchased.pk).update(
            created_at=timezone.now() - timedelta(days=20)
        )
        Product.objects.filter(pk=discarded.pk).update(
            created_at=timezone.now() - timedelta(days=15)
        )
        response = self.client.get(reverse("stats"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "99,00")
        self.assertContains(response, "40,00")
        self.assertContains(response, "10,0")
        self.assertContains(response, "50,0")


class InventoryViewsTests(TestCase):
    def test_inventory_list_empty(self):
        response = self.client.get(reverse("inventory_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tu inventario está vacío")

    def test_inventory_create(self):
        response = self.client.post(
            reverse("inventory_create"),
            {
                "name": "Auriculares con cable",
                "category": "Auriculares",
                "description": "",
                "url": "https://example.com/auriculares",
                "image_url": "https://example.com/auriculares.jpg",
                "purchase_date": "2025-01-01",
                "notes": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(OwnedItem.objects.filter(name="Auriculares con cable").exists())

    def test_inventory_list_shows_items(self):
        OwnedItem.objects.create(name="Auriculares con cable")
        response = self.client.get(reverse("inventory_list"))
        self.assertContains(response, "Auriculares con cable")

    def test_inventory_list_shows_replacement_and_products(self):
        producto = Product.objects.create(name="Auriculares inalámbricos")
        OwnedItem.objects.create(name="Auriculares con cable")
        OwnedItem.objects.create(name="Altavoz", replacement=producto)
        response = self.client.get(reverse("inventory_list"))
        self.assertContains(response, "Auriculares inalámbricos")
        self.assertContains(response, "Comprar de nuevo")

    def test_inventory_set_replacement(self):
        producto = Product.objects.create(name="Auriculares inalámbricos")
        item = OwnedItem.objects.create(name="Auriculares con cable")
        response = self.client.post(
            reverse("inventory_set_replacement", args=[item.pk]),
            {"replacement": producto.pk},
        )
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.replacement, producto)
        self.assertFalse(item.buy_again)

    def test_inventory_clear_replacement(self):
        producto = Product.objects.create(name="Auriculares inalámbricos")
        item = OwnedItem.objects.create(
            name="Auriculares con cable", replacement=producto
        )
        response = self.client.post(
            reverse("inventory_set_replacement", args=[item.pk]),
            {"replacement": ""},
        )
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertIsNone(item.replacement)
        self.assertFalse(item.buy_again)

    def test_inventory_set_replacement_invalid_pk(self):
        item = OwnedItem.objects.create(name="Auriculares con cable")
        response = self.client.post(
            reverse("inventory_set_replacement", args=[item.pk]),
            {"replacement": "abc"},
        )
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertIsNone(item.replacement)
        self.assertFalse(item.buy_again)

    def test_inventory_buy_again_marks_item(self):
        item = OwnedItem.objects.create(
            name="Mochila de trekking",
            category="Mochilas",
            url="https://example.com/mochila",
            image_url="https://example.com/mochila.jpg",
        )
        response = self.client.post(
            reverse("inventory_set_replacement", args=[item.pk]),
            {"buy_again": "on"},
        )
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertTrue(item.buy_again)
        self.assertIsNone(item.replacement)
        self.assertFalse(Product.objects.filter(name="Mochila de trekking").exists())


class PageAccessTests(TestCase):
    def test_main_pages_are_accessible(self):
        Product.objects.create(name="Algo")
        for url in [
            reverse("dashboard"),
            reverse("product_list"),
            reverse("product_create"),
            reverse("inventory_list"),
            reverse("inventory_create"),
            reverse("stats"),
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)


class ErrorPageTests(TestCase):
    @override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"])
    def test_unknown_url_returns_custom_404(self):
        response = self.client.get("/ruta-que-no-existe/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Página no encontrada", status_code=404)

    @override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"])
    def test_unknown_product_returns_custom_404(self):
        response = self.client.get(reverse("product_detail", args=[99999]))
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Página no encontrada", status_code=404)

    @override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"])
    def test_custom_404_offers_link_back(self):
        response = self.client.get("/no-existe/")
        self.assertContains(response, "Volver al panel", status_code=404)


class CategoryManagementTests(TestCase):
    def setUp(self):
        self.mochila = Product.objects.create(name="Mochila", category="Mochilas")
        self.bolso = Product.objects.create(name="Bolso", category="Mochilas")
        Product.objects.create(name="Auriculares", category="Auriculares")
        OwnedItem.objects.create(name="Crema facial", category="Skincare")

    def test_manage_page_lists_categories(self):
        response = self.client.get(reverse("category_manage"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mochilas")
        self.assertContains(response, "Auriculares")

    def test_manage_page_lists_inventory_categories(self):
        response = self.client.get(reverse("category_manage"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Skincare")

    def test_manage_page_accessible_when_empty(self):
        Product.objects.all().delete()
        OwnedItem.objects.all().delete()
        response = self.client.get(reverse("category_manage"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No hay categorías")

    def test_rename_category_updates_products_and_owned_items(self):
        OwnedItem.objects.create(name="Mochila pequeña", category="Mochilas")
        response = self.client.post(
            reverse("category_rename", args=["Mochilas"]),
            {"name": "Equipaje"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Product.objects.filter(category="Equipaje").count(), 2)
        self.assertFalse(Product.objects.filter(category="Mochilas").exists())
        self.assertEqual(OwnedItem.objects.filter(category="Equipaje").count(), 1)
        self.assertFalse(OwnedItem.objects.filter(category="Mochilas").exists())

    def test_rename_to_same_name_is_a_noop(self):
        response = self.client.post(
            reverse("category_rename", args=["Mochilas"]),
            {"name": "Mochilas"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Product.objects.filter(category="Mochilas").count(), 2)

    def test_delete_confirm_page_shows_category(self):
        response = self.client.get(reverse("category_delete", args=["Mochilas"]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mochilas")

    def test_delete_category_keeps_products_and_owned_items(self):
        OwnedItem.objects.create(name="Mochila pequeña", category="Mochilas")
        response = self.client.post(reverse("category_delete", args=["Mochilas"]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Product.objects.count(), 3)
        self.assertEqual(Product.objects.filter(category="").count(), 2)
        self.assertEqual(OwnedItem.objects.count(), 2)
        self.assertEqual(OwnedItem.objects.filter(category="").count(), 1)

    def test_delete_unused_category(self):
        Product.objects.create(name="Gadget", category="Gadgets")
        response = self.client.post(reverse("category_delete", args=["Gadgets"]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Product.objects.count(), 4)
        self.assertFalse(Product.objects.filter(category="Gadgets").exists())


class SettingsViewTests(TestCase):
    def test_settings_page_renders(self):
        response = self.client.get(reverse("settings"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Periodo de reflexión")

    def test_settings_page_lists_categories(self):
        Product.objects.create(name="Mochila", category="Mochilas")
        response = self.client.get(reverse("settings"))
        self.assertContains(response, "Mochilas")

    def test_settings_page_lists_inventory_categories(self):
        OwnedItem.objects.create(name="Crema facial", category="Skincare")
        response = self.client.get(reverse("settings"))
        self.assertContains(response, "Skincare")

    def test_save_settings(self):
        response = self.client.post(
            reverse("settings"),
            {
                "price_tier_1": "20.00",
                "waiting_days_1": "10",
                "price_tier_2": "40.00",
                "waiting_days_2": "20",
                "price_tier_3": "60.00",
                "waiting_days_3": "30",
                "waiting_days_max": "60",
            },
        )
        self.assertRedirects(response, reverse("settings"))
        settings = AppSettings.load()
        self.assertEqual(settings.price_tier_1, Decimal("20.00"))
        self.assertEqual(settings.waiting_days_1, 10)
        self.assertEqual(settings.waiting_days_max, 60)

    def test_save_settings_rejects_non_increasing_tiers(self):
        response = self.client.post(
            reverse("settings"),
            {
                "price_tier_1": "50.00",
                "waiting_days_1": "10",
                "price_tier_2": "40.00",
                "waiting_days_2": "20",
                "price_tier_3": "60.00",
                "waiting_days_3": "30",
                "waiting_days_max": "60",
            },
        )
        self.assertEqual(response.status_code, 200)
        settings = AppSettings.load()
        self.assertEqual(settings.price_tier_1, Decimal("15.00"))

    def test_rename_category_from_settings_returns_to_settings(self):
        Product.objects.create(name="Mochila", category="Mochilas")
        response = self.client.post(
            reverse("category_rename", args=["Mochilas"]),
            {"name": "Equipaje", "next": "settings"},
        )
        self.assertRedirects(response, reverse("settings"))
        self.assertEqual(Product.objects.filter(category="Equipaje").count(), 1)

    def test_delete_category_from_settings_returns_to_settings(self):
        Product.objects.create(name="Mochila", category="Mochilas")
        response = self.client.post(
            reverse("category_delete", args=["Mochilas"]),
            {"next": "settings"},
        )
        self.assertRedirects(response, reverse("settings"))
        self.assertEqual(Product.objects.filter(category="").count(), 1)

    def test_confirm_delete_from_settings_keeps_next(self):
        Product.objects.create(name="Mochila", category="Mochilas")
        response = self.client.get(
            reverse("category_delete", args=["Mochilas"]), {"next": "settings"}
        )
        self.assertContains(response, 'name="next" value="settings"')
