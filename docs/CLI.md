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

# Ejemplo WordPress completo
wslaragon site create mi-blog --wordpress --mysql

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
wslaragon site create mi-script --python
```

**Opciones:**
- `--php / --no-php`: Habilitar o deshabilitar PHP-FPM.
- `--mysql / --no-mysql`: Crear o no una base de datos MySQL automática.
- `--ssl / --no-ssl`: Generar certificado SSL local.
- `--html`: Crear sitio HTML estático con estructura completa (index.html, styles/estilos.css, js/app.js).
- `--wordpress`: Crear sitio WordPress completo con descarga automática.
- `--laravel=VERSIÓN`: Crear sitio Laravel (ej. `--laravel=12` para Laravel 12).
- `--postgres`: Usar PostgreSQL en lugar de MySQL para Laravel.
- `--supabase`: Usar Supabase (PostgreSQL + configuración Supabase) para Laravel.
- `--node`: Crear sitio para Node.js (asigna puerto libre automáticamente iniciando en 3000, deshabilita PHP/MySQL).
- `--python`: Crear sitio para Python (asigna puerto libre automáticamente iniciando en 8000, deshabilita PHP/MySQL).
- `--proxy [PORT]`: Configurar como Proxy Inverso para Apps manuales en el puerto especificado.
- `--public`: Apuntar document root a directorio `public/`.
- `--database`: Nombre personalizado para la base de datos.

### 2. Listar Sitios
Muestra todos los sitios creados y su estado actual.

```bash
wslaragon site list
```

### 3. Borrar un Sitio
Elimina la configuración y, opcionalmente, los archivos y la base de datos.

```bash
# Borrar solo configuración
wslaragon site delete mi-web

# Borrar todo (archivos + base de datos)
wslaragon site delete mi-web --remove-files --remove-database
```

### 4. Habilitar / Deshabilitar
Activa o desactiva un sitio en Nginx sin borrarlo.

```bash
wslaragon site disable mi-web
wslaragon site enable mi-web
```

### 5. Reparar Permisos
Si tienes problemas de escritura (ej. logs, cache, uploads) o has copiado archivos desde Windows, usa este comando para reasignar el propietario y permisos.

```bash
wslaragon site fix-permissions mi-web
```

### 6. Configuración de Directorio Público (Laravel/Symfony)
Configura Nginx para servir el sitio desde el directorio `public/` en lugar de la raíz.

```bash
# Crear sitio directamente con soporte public/
wslaragon site create mi-blog --public

# O cambiar un sitio existente
wslaragon site public mi-blog --enable   # Apunta a public/
wslaragon site public mi-blog --disable  # Apunta a la raíz ./
```

### 7. Backup y Restauración
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
wslaragon ssl create midominio.test
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

### 3. Detener y Reiniciar
```bash
wslaragon node stop mi-app-node
wslaragon node restart mi-app-node
```

---

## 🩺 Diagnóstico (`doctor`)

Si algo no funciona bien, el doctor es tu primer paso. Verifica servicios caídos, configuraciones erróneas y certificados faltantes.

```bash
wslaragon doctor
```

**Lo que verifica:**
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
