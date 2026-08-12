from datetime import timedelta
from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Product(models.Model):
    """Producto que se está considerando comprar."""

    class Status(models.TextChoices):
        NEW = "new", "Nuevo"
        WAITING = "waiting", "En espera"
        COMPARING = "comparing", "Comparando"
        PURCHASED = "purchased", "Comprado"
        DISCARDED = "discarded", "Descartado"

    class Priority(models.TextChoices):
        LOW = "low", "Baja"
        MEDIUM = "medium", "Media"
        HIGH = "high", "Alta"

    name = models.CharField("nombre", max_length=200)
    description = models.TextField("descripción", blank=True)
    url = models.URLField("enlace", blank=True)
    image_url = models.URLField("URL de imagen", blank=True)

    current_price = models.DecimalField(
        "precio actual",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
    )
    target_price = models.DecimalField(
        "precio objetivo",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
    )

    category = models.CharField("categoría", max_length=100, blank=True)
    reason = models.TextField("motivo", blank=True)

    priority = models.CharField(
        "prioridad",
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )

    status = models.CharField(
        "estado",
        max_length=30,
        choices=Status.choices,
        default=Status.WAITING,
    )

    waiting_days = models.PositiveIntegerField("días de espera", default=7)

    review_date = models.DateField("fecha de revisión", null=True, blank=True)

    created_at = models.DateTimeField("creado", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado", auto_now=True)
    purchased_at = models.DateTimeField("comprado", null=True, blank=True)
    discarded_at = models.DateTimeField("descartado", null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "producto"
        verbose_name_plural = "productos"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new and self.review_date is None:
            self.review_date = timezone.localdate() + timedelta(days=self.waiting_days)
        super().save(*args, **kwargs)

    @property
    def days_remaining(self):
        """Días que faltan hasta la revisión (nunca negativos)."""
        if self.review_date is None:
            return None
        days = (self.review_date - timezone.localdate()).days
        return max(days, 0)

    @property
    def days_stored(self):
        """Días que lleva guardado en la lista."""
        return (timezone.localdate() - self.created_at.date()).days

    @property
    def is_due_for_review(self):
        """La fecha de revisión ya ha llegado y el producto sigue abierto."""
        if self.review_date is None:
            return False
        return self.review_date <= timezone.localdate() and self.status not in (
            self.Status.PURCHASED,
            self.Status.DISCARDED,
        )

    def last_review(self):
        return self.reviews.order_by("-created_at").first()

    def mark_as_purchased(self):
        self.status = self.Status.PURCHASED
        self.purchased_at = timezone.now()
        self.discarded_at = None
        self.save(
            update_fields=[
                "status",
                "purchased_at",
                "discarded_at",
                "updated_at",
            ]
        )

    def mark_as_discarded(self):
        self.status = self.Status.DISCARDED
        self.discarded_at = timezone.now()
        self.purchased_at = None
        self.save(
            update_fields=[
                "status",
                "discarded_at",
                "purchased_at",
                "updated_at",
            ]
        )

    def postpone(self, days):
        """Pospone la revisión `days` días a partir de hoy."""
        self.review_date = timezone.localdate() + timedelta(days=days)
        self.save(update_fields=["review_date", "updated_at"])


class Alternative(models.Model):
    """Alternativa o «dupe» de un producto."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="alternatives",
        verbose_name="producto",
    )
    name = models.CharField("nombre", max_length=200)
    url = models.URLField("enlace", blank=True)
    image_url = models.URLField("URL de imagen", blank=True)

    price = models.DecimalField(
        "precio",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
    )

    similarity_score = models.PositiveSmallIntegerField(
        "similitud",
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )
    quality_score = models.PositiveSmallIntegerField(
        "calidad",
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    durability_score = models.PositiveSmallIntegerField(
        "durabilidad",
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    warranty_months = models.PositiveIntegerField("garantía (meses)", default=0)
    is_second_hand = models.BooleanField("segunda mano", default=False)
    notes = models.TextField("notas", blank=True)

    created_at = models.DateTimeField("creado", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        ordering = ["price", "created_at"]
        verbose_name = "alternativa"
        verbose_name_plural = "alternativas"

    def __str__(self):
        return self.name


class DecisionReview(models.Model):
    """Revisión realizada durante el proceso de decisión.

    El historial es inmutable por diseño: cada revisión crea un registro
    nuevo y nunca se sobrescribe una anterior.
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="producto",
    )

    need_score = models.PositiveSmallIntegerField(
        "necesidad",
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    interest_score = models.PositiveSmallIntegerField(
        "interés",
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )

    answers = models.JSONField("respuestas", default=dict, blank=True)
    notes = models.TextField("notas", blank=True)

    created_at = models.DateTimeField("creado", auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "revisión"
        verbose_name_plural = "revisiones"

    def __str__(self):
        return f"Revisión de {self.product.name} ({self.created_at:%d/%m/%Y})"


class OwnedItem(models.Model):
    """Objeto que ya se posee y puede cubrir la misma necesidad."""

    name = models.CharField("nombre", max_length=200)
    category = models.CharField("categoría", max_length=100, blank=True)
    description = models.TextField("descripción", blank=True)
    url = models.URLField("web de compra", blank=True)
    image_url = models.URLField("URL de imagen", blank=True)

    purchase_date = models.DateField("fecha de compra", null=True, blank=True)
    notes = models.TextField("notas", blank=True)

    created_at = models.DateTimeField("creado", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "objeto"
        verbose_name_plural = "objetos"

    def __str__(self):
        return self.name


class PriceSnapshot(models.Model):
    """Historial de precios registrado manualmente."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="price_snapshots",
        verbose_name="producto",
    )
    price = models.DecimalField(
        "precio",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    recorded_at = models.DateTimeField("registrado", default=timezone.now)

    class Meta:
        ordering = ["recorded_at"]
        verbose_name = "precio"
        verbose_name_plural = "precios"

    def __str__(self):
        return f"{self.product.name}: {self.price}"


class AppSettings(models.Model):
    """Configuración global de la aplicación (una sola fila)."""

    price_tier_1 = models.DecimalField(
        "Umbral de precio bajo (€)",
        max_digits=10,
        decimal_places=2,
        default=Decimal("15.00"),
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    waiting_days_1 = models.PositiveSmallIntegerField(
        "Días de espera para precios bajos",
        default=7,
    )
    price_tier_2 = models.DecimalField(
        "Umbral de precio medio (€)",
        max_digits=10,
        decimal_places=2,
        default=Decimal("35.00"),
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    waiting_days_2 = models.PositiveSmallIntegerField(
        "Días de espera para precios medios",
        default=15,
    )
    price_tier_3 = models.DecimalField(
        "Umbral de precio alto (€)",
        max_digits=10,
        decimal_places=2,
        default=Decimal("50.00"),
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    waiting_days_3 = models.PositiveSmallIntegerField(
        "Días de espera para precios altos",
        default=30,
    )
    waiting_days_max = models.PositiveSmallIntegerField(
        "Días de espera para precios muy altos",
        default=45,
    )
    updated_at = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        verbose_name = "configuración"
        verbose_name_plural = "configuración"

    @classmethod
    def load(cls):
        """Devuelve la configuración única, creándola si no existe."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Configuración de la aplicación"
