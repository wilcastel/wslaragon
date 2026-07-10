# 📚 Glosario de Comandos WSLaragon

Este documento sirve como referencia completa de todos los comandos disponibles en el CLI de `wslaragon`.

## 🏗️ Gestión de Sitios (`wslaragon site`)

Comando principal para la creación y administración de proyectos web.

| Comando | Argumentos / Opciones | Descripción |
| :--- | :--- | :--- |
| `site create` | `<name>` <br> `--php` / `--no-php` <br> `--mysql` / `--no-mysql` <br> `--ssl` / `--no-ssl` <br> `--database <name>` <br> `--public` <br> `--proxy <port>` <br> `--node` / `--python` <br> `--html` <br> `--wordpress` <br> `--phpmyadmin` <br> `--laravel=<ver>` <br> `--vite <template>` <br> `--astro[=<template>]` <br> `--postgres` <br> `--supabase` <br> `--force` <br> `--headless --backend=<wordpress\|laravel> --frontend=<sveltekit\|astro> --url=<name>` | Crea un nuevo sitio con la configuración especificada. `--wordpress` crea la base de datos MySQL automáticamente. `--headless` crea DOS sitios vinculados (frontend + backend/API) que comparten una raíz de proyecto — se usa `--url` en vez del argumento posicional `<name>`. <br> **Ejemplos:** <br> `wslaragon site create mi-blog --wordpress` <br> `wslaragon site create pma --phpmyadmin` <br> `wslaragon site create app-node --node` (Auto-port) <br> `wslaragon site create mi-app --vite react` <br> `wslaragon site create mi-astro --astro` <br> `wslaragon site create --headless --backend=wordpress --frontend=sveltekit --url=misitio` |
| `site list` | - | Lista todos los sitios creados y su estado actual (Activo/Inactivo, SSL, PHP, etc.). |
| `site delete` | `<name>` <br> `--remove-database` / `--keep-database` | Elimina la configuración de un sitio. Pregunta interactivamente si borrar los archivos del proyecto (no existe un flag `--remove-files`); la base de datos se borra solo con `--remove-database`. <br> **Nota**: si `<name>` es la mitad de un par headless, se avisa antes de confirmar y se eliminan **ambas mitades** junto con la raíz compartida. |
| `site enable` | `<name>` | Habilita un sitio previamente deshabilitado en Nginx. |
| `site disable` | `<name>` | Deshabilita un sitio en Nginx (no borra archivos). |
| `site public` | `<name>` <br> `--enable` / `--disable` | Cambia el document root entre `./` y `./public` (útil para Laravel/Symfony). |
| `site fix-permissions` | `<name>` | Repara propietario y permisos de archivos (útil tras copiar ficheros desde Windows). |
| `site ssl` | `<name>` | Habilita HTTPS/SSL para un sitio existente que no lo tenía. |
| `site api add` | `<name> <path> <backend_url>` | Agrega un proxy reverso Nginx en `<path>` hacia `<backend_url>` para el sitio (útil en Astro headless / sitios API-driven). |
| `site api remove` | `<name> <path>` | Elimina un proxy reverso previamente agregado. |
| `site api list` | `<name>` | Lista los proxies reversos configurados para el sitio. |
| `site export` | `<name>` <br> `--output <path>` | Crea un archivo de backup completo (.wslaragon) del sitio. |
| `site import` | `<file>` <br> `--name <name>` | Restaura un sitio desde un archivo de backup. |

## 🚀 Procesos Node (`wslaragon node`)

Gestión de aplicaciones back-end (Node, Python) con PM2.

| Comando | Argumentos | Descripción |
| :--- | :--- | :--- |
| `node list` | - | Lista procesos activos en PM2. |
| `node start` | `<site_name>` | Inicia la aplicación del sitio (app.js, npm start, main.py). |
| `node stop` | `<site_name>` | Detiene el proceso del sitio. |
| `node restart` | `<site_name>` | Reinicia el proceso del sitio. |
| `node delete` | `<site_name>` | Elimina el proceso de la lista y lo detiene. |

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
| `php enable-ext` | `<extension>` | Habilita una extensión PHP (ej. `mbstring`). |
| `php disable-ext` | `<extension>` | Deshabilita una extensión PHP. |
| `php config list` | - | Muestra valores importantes de `php.ini` (`memory_limit`, `upload_max_filesize`, etc.). |
| `php config get` | `<key>` | Muestra el valor de una directiva específica. |
| `php config set` | `<key> <value>` | Modifica una directiva en `php.ini` y reinicia FPM. |
| `php upload-limit` | `[size]` (default `512M`) | Ajusta `upload_max_filesize`, `post_max_size`, `memory_limit`, `max_execution_time` y `max_input_time` en **todas** las versiones de PHP instaladas (FPM + CLI) y `client_max_body_size` en Nginx, en un solo comando. Ej. `wslaragon php upload-limit 1G`. |

## 🐬 MySQL / Bases de Datos (`wslaragon mysql`)

Herramientas rápidas para gestión de bases de datos MariaDB/MySQL.

| Comando | Argumentos | Descripción |
| :--- | :--- | :--- |
| `mysql databases` | - | Lista todas las bases de datos existentes y su tamaño. |
| `mysql create-db` | `<name>` | Crea una nueva base de datos vacía. |
| `mysql drop-db` | `<name>` | Elimina permanentemente una base de datos. |

## 🔒 SSL / Certificados (`wslaragon ssl`)

Gestión de la autoridad de certificación local.

| Comando | Argumentos | Descripción |
| :--- | :--- | :--- |
| `ssl list` | - | Lista todos los certificados SSL generados y sus fechas de validez. |
| `ssl setup` | - | Genera la Autoridad de Certificación (CA) principal si no existe. |
| `ssl generate` | `<domain>` | Genera manualmente un certificado para un dominio dado. |
| `ssl delete` | `<domain>` | Elimina un certificado SSL y limpia la entrada correspondiente del hosts de Windows. |

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
| `completion` | `--install` <br> `--shell <type>` | Configura el autocompletado en tu terminal (bash/zsh). |

---


## ℹ️ Ayuda y Documentación

Comandos para acceder a la documentación y mejorar la experiencia de uso.

| Comando | Argumentos | Descripción |
| :--- | :--- | :--- |
| `glossary` | `<term>` | Muestra o busca en el glosario de comandos (ej. `wslaragon glossary node`). |
| `--glossary` / `-g` | - | Flag global para ver todo el glosario. |
| `completion` | `--install` <br> `--shell <type>` | Configura el autocompletado en tu terminal (bash/zsh). |

---

> **Nota:** Para ayuda interactiva, siempre puedes ejecutar `wslaragon --help` o `wslaragon <comando> --help`.
