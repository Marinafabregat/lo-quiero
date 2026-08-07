from decimal import Decimal

from django.test import TestCase

from wishlist.forms import (
    AlternativeForm,
    AppSettingsForm,
    PriceSnapshotForm,
    ProductForm,
    ReviewForm,
)
from wishlist.models import Product


def product_form_data(**overrides):
    data = {
        "name": "Auriculares",
        "url": "",
        "image_url": "",
        "current_price": "100.00",
        "target_price": "",
        "category": "Auriculares",
        "reason": "Porque los necesito",
        "priority": Product.Priority.MEDIUM,
        "waiting_days": "",
        "status": Product.Status.WAITING,
    }
    data.update(overrides)
    return data


class ProductFormTests(TestCase):
    def test_valid_form_creates_product(self):
        form = ProductForm(data=product_form_data())
        self.assertTrue(form.is_valid(), form.errors)
        product = form.save()
        self.assertEqual(product.name, "Auriculares")

    def test_negative_price_is_rejected(self):
        form = ProductForm(data=product_form_data(current_price="-5.00"))
        self.assertFalse(form.is_valid())
        self.assertIn("current_price", form.errors)

    def test_negative_target_price_is_rejected(self):
        form = ProductForm(
            data=product_form_data(current_price="50.00", target_price="-1")
        )
        self.assertFalse(form.is_valid())
        self.assertIn("target_price", form.errors)

    def test_waiting_days_auto_suggested_from_price(self):
        form = ProductForm(data=product_form_data(current_price="100.00"))
        self.assertTrue(form.is_valid(), form.errors)
        product = form.save()
        self.assertEqual(product.waiting_days, 45)

    def test_manual_waiting_days_is_respected(self):
        form = ProductForm(
            data=product_form_data(current_price="100.00", waiting_days="10")
        )
        self.assertTrue(form.is_valid(), form.errors)
        product = form.save()
        self.assertEqual(product.waiting_days, 10)

    def test_new_product_with_waiting_period_starts_waiting(self):
        form = ProductForm(
            data=product_form_data(current_price="100.00", status=Product.Status.NEW)
        )
        self.assertTrue(form.is_valid(), form.errors)
        product = form.save()
        self.assertEqual(product.status, Product.Status.WAITING)

    def test_edit_keeps_chosen_status(self):
        product = Product.objects.create(
            name="Auriculares",
            current_price=Decimal("100.00"),
            status=Product.Status.COMPARING,
        )
        form = ProductForm(
            data=product_form_data(
                name="Auriculares nuevos",
                current_price="100.00",
                waiting_days="45",
                status=Product.Status.COMPARING,
            ),
            instance=product,
        )
        self.assertTrue(form.is_valid(), form.errors)
        product = form.save()
        self.assertEqual(product.status, Product.Status.COMPARING)

    def test_invalid_url_is_rejected(self):
        form = ProductForm(data=product_form_data(url="no-es-una-url"))
        self.assertFalse(form.is_valid())
        self.assertIn("url", form.errors)


class ProductCategoryFormTests(TestCase):
    def setUp(self):
        Product.objects.create(name="Mochila", category="Mochilas")

    def test_dropdown_includes_existing_categories(self):
        form = ProductForm()
        choices = [value for value, _ in form.fields["category"].widget.choices]
        self.assertIn("Mochilas", choices)

    def test_dropdown_includes_create_option(self):
        form = ProductForm()
        choices = [value for value, _ in form.fields["category"].widget.choices]
        self.assertIn("__new__", choices)

    def test_creating_new_category(self):
        form = ProductForm(
            data=product_form_data(category="__new__", new_category="Herramientas")
        )
        self.assertTrue(form.is_valid(), form.errors)
        product = form.save()
        self.assertEqual(product.category, "Herramientas")

    def test_new_category_requires_a_name(self):
        form = ProductForm(data=product_form_data(category="__new__"))
        self.assertFalse(form.is_valid())
        self.assertIn("new_category", form.errors)

    def test_existing_category_is_kept(self):
        form = ProductForm(data=product_form_data(category="Mochilas"))
        self.assertTrue(form.is_valid(), form.errors)
        product = form.save()
        self.assertEqual(product.category, "Mochilas")

    def test_current_category_included_when_editing(self):
        product = Product.objects.create(name="Taladro", category="Herramientas")
        form = ProductForm(instance=product)
        choices = [value for value, _ in form.fields["category"].widget.choices]
        self.assertIn("Herramientas", choices)


class AlternativeFormTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name="Auriculares")

    def alternative_data(self, **overrides):
        data = {
            "name": "Dupes baratos",
            "url": "",
            "image_url": "",
            "price": "30.00",
            "similarity_score": "80",
            "quality_score": "6",
            "durability_score": "5",
            "warranty_months": "12",
            "is_second_hand": False,
            "notes": "",
        }
        data.update(overrides)
        return data

    def test_valid_alternative(self):
        form = AlternativeForm(data=self.alternative_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_similarity_out_of_range_is_rejected(self):
        form = AlternativeForm(data=self.alternative_data(similarity_score="120"))
        self.assertFalse(form.is_valid())
        self.assertIn("similarity_score", form.errors)

    def test_quality_out_of_range_is_rejected(self):
        form = AlternativeForm(data=self.alternative_data(quality_score="11"))
        self.assertFalse(form.is_valid())
        self.assertIn("quality_score", form.errors)

    def test_negative_price_is_rejected(self):
        form = AlternativeForm(data=self.alternative_data(price="-10.00"))
        self.assertFalse(form.is_valid())
        self.assertIn("price", form.errors)


class ReviewFormTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name="Auriculares")

    def review_data(self, **overrides):
        data = {
            "need_score": "8",
            "interest_score": "9",
            "notes": "",
            "q1": "Me aíslo del ruido",
            "q2": "No",
            "q3": "A diario",
            "q4": "Sí",
            "q5": "Sí",
            "q6": "Creo que sí",
            "q7": "Seguiría con ruido",
            "q8": "En mi escritorio",
            "q9": "Trabajo mejor",
            "q10": "El precio",
        }
        data.update(overrides)
        return data

    def test_valid_review_saves_structured_answers(self):
        form = ReviewForm(data=self.review_data())
        self.assertTrue(form.is_valid(), form.errors)
        review = form.save(commit=False)
        review.product = self.product
        review.save()
        self.assertEqual(review.answers["q1"]["answer"], "Me aíslo del ruido")
        self.assertEqual(
            review.answers["q1"]["label"], "¿Qué problema concreto resuelve?"
        )

    def test_need_score_out_of_range_is_rejected(self):
        form = ReviewForm(data=self.review_data(need_score="0"))
        self.assertFalse(form.is_valid())
        self.assertIn("need_score", form.errors)

    def test_interest_score_out_of_range_is_rejected(self):
        form = ReviewForm(data=self.review_data(interest_score="11"))
        self.assertFalse(form.is_valid())
        self.assertIn("interest_score", form.errors)

    def test_reviews_are_not_overwritten(self):
        form = ReviewForm(data=self.review_data())
        self.assertTrue(form.is_valid(), form.errors)
        first = form.save(commit=False)
        first.product = self.product
        first.save()
        form2 = ReviewForm(data=self.review_data(need_score="3"))
        self.assertTrue(form2.is_valid(), form2.errors)
        second = form2.save(commit=False)
        second.product = self.product
        second.save()
        self.assertEqual(self.product.reviews.count(), 2)


class PriceSnapshotFormTests(TestCase):
    def test_negative_price_is_rejected(self):
        form = PriceSnapshotForm(data={"price": "-1"})
        self.assertFalse(form.is_valid())
        self.assertIn("price", form.errors)

    def test_valid_price(self):
        form = PriceSnapshotForm(data={"price": "25.50"})
        self.assertTrue(form.is_valid(), form.errors)


class AppSettingsFormTests(TestCase):
    def settings_data(self, **overrides):
        data = {
            "price_tier_1": "15.00",
            "waiting_days_1": "7",
            "price_tier_2": "35.00",
            "waiting_days_2": "15",
            "price_tier_3": "50.00",
            "waiting_days_3": "30",
            "waiting_days_max": "45",
        }
        data.update(overrides)
        return data

    def test_valid_settings(self):
        form = AppSettingsForm(data=self.settings_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_non_increasing_tiers_are_rejected(self):
        form = AppSettingsForm(
            data=self.settings_data(price_tier_2="10.00", price_tier_3="20.00")
        )
        self.assertFalse(form.is_valid())
        self.assertIn("price_tier_3", form.errors)

    def test_equal_tiers_are_rejected(self):
        form = AppSettingsForm(
            data=self.settings_data(price_tier_1="15.00", price_tier_2="15.00")
        )
        self.assertFalse(form.is_valid())

    def test_negative_days_are_rejected(self):
        form = AppSettingsForm(data=self.settings_data(waiting_days_1="-1"))
        self.assertFalse(form.is_valid())
        self.assertIn("waiting_days_1", form.errors)
