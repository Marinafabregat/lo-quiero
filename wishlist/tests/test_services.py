from datetime import date
from decimal import Decimal

from django.test import SimpleTestCase

from wishlist.models import Alternative
from wishlist.services import (
    combined_score,
    compute_review_date,
    price_comparison,
    purchase_recommendation,
    suggested_waiting_days,
)


class SuggestedWaitingDaysTests(SimpleTestCase):
    def test_negative_price_is_invalid(self):
        with self.assertRaises(ValueError):
            suggested_waiting_days(Decimal("-1"))

    def test_none_price_uses_minimum(self):
        self.assertEqual(suggested_waiting_days(None), 7)

    def test_below_15_euros_is_7_days(self):
        self.assertEqual(suggested_waiting_days(Decimal("14.99")), 7)

    def test_15_to_35_euros_is_15_days(self):
        self.assertEqual(suggested_waiting_days(Decimal("15.00")), 15)
        self.assertEqual(suggested_waiting_days(Decimal("34.99")), 15)

    def test_35_to_50_euros_is_30_days(self):
        self.assertEqual(suggested_waiting_days(Decimal("35.00")), 30)
        self.assertEqual(suggested_waiting_days(Decimal("49.99")), 30)

    def test_50_or_more_is_45_days(self):
        self.assertEqual(suggested_waiting_days(Decimal("50.00")), 45)
        self.assertEqual(suggested_waiting_days(Decimal("349.00")), 45)


class ComputeReviewDateTests(SimpleTestCase):
    def test_adds_days_to_reference_date(self):
        self.assertEqual(
            compute_review_date(date(2026, 1, 1), 15),
            date(2026, 1, 16),
        )

    def test_zero_days(self):
        self.assertEqual(
            compute_review_date(date(2026, 1, 1), 0),
            date(2026, 1, 1),
        )

    def test_negative_days_is_invalid(self):
        with self.assertRaises(ValueError):
            compute_review_date(date(2026, 1, 1), -1)


class PurchaseRecommendationTests(SimpleTestCase):
    def test_high_need_and_high_interest(self):
        rec = purchase_recommendation(8, 8)
        self.assertEqual(rec.label, "Considerar compra")
        self.assertEqual(rec.code, "considerar")

    def test_high_need_and_low_interest(self):
        rec = purchase_recommendation(8, 4)
        self.assertEqual(rec.label, "Buscar una alternativa")
        self.assertEqual(rec.code, "alternativa")

    def test_low_need_and_high_interest(self):
        rec = purchase_recommendation(4, 8)
        self.assertEqual(rec.label, "Esperar: puede ser un capricho")
        self.assertEqual(rec.code, "esperar")

    def test_low_need_and_low_interest(self):
        rec = purchase_recommendation(4, 4)
        self.assertEqual(rec.label, "Descartar")
        self.assertEqual(rec.code, "descartar")

    def test_boundary_scores_are_high_at_7(self):
        rec = purchase_recommendation(7, 7)
        self.assertEqual(rec.label, "Considerar compra")

    def test_scores_must_be_between_1_and_10(self):
        with self.assertRaises(ValueError):
            purchase_recommendation(0, 5)
        with self.assertRaises(ValueError):
            purchase_recommendation(5, 11)


class PriceComparisonTests(SimpleTestCase):
    def test_savings_when_alternative_is_cheaper(self):
        difference, savings = price_comparison(Decimal("100.00"), Decimal("75.00"))
        self.assertEqual(difference, Decimal("-25.00"))
        self.assertEqual(savings, Decimal("25.00"))

    def test_difference_when_alternative_is_dearer(self):
        difference, savings = price_comparison(Decimal("100.00"), Decimal("120.00"))
        self.assertEqual(difference, Decimal("20.00"))
        self.assertEqual(savings, Decimal("-20.00"))

    def test_no_percent_when_product_price_is_zero(self):
        difference, savings = price_comparison(Decimal("0"), Decimal("5.00"))
        self.assertEqual(difference, Decimal("5.00"))
        self.assertIsNone(savings)

    def test_no_comparison_without_prices(self):
        self.assertEqual(
            price_comparison(None, Decimal("5.00")),
            (None, None),
        )
        self.assertEqual(
            price_comparison(Decimal("5.00"), None),
            (None, None),
        )

    def test_equal_prices(self):
        difference, savings = price_comparison(Decimal("50.00"), Decimal("50.00"))
        self.assertEqual(difference, Decimal("0.00"))
        self.assertEqual(savings, Decimal("0.00"))


class CombinedScoreTests(SimpleTestCase):
    def test_combined_score_formula(self):
        alternative = Alternative(
            similarity_score=80,
            quality_score=8,
            durability_score=6,
        )
        expected = (
            Decimal("0.4") * Decimal("8")
            + Decimal("0.35") * Decimal("8")
            + Decimal("0.25") * Decimal("6")
        )
        self.assertEqual(combined_score(alternative), expected)
