# 🛠️ Guía de Instalación

Esta guía asume que ya tienes instalado WSL2 con Ubuntu 22.04 o superior.

## 1. Requisitos del Sistema

WSLaragon requiere los siguientes servicios instalados en tu Ubuntu:

- **Servidor Web**: Nginx
- **Base de Datos**: MariaDB / MySQL
- **PHP**: PHP 8.1+ (recomendado 8.3) con FPM
- **Otras**: `mkcert` (para SSL local)

## 2. Instalación de WSLaragon

Sigue estos pasos para instalar el CLI de forma global:

```bash
# Entra en la carpeta del proyecto
cd /home/wil/baselog/wslaragon

# Instala las dependencias y crea el enlace global
sudo ln -sf $(pwd)/venv/bin/wslaragon /usr/local/bin/wslaragon
```

## 3. Configuración Inicial

WSLaragon utiliza un archivo `.env` para gestionar las credenciales de forma segura.

1.  Copia la plantilla de ejemplo:
    ```bash
    cp .env.example .env
    ```
2.  Edita el archivo `.env` y configura tu contraseña de base de datos:
    ```text
    DB_USER=root
    DB_PASSWORD=tu_contraseña_segura
    ```

## 4. Permisos de Administrador (SUDO)

Para que WSLaragon pueda crear sitios sin pedirte contraseña cada vez para Nginx, ejecuta:

```bash
echo "$USER ALL=(ALL) NOPASSWD: /usr/sbin/nginx, /usr/sbin/service, /bin/systemctl, /usr/bin/phpenmod, /usr/bin/phpdismod, /bin/cp, /bin/ln, /bin/rm, /usr/bin/tee" | sudo tee /etc/sudoers.d/wslaragon
```

---

¡Listo! Ahora puedes empezar a usar el comando `wslaragon` desde cualquier lugar.
