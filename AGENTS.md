# AGENTS.md

Guía para agentes y desarrolladores que trabajan en «¿Lo quiero?».

## Qué es

Aplicación web personal de Django para decidir compras: periodo de reflexión, cuestionario de revisión, alternativas («dupes»), inventario y estadísticas. Un único usuario, uso local, sin autenticación.

## Arquitectura

- **Django 5.2** monolítico: plantillas renderizadas por Django (sin API REST ni SPA).
- Una sola app: `wishlist/` (modelos, servicios, formularios, vistas, admin, commandos).
- `config/` = configuración del proyecto (settings, urls, wsgi/asgi).
- `templates/` = plantillas globales; `templates/wishlist/` = plantillas de la app.
- `static/` = Tailwind CSS compilado (`static/css/app.css`) + fuente (`static/src/input.css`).
- `data/` = SQLite persistente (`db.sqlite3`), montado por volumen en Docker.
- `wishlist/services.py` = reglas de negocio puras (sin Django ORM salvo estadísticas), fácilmente testeables.
- Docker: `Dockerfile` + `compose.yaml`, migraciones automáticas al arrancar.

## Convenciones

- **Código en inglés, interfaz en español.** Etiquetas y textos visibles siempre en español; nombres internos en inglés (valores de `TextChoices`, claves de JSON).
- **Dinero en `DecimalField`**, nunca `float`. Precios validados con `MinValueValidator(0)`.
- **Validación en el servidor** (formularios). JavaScript solo como mejora visual (p. ej. sugerir días de espera).
- **Sin `mark_safe`** con datos del usuario; el autoescapado de Django está activo.
- **Historial inmutable**: cada `DecisionReview` crea un registro nuevo; nunca se sobrescribe.
- Estado de producto: `new`, `waiting`, `comparing`, `purchased`, `discarded`.
- Preferir vistas basadas en funciones; las mutaciones van por **POST** y redirigen (patrón PRG).
- Evitar consultas N+1 con `prefetch_related`/`select_related` donde corresponda.
- Ruff para lint y formato (ver `ruff.toml`).

## Comandos de desarrollo

```bash
python manage.py runserver              # servidor de desarrollo
python manage.py makemigrations wishlist
python manage.py migrate
python manage.py seed_demo              # datos ficticios + superusuario admin/admin, no duplica (--reset los recrea)
python manage.py changepassword admin   # cambiar la contraseña por defecto del admin
python manage.py createsuperuser
python manage.py test                   # pruebas
ruff check .                            # lint
ruff format .                           # formato
npm run build:css                       # recompilar Tailwind (tras tocar input.css)
docker compose up --build               # entorno completo
docker compose exec web python manage.py test
```

## Reglas de negocio (en `wishlist/services.py`)

- **Periodo de reflexión** (`suggested_waiting_days`): < 15 € → 7 días; < 35 € → 15; < 50 € → 30; >= 50 € → 45. El borde exacto (15,00 € y 35,00 €) entra en el tramo siguiente.
- **Fecha de revisión** (`compute_review_date` / `Product.save`): `fecha de creación + waiting_days`, solo al crear.
- **Sugerencia de días**: en `ProductForm`, si el campo está vacío se aplica la sugerencia; el valor manual se respeta.
- **Estado inicial**: al crear con `waiting_days > 0`, el estado es `waiting` (se cambia después desde la ficha).
- **Recomendación** (`purchase_recommendation`): matriz necesidad × interés (alto = >= 7). Es orientación, no decisión automática.
- **Comparación** (`price_comparison`): diferencia y % de ahorro; evita dividir por cero (precio original 0 → sin porcentaje; sin precios → sin comparación).
- **Puntuación combinada** (`combined_score`): `similitud×0.4 + calidad×0.35 + durabilidad×0.25`, escala 0–10, un decimal. Orientativa, no objetiva.
- **Estadísticas** (`compute_stats`): controla listas vacías; `created_at` no se puede fijar por `create()` porque es `auto_now_add` (usar `.update()` en tests).

## Cómo ejecutar las pruebas

```bash
python manage.py test
```

Usan el runner de Django (sin pytest). Localización de archivos: `wishlist/tests/` (`test_services.py`, `test_models.py`, `test_forms.py`, `test_views.py`).

## Decisiones técnicas

- `app_name` **no** se usa en `wishlist/urls.py`: los nombres de URL son globales (simplifica plantillas y `reverse`). `admin` conserva su namespace `admin:`.
- El CSS de Tailwind **está compilado y versionado** (`static/css/app.css`) para funcionar sin Node en tiempo de ejecución ni internet.
- La auto-sugerencia de días vive en el formulario, no en `Product.save()` (permitir modificación manual sin hackear el valor por defecto).
- Los tests de vistas usan números con coma decimal (localización es-ES): `99,00 €`.
- Contenedor Docker sin usuario no-root: decisión deliberada para simplificar permisos de escritura del volumen `./data` en un entorno local de un solo usuario.
- `SECRET_KEY` sin variable de entorno se genera una vez y se persiste en `data/secret_key` (ignorado por git): cada instalación local tiene su propia clave aunque el repositorio sea público.
- `seed_demo` crea el superusuario `admin`/`admin` si no existe (solo en creación, nunca resetea la contraseña). Es una app local de un solo usuario; el README recomienda cambiarla.

## Funciones fuera del MVP (no implementar todavía)

Scraping de precios, importación automática de enlaces, extensión de navegador, app móvil nativa, multi-usuario, notificaciones por correo, seguimiento automático de precios, APIs de tiendas, inteligencia artificial, sincronización en la nube, listas compartidas y procesamiento de pagos.
