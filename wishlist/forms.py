"""Formularios de «¿Lo quiero?» con validación en el servidor."""

from django import forms

from .categories import all_categories
from .models import (
    Alternative,
    AppSettings,
    DecisionReview,
    OwnedItem,
    PriceSnapshot,
    Product,
)
from .services import suggested_waiting_days, waiting_config

# Preguntas del cuestionario de reflexión.
# (clave, texto de la pregunta)
REFLECTION_QUESTIONS = [
    ("q1", "¿Qué problema concreto resuelve?"),
    ("q2", "¿Ya tienes algo que haga lo mismo?"),
    ("q3", "¿Cuántas veces esperas utilizarlo?"),
    ("q4", "¿Lo comprarías si no estuviera rebajado?"),
    ("q5", "¿Puedes pagarlo sin utilizar ahorros importantes?"),
    ("q6", "¿Crees que seguirás queriéndolo dentro de un mes?"),
    ("q7", "¿Qué ocurriría si no lo compras?"),
    ("q8", "¿Dónde lo guardarás?"),
    ("q9", "¿Cuál es la principal razón para comprarlo?"),
    ("q10", "¿Cuál es la principal razón para no comprarlo?"),
]


class ProductForm(forms.ModelForm):
    CATEGORY_NEW = "__new__"

    waiting_days = forms.IntegerField(
        label="Días de espera",
        min_value=0,
        required=False,
        help_text=("Déjalo en blanco para usar los días sugeridos según el precio."),
    )

    new_category = forms.CharField(
        label="Nueva categoría",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-field",
                "placeholder": "Escribe el nombre de la nueva categoría…",
            }
        ),
    )

    class Meta:
        model = Product
        fields = [
            "name",
            "url",
            "image_url",
            "current_price",
            "target_price",
            "category",
            "reason",
            "priority",
            "waiting_days",
            "status",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-field"}),
            "url": forms.URLInput(attrs={"class": "form-field"}),
            "image_url": forms.URLInput(attrs={"class": "form-field"}),
            "current_price": forms.NumberInput(
                attrs={"class": "form-field", "step": "0.01"}
            ),
            "target_price": forms.NumberInput(
                attrs={"class": "form-field", "step": "0.01"}
            ),
            "category": forms.Select(attrs={"class": "form-field"}),
            "reason": forms.Textarea(attrs={"class": "form-field", "rows": 4}),
            "status": forms.Select(attrs={"class": "form-field"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        price_initial = self.initial.get("current_price")
        if (
            self.instance.pk is None
            and price_initial is not None
            and "waiting_days" not in self.data
        ):
            self.initial["waiting_days"] = suggested_waiting_days(
                price_initial, waiting_config(AppSettings.load())
            )
        self._set_category_choices()

    def _existing_categories(self):
        return list(all_categories())

    def _set_category_choices(self):
        categories = self._existing_categories()
        current = self.instance.category
        if current and current not in categories:
            categories.insert(0, current)
        options = [("", "Sin categoría")]
        options.extend((category, category) for category in categories)
        options.append((self.CATEGORY_NEW, "Otra categoría…"))
        self.fields["category"].widget.choices = options

    def clean(self):
        cleaned = super().clean()
        if cleaned is None:
            return cleaned

        current_price = cleaned.get("current_price")
        waiting_days = cleaned.get("waiting_days")

        if current_price is not None and current_price < 0:
            self.add_error("current_price", "El precio no puede ser negativo.")
            if waiting_days is None:
                waiting_days = 7
        elif waiting_days is None:
            waiting_days = suggested_waiting_days(
                current_price, waiting_config(AppSettings.load())
            )

        cleaned["waiting_days"] = waiting_days
        self.instance.waiting_days = waiting_days

        # Categoría: si se elige «Otra categoría…», se usa el valor escrito.
        category = cleaned.get("category")
        if category == self.CATEGORY_NEW:
            new_category = (cleaned.get("new_category") or "").strip()
            if not new_category:
                self.add_error(
                    "new_category", "Escribe el nombre de la nueva categoría."
                )
                category = ""
            else:
                category = new_category
            cleaned["category"] = category

        # Regla de negocio: con periodo de espera, el estado inicial es
        # «En espera». El estado se puede cambiar después desde la ficha.
        if self.instance.pk is None and waiting_days > 0:
            cleaned["status"] = Product.Status.WAITING

        return cleaned


class AlternativeForm(forms.ModelForm):
    class Meta:
        model = Alternative
        fields = [
            "name",
            "url",
            "image_url",
            "price",
            "similarity_score",
            "quality_score",
            "durability_score",
            "warranty_months",
            "is_second_hand",
            "notes",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-field"}),
            "url": forms.URLInput(attrs={"class": "form-field"}),
            "image_url": forms.URLInput(attrs={"class": "form-field"}),
            "price": forms.NumberInput(attrs={"class": "form-field", "step": "0.01"}),
            "similarity_score": forms.NumberInput(
                attrs={"class": "form-field", "min": 0, "max": 100}
            ),
            "quality_score": forms.NumberInput(
                attrs={"class": "form-field", "min": 1, "max": 10}
            ),
            "durability_score": forms.NumberInput(
                attrs={"class": "form-field", "min": 1, "max": 10}
            ),
            "warranty_months": forms.NumberInput(
                attrs={"class": "form-field", "min": 0}
            ),
            "notes": forms.Textarea(attrs={"class": "form-field", "rows": 3}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned and cleaned.get("price") is not None and cleaned["price"] < 0:
            self.add_error("price", "El precio no puede ser negativo.")
        return cleaned


class ReviewForm(forms.ModelForm):
    class Meta:
        model = DecisionReview
        fields = [
            "need_score",
            "interest_score",
            "notes",
        ]
        widgets = {
            "need_score": forms.NumberInput(
                attrs={"class": "form-field", "min": 1, "max": 10}
            ),
            "interest_score": forms.NumberInput(
                attrs={"class": "form-field", "min": 1, "max": 10}
            ),
            "notes": forms.Textarea(attrs={"class": "form-field", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key, question in REFLECTION_QUESTIONS:
            self.fields[key] = forms.CharField(
                label=question,
                required=False,
                widget=forms.Textarea(
                    attrs={
                        "class": "form-field",
                        "rows": 2,
                        "placeholder": "Tu respuesta…",
                    }
                ),
            )

    def clean(self):
        cleaned = super().clean()
        if cleaned is None:
            return cleaned
        answers = {
            key: {
                "label": question,
                "answer": cleaned.get(key, ""),
            }
            for key, question in REFLECTION_QUESTIONS
        }
        self.answers = answers
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.answers = getattr(self, "answers", {})
        if commit:
            instance.save()
        return instance


class OwnedItemForm(forms.ModelForm):
    CATEGORY_NEW = "__new__"

    new_category = forms.CharField(
        label="Nueva categoría",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-field",
                "placeholder": "Escribe el nombre de la nueva categoría…",
            }
        ),
    )

    class Meta:
        model = OwnedItem
        fields = [
            "name",
            "category",
            "description",
            "url",
            "image_url",
            "purchase_date",
            "notes",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-field"}),
            "category": forms.Select(attrs={"class": "form-field"}),
            "description": forms.Textarea(attrs={"class": "form-field", "rows": 3}),
            "url": forms.URLInput(attrs={"class": "form-field"}),
            "image_url": forms.URLInput(attrs={"class": "form-field"}),
            "purchase_date": forms.DateInput(
                attrs={"class": "form-field", "type": "date"}
            ),
            "notes": forms.Textarea(attrs={"class": "form-field", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_category_choices()

    def _set_category_choices(self):
        categories = list(all_categories())
        current = self.instance.category
        if current and current not in categories:
            categories.insert(0, current)
        options = [("", "Sin categoría")]
        options.extend((category, category) for category in categories)
        options.append((self.CATEGORY_NEW, "Otra categoría…"))
        self.fields["category"].widget.choices = options

    def clean(self):
        cleaned = super().clean()
        if cleaned is None:
            return cleaned
        category = cleaned.get("category")
        if category == self.CATEGORY_NEW:
            new_category = (cleaned.get("new_category") or "").strip()
            if not new_category:
                self.add_error(
                    "new_category", "Escribe el nombre de la nueva categoría."
                )
                category = ""
            else:
                category = new_category
            cleaned["category"] = category
        return cleaned


class PriceSnapshotForm(forms.ModelForm):
    class Meta:
        model = PriceSnapshot
        fields = ["price"]
        widgets = {
            "price": forms.NumberInput(attrs={"class": "form-field", "step": "0.01"}),
        }

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price < 0:
            raise forms.ValidationError("El precio no puede ser negativo.")
        return price


class CategoryRenameForm(forms.Form):
    name = forms.CharField(
        label="Nuevo nombre",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-field"}),
    )


class AppSettingsForm(forms.ModelForm):
    class Meta:
        model = AppSettings
        fields = [
            "price_tier_1",
            "waiting_days_1",
            "price_tier_2",
            "waiting_days_2",
            "price_tier_3",
            "waiting_days_3",
            "waiting_days_max",
        ]
        widgets = {
            "price_tier_1": forms.NumberInput(
                attrs={"class": "form-field", "step": "0.01", "min": "0.01"}
            ),
            "price_tier_2": forms.NumberInput(
                attrs={"class": "form-field", "step": "0.01", "min": "0.01"}
            ),
            "price_tier_3": forms.NumberInput(
                attrs={"class": "form-field", "step": "0.01", "min": "0.01"}
            ),
            "waiting_days_1": forms.NumberInput(
                attrs={"class": "form-field", "min": 0}
            ),
            "waiting_days_2": forms.NumberInput(
                attrs={"class": "form-field", "min": 0}
            ),
            "waiting_days_3": forms.NumberInput(
                attrs={"class": "form-field", "min": 0}
            ),
            "waiting_days_max": forms.NumberInput(
                attrs={"class": "form-field", "min": 0}
            ),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned is None:
            return cleaned
        tiers = [
            cleaned.get("price_tier_1"),
            cleaned.get("price_tier_2"),
            cleaned.get("price_tier_3"),
        ]
        if all(t is not None for t in tiers) and not (tiers[0] < tiers[1] < tiers[2]):
            self.add_error(
                "price_tier_3",
                "Los umbrales deben ir en orden creciente (bajo < medio < alto).",
            )
        return cleaned
