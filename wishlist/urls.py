from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("productos/", views.product_list, name="product_list"),
    path("productos/nuevo/", views.product_create, name="product_create"),
    path("productos/<int:pk>/", views.product_detail, name="product_detail"),
    path("productos/<int:pk>/editar/", views.product_edit, name="product_edit"),
    path(
        "productos/<int:pk>/eliminar/",
        views.product_delete,
        name="product_delete",
    ),
    path(
        "productos/<int:pk>/comprar/",
        views.product_purchase,
        name="product_purchase",
    ),
    path(
        "productos/<int:pk>/descartar/",
        views.product_discard,
        name="product_discard",
    ),
    path(
        "productos/<int:pk>/posponer/",
        views.product_postpone,
        name="product_postpone",
    ),
    path(
        "productos/<int:product_pk>/alternativas/nueva/",
        views.alternative_create,
        name="alternative_create",
    ),
    path(
        "productos/<int:product_pk>/alternativas/<int:pk>/editar/",
        views.alternative_edit,
        name="alternative_edit",
    ),
    path(
        "productos/<int:product_pk>/alternativas/<int:pk>/eliminar/",
        views.alternative_delete,
        name="alternative_delete",
    ),
    path(
        "productos/<int:pk>/revisiones/nueva/",
        views.review_create,
        name="review_create",
    ),
    path(
        "productos/<int:pk>/precios/",
        views.price_snapshot_create,
        name="price_snapshot_create",
    ),
    path("categorias/", views.category_manage, name="category_manage"),
    path(
        "categorias/<str:name>/renombrar/",
        views.category_rename,
        name="category_rename",
    ),
    path(
        "categorias/<str:name>/eliminar/",
        views.category_delete,
        name="category_delete",
    ),
    path("inventario/", views.inventory_list, name="inventory_list"),
    path("inventario/nuevo/", views.inventory_create, name="inventory_create"),
    path(
        "inventario/<int:pk>/editar/",
        views.inventory_edit,
        name="inventory_edit",
    ),
    path(
        "inventario/<int:pk>/eliminar/",
        views.inventory_delete,
        name="inventory_delete",
    ),
    path("estadisticas/", views.stats, name="stats"),
    path("configuracion/", views.settings, name="settings"),
]
