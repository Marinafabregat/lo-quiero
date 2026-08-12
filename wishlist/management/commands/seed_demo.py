"""Datos de demostración para «¿Lo quiero?»."""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from wishlist.models import (
    Alternative,
    AppSettings,
    DecisionReview,
    OwnedItem,
    PriceSnapshot,
    Product,
)


class Command(BaseCommand):
    help = (
        "Añade datos ficticios de demostración sin duplicarlos. "
        "Usa --reset para borrar los actuales y volver a crearlos."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Borra los datos de demostración existentes antes de recrearlos.",
        )

    def handle(self, *args, **options):
        today = timezone.localdate()

        if options["reset"]:
            PriceSnapshot.objects.all().delete()
            DecisionReview.objects.all().delete()
            Alternative.objects.all().delete()
            OwnedItem.objects.all().delete()
            Product.objects.all().delete()
            AppSettings.objects.all().delete()
            self.stdout.write("  - Datos de demostración anteriores borrados.")

        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={"is_staff": True, "is_superuser": True, "email": ""},
        )
        if created:
            admin.set_password("admin")
            admin.save()
            self.stdout.write("  + Superusuario: admin (admin/admin)")

        AppSettings.load()
        self.stdout.write("  = Configuración por defecto (periodo de reflexión).")

        auriculares, created = Product.objects.get_or_create(
            name="Auriculares inalámbricos Sony WH-1000XM5",
            defaults={
                "description": (
                    "Auriculares de diadema con cancelación de ruido activa "
                    "y una batería de más de 30 horas."
                ),
                "url": "https://www.sony.es/electronics/auriculares/wh-1000xm5",
                "current_price": Decimal("349.00"),
                "target_price": Decimal("279.00"),
                "category": "Auriculares",
                "reason": (
                    "Los uso para trabajar y viajar, y los míos actuales "
                    "ya no aguantan la carga."
                ),
                "priority": Product.Priority.HIGH,
                "status": Product.Status.COMPARING,
                "waiting_days": 45,
                "review_date": today + timedelta(days=15),
            },
        )
        if created:
            self.stdout.write(f"  + Producto: {auriculares.name}")

        alt1, created = Alternative.objects.get_or_create(
            product=auriculares,
            name="Sony WH-CH720N",
            defaults={
                "url": "https://www.sony.es/electronics/auriculares/wh-ch720n",
                "price": Decimal("99.99"),
                "similarity_score": 80,
                "quality_score": 7,
                "durability_score": 7,
                "warranty_months": 24,
                "is_second_hand": False,
                "notes": "Más económica y con cancelación de ruido suficiente.",
            },
        )
        if created:
            self.stdout.write(f"  + Alternativa: {alt1.name}")

        alt2, created = Alternative.objects.get_or_create(
            product=auriculares,
            name="Anker Soundcore Q30 (segunda mano)",
            defaults={
                "price": Decimal("69.00"),
                "similarity_score": 75,
                "quality_score": 6,
                "durability_score": 5,
                "warranty_months": 0,
                "is_second_hand": True,
                "notes": "Reacondicionados, garantía de 6 meses del vendedor.",
            },
        )
        if created:
            self.stdout.write(f"  + Alternativa: {alt2.name}")

        if not auriculares.reviews.exists():
            DecisionReview.objects.create(
                product=auriculares,
                need_score=8,
                interest_score=9,
                answers={
                    "q1": {
                        "label": "¿Qué problema concreto resuelve?",
                        "answer": "Aislarme del ruido mientras trabajo.",
                    },
                    "q2": {
                        "label": "¿Ya tienes algo que haga lo mismo?",
                        "answer": "Sí, unos viejos que ya no cargan bien.",
                    },
                    "q3": {
                        "label": "¿Cuántas veces esperas utilizarlo?",
                        "answer": "A diario.",
                    },
                },
            )
            self.stdout.write("  + Revisión para auriculares")

        precios_auriculares = [
            (today - timedelta(days=60), Decimal("379.00")),
            (today - timedelta(days=30), Decimal("365.00")),
            (today - timedelta(days=7), Decimal("349.00")),
        ]
        if not auriculares.price_snapshots.exists():
            for dia, precio in precios_auriculares:
                PriceSnapshot.objects.create(
                    product=auriculares,
                    price=precio,
                    recorded_at=timezone.make_aware(
                        timezone.datetime.combine(dia, timezone.datetime.min.time())
                    ),
                )
            self.stdout.write("  + Historial de precios para auriculares")

        mochila, created = Product.objects.get_or_create(
            name="Mochila urbana impermeable 20L",
            defaults={
                "description": (
                    "Mochila para el día a día con funda impermeable "
                    "y hueco para portátil de 15 pulgadas."
                ),
                "current_price": Decimal("45.00"),
                "category": "Mochilas",
                "reason": "La actual está rota en una cremallera.",
                "priority": Product.Priority.MEDIUM,
                "status": Product.Status.WAITING,
                "waiting_days": 30,
                "review_date": today + timedelta(days=20),
            },
        )
        if created:
            self.stdout.write(f"  + Producto: {mochila.name}")

        teclado, created = Product.objects.get_or_create(
            name="Teclado mecánico Keychron K3",
            defaults={
                "description": "Teclado mecánico bajo perfil, conectividad Bluetooth.",
                "current_price": Decimal("89.00"),
                "category": "Teclados",
                "reason": "Me gustaría algo más compacto y silencioso.",
                "priority": Product.Priority.LOW,
                "status": Product.Status.WAITING,
                "waiting_days": 15,
                "review_date": today + timedelta(days=5),
            },
        )
        if created:
            self.stdout.write(f"  + Producto: {teclado.name}")

        if not mochila.reviews.exists():
            DecisionReview.objects.create(
                product=mochila,
                need_score=7,
                interest_score=6,
            )
            self.stdout.write("  + Revisión para la mochila")

        silla, created = Product.objects.get_or_create(
            name="Silla ergonómica de oficina",
            defaults={
                "description": (
                    "Silla con soporte lumbar y reposabrazos regulable, "
                    "para el teletrabajo diario."
                ),
                "url": "https://www.ikea.com/es/es/",
                "current_price": Decimal("199.00"),
                "target_price": Decimal("180.00"),
                "category": "Oficina",
                "reason": (
                    "Llevo dos años con una silla básica y noto molestias "
                    "de espalda al final del día."
                ),
                "priority": Product.Priority.HIGH,
                "status": Product.Status.COMPARING,
                "waiting_days": 45,
                "review_date": today + timedelta(days=2),
            },
        )
        if created:
            self.stdout.write(f"  + Producto: {silla.name}")

        if not silla.reviews.exists():
            DecisionReview.objects.create(
                product=silla,
                need_score=9,
                interest_score=8,
            )
            self.stdout.write("  + Revisión para la silla")

        descartado, created = Product.objects.get_or_create(
            name="Consola retro portátil",
            defaults={
                "description": "Consola para jugar a títulos clásicos.",
                "current_price": Decimal("120.00"),
                "category": "Ocio",
                "reason": "Nostalgia, sin tiempo real para usarla.",
                "priority": Product.Priority.LOW,
                "status": Product.Status.DISCARDED,
                "waiting_days": 30,
                "review_date": today - timedelta(days=10),
                "discarded_at": timezone.now() - timedelta(days=5),
            },
        )
        if created:
            DecisionReview.objects.create(
                product=descartado,
                need_score=2,
                interest_score=4,
            )
            self.stdout.write(f"  + Producto descartado: {descartado.name}")

        comprado, created = Product.objects.get_or_create(
            name="Ratón ergonómico Logitech MX Master 3S",
            defaults={
                "description": "Ratón ergonómico para uso diario en el trabajo.",
                "current_price": Decimal("99.00"),
                "category": "Informática",
                "reason": "El anterior me provocaba molestias en la muñeca.",
                "priority": Product.Priority.HIGH,
                "status": Product.Status.PURCHASED,
                "waiting_days": 15,
                "review_date": today - timedelta(days=60),
                "purchased_at": timezone.now() - timedelta(days=45),
            },
        )
        if created:
            DecisionReview.objects.create(
                product=comprado,
                need_score=9,
                interest_score=8,
            )
            self.stdout.write(f"  + Producto comprado: {comprado.name}")

        inventario = [
            {
                "name": "Auriculares con cable básicos",
                "category": "Auriculares",
                "purchase_date": today - timedelta(days=400),
                "url": "https://example.com/auriculares",
                "image_url": "https://example.com/auriculares.jpg",
            },
            {
                "name": "Mochila de trekking 30L",
                "category": "Mochilas",
                "purchase_date": today - timedelta(days=800),
            },
            {
                "name": "Teclado de membrana",
                "category": "Teclados",
                "purchase_date": today - timedelta(days=500),
            },
            {
                "name": "Altavoz bluetooth pequeño",
                "category": "Ocio",
                "purchase_date": today - timedelta(days=300),
            },
            {
                "name": "Silla de comedor con respaldo rígido",
                "category": "Oficina",
                "purchase_date": today - timedelta(days=700),
                "notes": "Es la que uso para trabajar; de ahí las molestias.",
            },
        ]
        for data in inventario:
            item, created = OwnedItem.objects.get_or_create(
                name=data["name"], defaults=data
            )
            if created:
                self.stdout.write(f"  + Inventario: {item.name}")

        self.stdout.write(self.style.SUCCESS("Datos de demostración listos."))
