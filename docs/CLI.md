# 📖 Guía del CLI (Comandos)

El comando principal es `wslaragon`. Aquí tienes todos los comandos disponibles y ejemplos de uso.

## 📁 Gestión de Sitios (`site`)

### 1. Crear un Sitio
Crea un nuevo proyecto con configuración de Nginx, base de datos y SSL.

```bash
# Ejemplo básico (PHP + MySQL + SSL)
wslaragon site create mi-web --php --mysql --ssl

# Ejemplo solo HTML estático
wslaragon site create mi-web --html

# Crear sitio HTML completo (index.html, styles/, js/)
wslaragon site create landing --html

# Ejemplo WordPress (la base de datos se crea automáticamente)
wslaragon site create mi-blog --wordpress

# Ejemplo Laravel 12 con MySQL
wslaragon site create mi-app --laravel=12 --mysql

# Ejemplo Laravel 12 con PostgreSQL
wslaragon site create mi-app --laravel=12 --postgres

# Ejemplo Laravel 12 con Supabase (PostgreSQL + Supabase)
wslaragon site create mi-app --laravel=12 --supabase

# Ejemplo App Python/Node (Proxy puerto 8000)
wslaragon site create mi-app --proxy 8000 --no-php --no-mysql --ssl

# Ejemplo Node.js (Auto-puerto desde 3000)
wslaragon site create mi-api --node

# Ejemplo Python (Auto-puerto desde 8000)
# Ejemplo Python (Auto-puerto desde 8000)
wslaragon site create mi-script --python

# Ejemplo Vite React (Auto-puerto 3000+, npm install automático)
wslaragon site create mi-app-react --vite react

# Ejemplo Astro SSG (sitio estático, nginx sirve dist/, sin proceso)
wslaragon site create mi-astro --astro

# Astro con template específico
wslaragon site create mi-blog --astro=blog
wslaragon site create mi-minimal --astro=minimal

# Astro Headless — sitio API-driven con island architecture
wslaragon site create dash --astro=headless
# Luego agregar APIs dinámicamente:
wslaragon site api add dash /api https://api.dash.test/api
```

> **Astro SSG**: El sitio se compila a HTML estático (`npm run build` → `dist/`). Nginx sirve los archivos directamente, sin proxy ni proceso corriendo. Para desarrollo con HMR, ejecutá `npm run dev` manualmente desde la carpeta del proyecto.

**Opciones:**
- `--php / --no-php`: Habilitar o deshabilitar PHP-FPM.
- `--mysql / --no-mysql`: Crear o no una base de datos MySQL automática. **Para WordPress, `--mysql` se activa automáticamente** — no es necesario especificarlo.
- `--ssl / --no-ssl`: Generar certificado SSL local (Habilitado por defecto).
- `--html`: Crear sitio HTML estático con estructura completa (index.html, styles/estilos.css, js/app.js).
- `--wordpress`: Crear sitio WordPress completo con descarga automática. **Crea la base de datos MySQL automáticamente.**
- `--phpmyadmin`: Crear sitio phpMyAdmin para gestión visual de bases de datos.
- `--laravel=VERSIÓN`: Crear sitio Laravel (ej. `--laravel=12` para Laravel 12).
- `--postgres`: Usar PostgreSQL en lugar de MySQL para Laravel.
- `--supabase`: Usar Supabase (PostgreSQL + configuración Supabase) para Laravel.
- `--node`: Crear sitio para Node.js (asigna puerto libre automáticamente iniciando en 3000, deshabilita PHP/MySQL).
- `--python`: Crear sitio para Python (asigna puerto libre automáticamente iniciando en 8000, deshabilita PHP/MySQL).
- `--vite <template>`: Crear sitio Vite usando una plantilla (react, vue, svelte, vanilla, etc). Asigna puerto Node.
- `--astro`: Crear sitio Astro SSG. Usa template `basics` por defecto. Especificar template: `--astro=blog`, `--astro=minimal`, `--astro=headless`. Compila a estáticos en `dist/`, nginx sirve directamente sin proxy.
- `--proxy [PORT]`: Configurar como Proxy Inverso para Apps manuales en el puerto especificado.
- `--public`: Apuntar document root a directorio `public/`.
- `--database`: Nombre personalizado para la base de datos.

### 2. Listar Sitios
Muestra todos los sitios creados y su estado actual.

```bash
wslaragon site list
```

### 3. Borrar un Sitio
Elimina la configuración Nginx, SSL, y opcionalmente los archivos y la base de datos.

```bash
# Borrar sitio (pregunta si borrar archivos)
wslaragon site delete mi-web

# Borrar todo incluyendo base de datos
wslaragon site delete mi-web --remove-database

# Mantener archivos (responder No cuando pregunta)
wslaragon site delete mi-web
```

> **Nota**: El comando pregunta interactivamente si deseás eliminar los archivos del proyecto. La base de datos se elimina solo con `--remove-database`.

### 4. Habilitar / Deshabilitar
Activa o desactiva un sitio en Nginx sin borrarlo.

```bash
wslaragon site disable mi-web
wslaragon site enable mi-web
```

### 5. Reparar Permisos
Si tienes problemas de escritura (ej. WordPress no sube archivos, VSCode no puede guardar, logs, cache, uploads) o has copiado archivos desde Windows, usa este comando para reasignar el propietario y permisos.

```bash
wslaragon site fix-permissions mi-web
```

> Los permisos se corrigen automáticamente al crear un sitio. Usá este comando solo en sitios existentes que necesiten reparación.

**Qué hace:**
- `chown -R usuario:www-data` — el usuario puede editar desde VSCode, www-data (Nginx/PHP) puede leer y escribir
- `chmod -R 775` — owner y grupo con permisos completos
- `setgid` en directorios — nuevos archivos heredan el grupo `www-data`
- WordPress: agrega `FS_METHOD = 'direct'` a `wp-config.php`

### 6. API Proxies (Astro Headless / sitios API-driven)
Agrega o elimina proxies reversos Nginx por sitio. Ideal para sitios Astro headless que consumen APIs externas.

```bash
# Listar proxies de un sitio
wslaragon site api list dash

# Agregar un proxy: path local → backend URL
wslaragon site api add dash /api https://api.dash.test/api
wslaragon site api add dash /search https://search.dash.test/api

# Eliminar un proxy
wslaragon site api remove dash /api
```

> Los proxies se persisten en `sites.json` y la configuración Nginx se regenera automáticamente.

### 7. Configuración de Directorio Público (Laravel/Symfony)
Configura Nginx para servir el sitio desde el directorio `public/` en lugar de la raíz.

```bash
# Crear sitio directamente con soporte public/
wslaragon site create mi-blog --public

# O cambiar un sitio existente
wslaragon site public mi-blog --enable   # Apunta a public/
wslaragon site public mi-blog --disable  # Apunta a la raíz ./
```

### 8. Backup y Restauración
Para migrar sitios entre instalaciones o crear copias de seguridad.

```bash
# Exportar un sitio (archivos + base de datos + configuración)
wslaragon site export mi-web

# Exportar a una ruta específica
wslaragon site export mi-web --output /mnt/c/Backups/

# Importar un sitio desde un archivo de respaldo
wslaragon site import /mnt/c/Backups/mi-web_2024.wslaragon

# Importar con un nuevo nombre
wslaragon site import backup.wslaragon --name mi-web-copia
```

---

## 🔧 Gestión de Servicios (`service`)

Consulta el estado de Nginx, MySQL y PHP-FPM.

```bash
wslaragon service status
```

---

## 🐘 Gestión de PHP (`php`)

### 1. Configuración de runtime (ini)
Modifica valores comunes como límite de memoria o tamaño de subida sin editar archivos manualmente.

```bash
# Ver valores actuales
wslaragon php config list

# Cambiar un valor (reinicia FPM automáticamente)
wslaragon php config set upload_max_filesize 100M
wslaragon php config set memory_limit 512M

# Consultar valor específico
wslaragon php config get post_max_size
```

### 2. Versiones y Extensiones
```bash
# Listar versiones instaladas
wslaragon php versions

# Cambiar versión activa
wslaragon php switch 8.2

# Gestionar extensiones
wslaragon php enable_ext mbstring
wslaragon php disable_ext xdebug
```

---

## 🔒 Gestión de SSL (`ssl`)

Administra los certificados y la Autoridad de Certificación (CA).

```bash
# Listar certificados instalados
wslaragon ssl list

# Generar un nuevo certificado manualmente
wslaragon ssl generate midominio.test

# Eliminar un certificado y limpiar hosts de Windows
wslaragon ssl delete midominio.test
```

---

## 🚀 Gestión de Procesos Node (PM2) (`node`)

Para aplicaciones Node.js (Express, NestJS, etc.) o Python que requieren un servidor de aplicaciones persistente, `wslaragon` integra PM2.

> **Nota**: Cuando creas un sitio con `--node`, se genera un archivo `app.js` básico de prueba. Debes reemplazarlo con tu propio proyecto (ej. `npm init`, `npm create vite`, clonar repo) y luego iniciar el proceso.

### 1. Listar procesos
```bash
wslaragon node list
```

### 2. Iniciar aplicación
Detecta automáticamente `app.js`, `main.py` o `npm start` en la carpeta del sitio.
```bash
wslaragon node start mi-app-node
```



### 3. Detener, Reiniciar y Eliminar
```bash
wslaragon node stop mi-app-node
wslaragon node restart mi-app-node
wslaragon node delete mi-app-node   # Elimina el proceso de la lista
```

---

## 🩺 Diagnóstico (`doctor`)

Si algo no funciona bien, el doctor es tu primer paso. Verifica servicios caídos, configuraciones erróneas y certificados faltantes.

```bash
wslaragon doctor
```

**Lo que verifica:**
- Estado de Nginx, MySQL, PHP-FPM, Redis.
- Si los puertos (80, 443, 3306, 6379) están escuchando.
- Validez de la Autoridad de Certificación (SSL CA).
- Integridad de archivos de configuración.

---

## 🤖 Agentes IA (`agent`)

Prepara tu proyecto para trabajar con Agentes de IA, generando una estructura estandarizada de "Skills" (Habilidades) en la carpeta `.agent/`.

### 1. Inicializar estructura (`agent init`)

Prepara el directorio actual con una estructura de carpetas estándar (`.agent/`) que incluye:
- `skills/`: Habilidades de los agentes.
- `memory/`: Memoria del proyecto (Contexto, Arquitectura, Decisiones).
- `ui/assets/`: Recursos visuales para el skill UI Designer.
- `specs/`: Documentos de requerimientos.
- `qa/`: Planes de prueba.

```bash
# Preset básico (incluye Product Analyst, Architect, Git Manager, Librarian, UI Designer)
wslaragon agent init

# Preset para Laravel (Laravel Architect, Test Engineer...)
wslaragon agent init --preset laravel

# Preset para JavaScript/Node (Frontend Architect, Node Specialist...)
wslaragon agent init --preset javascript

# Preset Meta (Generador de Skills)
wslaragon agent init --preset meta
```
**Presets disponibles:** `default`, `laravel`, `wordpress`, `python`, `javascript`, `meta`.

### 2. Importar Skills Externos (`agent import`)

Descarga e instala una nueva habilidad desde una URL remota (ej. GitHub Gist, Raw File).

```bash
# Importar un skill desde una URL raw
wslaragon agent import https://raw.githubusercontent.com/user/repo/main/my_skill.md
```
Esto creará una nueva carpeta en `.agent/skills/` con el contenido descargado.

---

> **Tip:** Puedes escribir `wslaragon --help` en cualquier momento para ver la ayuda integrada del comando.

---

## ⌨️ Autocompletado

Para habilitar el autocompletado en tu terminal (Bash/Zsh):

```bash
# Instalar automáticamente
wslaragon completion --install
```

O para ver el script manual:
```bash
wslaragon completion
```

---

## ℹ️ Glosario Interactivo

Accede a la documentación completa directamente desde la terminal.

```bash
# Ver el glosario completo
wslaragon --glossary
# o usar el alias corto
wslaragon -g

# Buscar/Filtrar por término
wslaragon glossary node   # Muestra solo la sección de Node/PM2
wslaragon glossary php    # Muestra solo la sección de PHP
```
