# ¿Lo quiero?

Decide antes de comprar.

> 🌐 Página de presentación: <https://marinafabregat.github.io/lo-quiero/>

Aplicación web **personal** para reflexionar antes de comprar: guarda productos, establece un periodo obligatorio de reflexión, responde un cuestionario, compara alternativas o «dupes», registra los objetos que ya tienes y decide si compras, pospones o descartas.

> Uso local para **un único usuario**, sin registro ni autenticación. La base de datos es SQLite y se guarda en `./data`.

## Qué hace

- Guardar productos que quieres comprar con precio, categoría, motivo y prioridad.
- Elegir la categoría de un desplegable con las existentes o **crear una nueva**, y **gestionarlas** (renombrar para corregir erratas o eliminar etiquetas sin borrar los productos asociados).
- Sugerir un **periodo de reflexión** según el precio (7 / 15 / 30 / 45 días), modificable manualmente.
- Responder un **cuestionario de 10 preguntas** y puntuar necesidad e interés en cada revisión.
- Mostrar una **recomendación orientativa** según la última revisión.
- Añadir **alternativas («dupes»)** y compararlas con el original (diferencia de precio, ahorro, similitud, calidad, durabilidad, garantía, segunda mano).
- Llevar un **inventario** de lo que ya tienes y avisar si ya posees algo de la misma categoría.
- Registrar un **historial manual de precios**.
- Marcar productos como **comprado**, **descartado** o **posponer** la revisión.
- Consultar **estadísticas** sencillas (gastado, descartado, categorías, tiempos medios).

## Requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (con WSL 2 en Windows), o
- Python 3.12 + Node.js si quieres ejecutarlo fuera de Docker.

### Instalar Docker Desktop (resumen general)

1. Descarga e instala [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. En Windows, durante la instalación marca la opción de **WSL 2 backend** si se ofrece.
3. Reinicia el equipo cuando lo pida el instalador.
4. Abre Docker Desktop y espera a que aparezca el icono de ballena verde («Docker Desktop is running»).
5. Comprueba que funciona abriendo PowerShell o CMD y ejecutando `docker --version`.

## Iniciar el proyecto con Docker

```bash
docker compose up --build
```

La primera vez descarga la imagen base e instala dependencias: tarda unos minutos. Cuando termine:

- La aplicación está en **http://localhost:8000**.
- Las migraciones se aplican automáticamente al arrancar.

## Detenerlo

```bash
docker compose down
```

Para detenerlo y **borrar el contenedor** pero conservar los datos:

```bash
docker compose down   # los datos siguen en ./data
```

## Ejecutar migraciones

El arranque con Docker aplica las migraciones automáticamente. Si necesitas hacerlo a mano:

```bash
# Dentro del contenedor
docker compose exec web python manage.py migrate

# O en local (con virtualenv activo)
python manage.py migrate
```

Para crear migraciones nuevas tras modificar un modelo:

```bash
python manage.py makemigrations wishlist
```

## Datos de demostración

```bash
docker compose exec web python manage.py seed_demo
```

Añade auriculares, una mochila, un teclado, una silla, alternativas, revisiones, historial de precios, inventario, un producto comprado y uno descartado. También crea el superusuario **`admin` / `admin`** para el panel de administración si no existía. Es seguro ejecutarlo varias veces: **no duplica** los datos ni cambia la contraseña. No se ejecuta automáticamente al arrancar.

Para **borrar los datos demo actuales y crearlos desde cero** (por ejemplo, tras experimentar con la web):

```bash
docker compose exec web python manage.py seed_demo --reset
```

> `--reset` elimina todos los productos, alternativas, revisiones, precios e inventario, así que úsalo solo si no tienes datos propios que conservar.

## Panel de administración

Accesible en **http://localhost:8000/admin**. Tras ejecutar `seed_demo`, las credenciales de acceso son **`admin` / `admin`**.

> Es una app local de un único usuario, por eso se comparte una contraseña por defecto. En cuanto empieces a usarla, cámbiala o crea tu propio superusuario con el comando de abajo.

```bash
docker compose exec web python manage.py changepassword admin   # cambiar contraseña
```

Para crear un superusuario distinto desde cero:

```bash
docker compose exec web python manage.py createsuperuser
```

## Ejecutar las pruebas

```bash
docker compose exec web python manage.py test
```

O en local:

```bash
pip install -r requirements-dev.txt
python manage.py test
```

## Lint y formato

```bash
pip install -r requirements-dev.txt
ruff check .
ruff format .
```

## Dónde se guarda SQLite

El contenedor guarda la base de datos en `/app/data/db.sqlite3`, que está montado en la carpeta local `./data`. La carpeta **no se borra** al reconstruir el contenedor: tus datos persisten entre `docker compose down` y `docker compose up --build`.

En esa carpeta se guarda también `secret_key`: una clave secreta de Django **única por instalación**, generada automáticamente la primera vez si no defines la variable de entorno `SECRET_KEY`. Como `data/` está en `.gitignore`, cada persona que clone el repositorio tiene su propia clave aunque el código sea público.

## Copia de seguridad

Con el contenedor **detenido** (o parando la app), copia el archivo de base de datos:

```bash
# Detén el contenedor para evitar escrituras simultáneas
docker compose down

# Copia de seguridad (PowerShell)
Copy-Item data\db.sqlite3 backup-lo-quiero.sqlite3

# Copia de seguridad (CMD)
copy data\db.sqlite3 backup-lo-quiero.sqlite3
```

También puedes copiar la carpeta `data/` entera.

## Restaurar la base de datos

1. Detén el contenedor: `docker compose down`.
2. Reemplaza `data\db.sqlite3` con tu copia: `Copy-Item backup-lo-quiero.sqlite3 data\db.sqlite3`.
3. Arranca de nuevo: `docker compose up`.

## Reiniciar el entorno por completo (borrar todos los datos)

```bash
docker compose down
rm data/db.sqlite3          # PowerShell: Remove-Item data\db.sqlite3
docker compose up --build
```

> Esto elimina **todos** los productos, revisiones, alternativas, inventario y estadísticas.

## Problemas frecuentes en Windows y WSL 2

- **`docker compose` no se reconoce**: instala Docker Desktop y reinicia; usa PowerShell o CMD, no la consola antigua.
- **Error «Docker Engine stopped» / WSL**: abre Docker Desktop, ve a *Settings → Resources → WSL Integration* y comprueba que la integración esté activa. Ejecuta `wsl --update` en PowerShell.
- **Puerto 8000 ocupado**: otra aplicación usa el puerto. Cambia el mapeo en `compose.yaml` (por ejemplo `"8001:8000"`) y abre http://localhost:8001.
- **La base de datos no persiste**: comprueba que en `compose.yaml` existe el volumen `./data:/app/data`. Si borraste la carpeta `data`, se crea vacía.
- **Permisos de `./data` en Linux/WSL**: si el contenedor no puede escribir, asegúrate de que la carpeta `data` existe y tiene permisos de escritura.
- **Tarda mucho la primera vez**: es normal (descarga de imagen + dependencias). Las siguientes son rápidas.

## Desarrollo fuera de Docker (opcional)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Si modificas plantillas o el CSS, reconstruye los estilos (Tailwind):

```bash
npm install
npm run build:css
```

## Trabajo futuro (fuera del MVP)

- Scraping de precios y seguimiento automático.
- Importación automática desde enlaces y extensión de navegador.
- Aplicación móvil nativa.
- Cuentas y datos para múltiples usuarios.
- Notificaciones por correo.
- APIs de tiendas, inteligencia artificial y recomendaciones por modelos externos.
- Sincronización en la nube, listas compartidas y procesamiento de pagos.

Ver también `AGENTS.md` y `PLAN.md` para decisiones técnicas y convenciones.
