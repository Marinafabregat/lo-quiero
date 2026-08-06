from django.contrib import admin

from .models import Alternative, DecisionReview, OwnedItem, PriceSnapshot, Product


class AlternativeInline(admin.TabularInline):
    model = Alternative
    extra = 0
    fields = [
        "name",
        "price",
        "similarity_score",
        "quality_score",
        "durability_score",
    ]


class ReviewInline(admin.TabularInline):
    model = DecisionReview
    extra = 0
    fields = [
        "need_score",
        "value_score",
        "interest_score",
        "expected_uses",
        "created_at",
    ]
    readonly_fields = ["created_at"]


class PriceSnapshotInline(admin.TabularInline):
    model = PriceSnapshot
    extra = 0
    fields = ["price", "recorded_at"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "status",
        "category",
        "priority",
        "current_price",
        "review_date",
        "days_remaining",
        "created_at",
    ]
    list_filter = ["status", "priority", "category", "created_at"]
    search_fields = ["name", "description", "reason", "category"]
    readonly_fields = [
        "created_at",
        "updated_at",
        "purchased_at",
        "discarded_at",
        "days_remaining",
        "days_stored",
    ]
    fieldsets = (
        (
            "Datos básicos",
            {"fields": ("name", "description", "url", "image_url")},
        ),
        (
            "Precios",
            {"fields": ("current_price", "target_price")},
        ),
        (
            "Decisión",
            {
                "fields": (
                    "category",
                    "reason",
                    "priority",
                    "status",
                    "waiting_days",
                    "review_date",
                )
            },
        ),
        (
            "Fechas",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                    "purchased_at",
                    "discarded_at",
                    "days_stored",
                    "days_remaining",
                )
            },
        ),
    )
    inlines = [AlternativeInline, ReviewInline, PriceSnapshotInline]


@admin.register(Alternative)
class AlternativeAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "product",
        "price",
        "similarity_score",
        "quality_score",
        "durability_score",
        "is_second_hand",
    ]
    list_filter = ["is_second_hand", "product"]
    search_fields = ["name", "notes", "product__name"]


@admin.register(DecisionReview)
class DecisionReviewAdmin(admin.ModelAdmin):
    list_display = [
        "product",
        "need_score",
        "value_score",
        "interest_score",
        "expected_uses",
        "created_at",
    ]
    list_filter = ["created_at"]
    search_fields = ["product__name", "notes"]
    readonly_fields = ["created_at"]


@admin.register(OwnedItem)
class OwnedItemAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "category",
        "condition",
        "usage_frequency",
        "purchase_date",
        "last_used_at",
    ]
    list_filter = ["category", "condition", "usage_frequency"]
    search_fields = ["name", "description", "notes", "category"]


@admin.register(PriceSnapshot)
class PriceSnapshotAdmin(admin.ModelAdmin):
    list_display = ["product", "price", "recorded_at"]
    list_filter = ["recorded_at"]
    search_fields = ["product__name"]
    readonly_fields = ["recorded_at"]
