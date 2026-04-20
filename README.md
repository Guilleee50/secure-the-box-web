# 🛡️ Secure the Box - Plataforma de Entrenamiento SOC

## Instalación del entorno
python -m venv venv  
source venv/bin/activate  
pip install -r requirements.txt  
python manage.py migrate  
python manage.py runserver

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Django](https://img.shields.io/badge/Django-5.0-green?logo=django)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC?logo=tailwind-css)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)
![Nginx](https://img.shields.io/badge/Nginx-Production-009639?logo=nginx)

**Secure the Box** es una plataforma interactiva diseñada para el entrenamiento de perfiles Blue Team y analistas SOC. Permite a los usuarios desplegar entornos vulnerables (contenedores Docker), aplicar políticas de bastionado (Hardening) y validar su seguridad en tiempo real a través de un sistema de puntuación centralizado.

---

## 🚀 Características Principales

* **Despliegue Rápido:** Máquinas vulnerables encapsuladas en Docker.
* **Validación en Tiempo Real:** Script de evaluación automática (`check_hardening.py`).
* **Dashboard SOC:** Panel de usuario para seguimiento de máquinas completadas y puntuación.
* **Arquitectura Escalable:** Servidor web desplegado en AWS con Nginx y Gunicorn.

---

## 🛠️ Stack Tecnológico

* **Backend:** Python, Django
* **Frontend:** HTML5, TailwindCSS
* **Servidor de Producción:** Nginx (Proxy inverso), Gunicorn (WSGI)
* **Infraestructura:** AWS EC2, Docker & Docker Compose
* **Base de Datos:** SQLite (Desarrollo) / PostgreSQL (Producción)

---

## 💻 Requisitos Previos

Para ejecutar este proyecto en local necesitas tener instalado:
* [Python 3.10+](https://www.python.org/downloads/)
* [Git](https://git-scm.com/)
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) (para las máquinas vulnerables)

---
