from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from wishlist.models import Alternative, DecisionReview, Product


class ProductModelTests(TestCase):
    def test_creation_sets_review_date_from_waiting_days(self):
        product = Product.objects.create(
            name="Auriculares",
            current_price=Decimal("100.00"),
            waiting_days=15,
        )
        self.assertEqual(
            product.review_date,
            timezone.localdate() + timedelta(days=15),
        )

    def test_creation_keeps_manual_review_date(self):
        review_date = timezone.localdate() + timedelta(days=30)
        product = Product.objects.create(
            name="Mochila",
            review_date=review_date,
            waiting_days=7,
        )
        product.refresh_from_db()
        self.assertEqual(product.review_date, review_date)

    def test_days_remaining_never_negative(self):
        product = Product.objects.create(
            name="Producto",
            review_date=timezone.localdate() - timedelta(days=5),
        )
        self.assertEqual(product.days_remaining, 0)

    def test_days_remaining_positive(self):
        product = Product.objects.create(
            name="Producto",
            review_date=timezone.localdate() + timedelta(days=5),
        )
        self.assertEqual(product.days_remaining, 5)

    def test_is_due_for_review(self):
        product = Product.objects.create(
            name="Producto",
            review_date=timezone.localdate() - timedelta(days=1),
        )
        self.assertTrue(product.is_due_for_review)

    def test_not_due_when_review_in_future(self):
        product = Product.objects.create(
            name="Producto",
            review_date=timezone.localdate() + timedelta(days=1),
        )
        self.assertFalse(product.is_due_for_review)

    def test_mark_as_purchased(self):
        product = Product.objects.create(name="Ratón")
        product.mark_as_purchased()
        product.refresh_from_db()
        self.assertEqual(product.status, Product.Status.PURCHASED)
        self.assertIsNotNone(product.purchased_at)
        self.assertIsNone(product.discarded_at)

    def test_mark_as_discarded(self):
        product = Product.objects.create(name="Ratón")
        product.mark_as_discarded()
        product.refresh_from_db()
        self.assertEqual(product.status, Product.Status.DISCARDED)
        self.assertIsNotNone(product.discarded_at)
        self.assertIsNone(product.purchased_at)

    def test_postpone_moves_review_date(self):
        product = Product.objects.create(name="Teclado", waiting_days=7)
        product.postpone(30)
        product.refresh_from_db()
        self.assertEqual(
            product.review_date,
            timezone.localdate() + timedelta(days=30),
        )

    def test_last_review_returns_newest(self):
        product = Product.objects.create(name="Auriculares")
        DecisionReview.objects.create(product=product, need_score=5, interest_score=5)
        newest = DecisionReview.objects.create(
            product=product, need_score=9, interest_score=9
        )
        self.assertEqual(product.last_review().pk, newest.pk)


class AlternativeModelTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name="Auriculares")

    def test_alternative_related_to_product(self):
        alt = Alternative.objects.create(
            product=self.product,
            name="Alternativa",
            similarity_score=80,
            quality_score=7,
            durability_score=6,
        )
        self.assertIn(alt, self.product.alternatives.all())

    def test_default_warranty_is_zero_months(self):
        alt = Alternative.objects.create(
            product=self.product,
            name="Alternativa",
            similarity_score=80,
            quality_score=7,
            durability_score=6,
        )
        self.assertEqual(alt.warranty_months, 0)
