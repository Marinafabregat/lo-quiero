# PLAN.md — «¿Lo quiero?»

Plan de construcción del MVP de la aplicación web personal para decidir compras.

## Objetivo

Construir una primera versión funcional con Django + Tailwind CSS + SQLite + Docker, lista para ejecutar desde Windows con `docker compose up --build` y accesible en `http://localhost:8000`.

## Estado inicial del repositorio

El repositorio contenía un esqueleto parcial:

- `config/` con `settings.py`, `urls.py`, `wsgi.py`, `asgi.py`.
- `wishlist/` con el modelo `Product` (ubicado erróneamente en `admin.py`), un borrador de `services.py` y tests iniciales.
- `requirements.txt` mínimo.
- Sin migraciones, formularios, vistas, plantillas, estáticos, Docker ni documentación.

### Correcciones necesarias

1. Mover los modelos a `models.py` y reescribir `admin.py` con el registro real.
2. Ajustar `suggested_waiting_days` a los umbrales de la especificación (7/15/30/45 días para <15 €, <35 €, <50 €, >=50 €) en lugar de los originales (50/200/500 €).
3. Eliminar la lógica frágil de auto-sugerencia basada en `waiting_days == 7` del `save()` del modelo; la sugerencia se aplica desde el formulario y respeta la modificación manual.

## Arquitectura

- **Django 5.2** como framework único (no API REST, no frontend SPA).
- Una única app Django: `wishlist`.
- Plantillas renderizadas por Django en `templates/` (directorio raíz, según estructura pedida).
- Tailwind CSS compilado a un CSS estático (`static/css/app.css`) que se incluye en el repositorio, para no depender de Node en tiempo de ejecución ni de internet.
- SQLite persistido en `./data/db.sqlite3` mediante volumen de Docker.
- Lógica de negocio en `wishlist/services.py`, separada de las vistas.
- Formularios con validación estricta en el servidor (rangos, precios no negativos).

## Modelos

`Product`, `Alternative`, `DecisionReview`, `OwnedItem` y `PriceSnapshot`, con los campos y estados indicados en la especificación.

## Fases

1. Configuración y entorno.
2. Modelos y migraciones.
3. Reglas de negocio (servicios).
4. Formularios.
5. Vistas y URLs.
6. Plantillas.
7. Tailwind CSS.
8. Panel administrativo.
9. Comando `seed_demo`.
10. Docker + persistencia.
11. Pruebas.
12. Documentación.

## Decisiones técnicas relevantes

- **Umbrales de espera**: `price < 15` → 7 días; `price < 35` → 15 días; `price < 50` → 30 días; `>= 50` → 45 días. El borde exacto en 15,00 € y 35,00 € entra en el tramo siguiente (documentado).
- **Estado inicial**: al crear un producto con días de espera > 0 se fuerza el estado `waiting` (regla de negocio). El usuario puede cambiarlo después desde la ficha.
- **Fecha de revisión**: `review_date = fecha de creación + waiting_days`, calculada en `Product.save()` solo para productos nuevos.
- **Puntuación combinada de alternativas**: media ponderada `similitud (40%) + calidad (35%) + durabilidad (25%)`, en escala 0–10. Se muestra como orientación, no como verdad objetiva.
- **CSS estático compilado**: se incluye `static/css/app.css` en el repositorio para funcionar sin Node. Se puede regenerar con `npm run build:css` (documentado).
- **Pruebas**: runner nativo de Django (`manage.py test`), sin pytest, para mantener dependencias al mínimo.

## Fuera del MVP

Scraping, importación automática de enlaces, extensión de navegador, app móvil, multi-usuario, notificaciones por correo, seguimiento automático de precios, APIs de tiendas, IA y procesamiento de pagos.
