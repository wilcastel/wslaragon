# 📚 Glosario de Comandos WSLaragon

Este documento sirve como referencia completa de todos los comandos disponibles en el CLI de `wslaragon`.

## 🏗️ Gestión de Sitios (`wslaragon site`)

Comando principal para la creación y administración de proyectos web.

| Comando | Argumentos / Opciones | Descripción |
| :--- | :--- | :--- |
| `site create` | `<name>` <br> `--php` / `--no-php` <br> `--mysql` / `--no-mysql` <br> `--ssl` / `--no-ssl` <br> `--database <name>` <br> `--public` <br> `--proxy <port>` <br> `--html` <br> `--wordpress` <br> `--laravel=<ver>` <br> `--postgres` <br> `--supabase` <br> `--force` | Crea un nuevo sitio con la configuración especificada. <br> **Ejemplos:** <br> `wslaragon site create mi-blog --wordpress` <br> `wslaragon site create app-node --proxy 3000` |
| `site list` | - | Lista todos los sitios creados y su estado actual (Activo/Inactivo, SSL, PHP, etc.). |
| `site delete` | `<name>` <br> `--remove-files` <br> `--remove-database` | Elimina la configuración de un sitio. Opcionalmente borra archivos y base de datos. |
| `site enable` | `<name>` | Habilita un sitio previamente deshabilitado en Nginx. |
| `site disable` | `<name>` | Deshabilita un sitio en Nginx (no borra archivos). |
| `site public` | `<name>` <br> `--enable` / `--disable` | Cambia el document root entre `./` y `./public` (útil para Laravel/Symfony). |
| `site fix-permissions` | `<name>` | Repara propietario y permisos de archivos (útil tras copiar ficheros desde Windows). |
| `site ssl` | `<name>` | Habilita HTTPS/SSL para un sitio existente que no lo tenía. |

## 🔧 Gestión de Servicios (`wslaragon service`)

Control directo sobre los demonios de sistema que potencian el entorno.

| Comando | Argumentos | Descripción |
| :--- | :--- | :--- |
| `service status` | - | Muestra el estado (Running/Stopped) y puertos de Nginx, MySQL, PHP-FPM, etc. |
| `service start` | `<service_name>` | Inicia un servicio específico (ej. `nginx`, `mysql`). |
| `service stop` | `<service_name>` | Detiene un servicio específico. |
| `service restart` | `<service_name>` | Reinicia un servicio específico. |

## 🐘 PHP (`wslaragon php`)

Gestión de versiones, extensiones y configuración `php.ini`.

| Comando | Argumentos | Descripción |
| :--- | :--- | :--- |
| `php versions` | - | Lista las versiones de PHP instaladas y marca la activa. |
| `php switch` | `<version>` | Cambia la versión global de PHP activa (ej. `wslaragon php switch 8.2`). |
| `php extensions` | - | Lista todas las extensiones PHP disponibles/activas. |
| `php enable_ext` | `<extension>` | Habilita una extensión PHP (ej. `mbstring`). |
| `php disable_ext` | `<extension>` | Deshabilita una extensión PHP. |
| `php config list` | - | Muestra valores importantes de `php.ini` (`memory_limit`, `upload_max_filesize`, etc.). |
| `php config get` | `<key>` | Muestra el valor de una directiva específica. |
| `php config set` | `<key> <value>` | Modifica una directiva en `php.ini` y reinicia FPM. |

## 🐬 MySQL / Bases de Datos (`wslaragon mysql`)

Herramientas rápidas para gestión de bases de datos MariaDB/MySQL.

| Comando | Argumentos | Descripción |
| :--- | :--- | :--- |
| `mysql databases` | - | Lista todas las bases de datos existentes y su tamaño. |
| `mysql create_db` | `<name>` | Crea una nueva base de datos vacía. |
| `mysql drop_db` | `<name>` | Elimina permanentemente una base de datos. |

## 🔒 SSL / Certificados (`wslaragon ssl`)

Gestión de la autoridad de certificación local.

| Comando | Argumentos | Descripción |
| :--- | :--- | :--- |
| `ssl list` | - | Lista todos los certificados SSL generados y sus fechas de validez. |
| `ssl setup` | - | Genera la Autoridad de Certificación (CA) principal si no existe. |
| `ssl generate` | `<domain>` | Genera manualmente un certificado para un dominio dado. |

## 🌐 Nginx (`wslaragon nginx`)

Configuración global del servidor web.

| Comando | Argumentos | Descripción |
| :--- | :--- | :--- |
| `nginx config list` | - | Muestra configuraciones editables de Nginx (ej. limit body size). |
| `nginx config set` | `<key> <value>` | Cambia configuraciones globales de Nginx (ej. `wslaragon nginx config set client_max_body_size 50M`). |

## 🩺 Diagnóstico (`wslaragon doctor`)

Herramientas de auto-diagnóstico para el entorno.

| Comando | Argumentos | Descripción |
| :--- | :--- | :--- |
| `doctor` | - | Ejecuta un chequeo completo de servicios, puertos, certificados SSL y configuraciones críticas. |

## 🤖 Agentes IA (`wslaragon agent`)

Integración con flujos de trabajo de Agentes de IA (.agent/skills).

| Comando | Argumentos | Descripción |
| :--- | :--- | :--- |
| `agent init` | `--preset <name>` <br> `--path <dir>` | Inicializa la estructura `.agent` (skills, memory, ui, specs) con skills predefinidos. <br> **Presets:** `default`, `laravel`, `wordpress`, `python`, `javascript`, `meta`. |
| `agent import` | `<url>` | Descarga e instala un Skill desde una URL remota (Raw Markdown). |

---

> **Nota:** Para ayuda interactiva, siempre puedes ejecutar `wslaragon --help` o `wslaragon <comando> --help`.
