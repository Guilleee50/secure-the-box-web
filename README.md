# Secure the Box - Plataforma de Entrenamiento SOC

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Django](https://img.shields.io/badge/Django-6.0-green?logo=django)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC?logo=tailwind-css)
![MariaDB](https://img.shields.io/badge/MariaDB-Production-003545?logo=mariadb)
![Nginx](https://img.shields.io/badge/Nginx-Production-009639?logo=nginx)

**Secure the Box** es una plataforma interactiva para el entrenamiento de perfiles Blue Team y analistas SOC. Los usuarios completan máquinas de hardening, obtienen FLAGS firmadas criptográficamente y las canjean desde la web para acumular puntos en un ranking global.

---

## Stack Tecnológico

| Capa | Tecnología |
|---|---|
| Backend | Python 3.12, Django 6.0, Django REST Framework 3.17 |
| Frontend | HTML5, TailwindCSS 3.4 |
| Autenticación | `django-two-factor-auth` (2FA TOTP), `django-axes` (bloqueo por IP) |
| API Docs | `drf-spectacular` (OpenAPI 3 + Swagger UI) |
| Base de datos | MariaDB (producción) |
| Servidor | Nginx (proxy inverso) + Gunicorn (WSGI) |
| Dominio | [securethebox.cat](https://securethebox.cat) |

---

## Arquitectura general

```
Usuario
  │
  ├─ Web (Django)  ──► MariaDB
  │      │
  │   Panel, Ranking, Canje de FLAGS
  │
Script de validación (máquina local)
  │
  ├─ POST /api/v1/flags/registrar/   ← deposita FLAG con firma HMAC
  └─ FLAG canjeada por el usuario en el panel web
```

---

## Características principales

- **Registro con CAPTCHA** y verificación en dos pasos (2FA TOTP).
- **Protección ante fuerza bruta:** bloqueo automático tras 5 intentos fallidos (`django-axes`), con página de lockout personalizada.
- **Sistema de FLAGS:** el script de validación genera una FLAG firmada con HMAC-SHA256 (`STB-<maquina>-<timestamp>-<hmac>`), la deposita en la BD y el usuario la canjea desde su panel. Caduca a los 30 minutos y es de un solo uso.
- **Puntuación automática:** al añadir una máquina completada, una señal de Django recalcula los puntos totales del perfil.
- **Ranking global:** los 5 usuarios con más puntos aparecen en la página principal.
- **Panel de usuario:** muestra máquinas completadas, puntuación total y la API Key personal.
- **API documentada** con Swagger UI en `/api/docs/` (solo accesible con `DEBUG=True` o cuenta de administrador).
- **Rate limiting:** 25 peticiones/día por usuario anónimo y autenticado.
- **Hardening HTTP:** cabeceras de seguridad, HTTPS forzado en producción, `SECURE_PROXY_SSL_HEADER` configurado para Nginx.

---

## Endpoints de la API

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| POST | `/api/v1/validar/` | Validar máquina por API Key (flujo legacy) | API Key |
| POST | `/api/v1/get_user_data` | Obtener datos del agente | API Key |
| POST | `/api/v1/flags/registrar/` | Depositar FLAG firmada (llamado por el script) | HMAC |
| POST | `/api/v1/flags/canjear/` | Canjear FLAG por puntos | Sesión web |
| GET | `/api/docs/` | Swagger UI | Admin / DEBUG |
| GET | `/api/schema/` | Esquema OpenAPI | Admin / DEBUG |

---

## Modelos de datos

- **`SOCProfile`** — perfil extendido de usuario: API Key, puntos totales, máquinas completadas, aceptación de normativa.
- **`Maquina`** — máquinas disponibles con nombre, descripción, dificultad y puntos.
- **`Flag`** — FLAGS de un solo uso: token HMAC, máquina asociada, timestamp de creación, usuario que la canjeó.
- **`Score`** — registro histórico de puntuaciones por máquina y usuario.

---

## Instalación en local

### Requisitos previos

- Python 3.12+
- MariaDB
- Git

### 1. Clonar y preparar el entorno

```bash
git clone <repo>
cd secure-the-box-web
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Crear la base de datos

```sql
sudo mariadb -u root -p
CREATE DATABASE securethebox_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'django_user'@'localhost' IDENTIFIED BY 'tu-contraseña';
GRANT ALL PRIVILEGES ON securethebox_db.* TO 'django_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3. Configurar variables de entorno

Copia `.env.example` a `.env` y rellena los valores:

```bash
cp .env.example .env
```

```ini
SECRET_KEY=genera-una-clave-larga-y-aleatoria
DEBUG=True
DB_NAME=securethebox_db
DB_USER=django_user
DB_PASSWORD=tu-contraseña
DB_HOST=localhost
DB_PORT=3306
FLAG_SECRET=secreto-compartido-con-el-repo-de-maquinas
```

> `FLAG_SECRET` debe coincidir con el valor configurado en el repositorio de máquinas para que las FLAGS sean válidas.

### 4. Aplicar migraciones y arrancar

```bash
python manage.py migrate
python manage.py createsuperuser  # opcional, para acceder al admin
python manage.py runserver
```

---

## Variables de entorno

| Variable | Descripción | Requerida |
|---|---|---|
| `SECRET_KEY` | Clave secreta de Django | Sí |
| `DEBUG` | Modo debug (`True`/`False`) | No (default: `False`) |
| `DB_NAME` | Nombre de la base de datos | Sí |
| `DB_USER` | Usuario de MariaDB | Sí |
| `DB_PASSWORD` | Contraseña de MariaDB | Sí |
| `DB_HOST` | Host de MariaDB | No (default: `localhost`) |
| `DB_PORT` | Puerto de MariaDB | No (default: `3306`) |
| `FLAG_SECRET` | Secreto HMAC compartido con el script de validación | Sí |

---

## Seguridad

- 2FA obligatorio en el flujo de login.
- Bloqueo por IP tras 5 intentos fallidos (desbloqueo automático en 1 hora).
- FLAGS firmadas con HMAC-SHA256 con caducidad de 30 minutos.
- HTTPS forzado en producción con redirección SSL y cookies seguras.
- Cabeceras: `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection`.
- Swagger UI restringido a administradores (o `DEBUG=True`).
