# 📖 Guía del CLI (Comandos)

El comando principal es `wslaragon`. Aquí tienes todos los comandos disponibles y ejemplos de uso.

## 📁 Gestión de Sitios (`site`)

### 1. Crear un Sitio
Crea un nuevo proyecto con configuración de Nginx, base de datos y SSL.

```bash
# Ejemplo básico (PHP + MySQL + SSL)
wslaragon site create mi-web --php --mysql --ssl

# Ejemplo solo HTML estático
wslaragon site create landing --php=false --mysql=false
```

**Opciones:**
- `--php / --no-php`: Habilitar o deshabilitar PHP-FPM.
- `--mysql / --no-mysql`: Crear o no una base de datos automática.
- `--ssl / --no-ssl`: Generar certificado SSL local.

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

---

## 🔧 Gestión de Servicios (`service`)

Consulta el estado de Nginx, MySQL y PHP-FPM.

```bash
wslaragon service status
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

> **Tip:** Puedes escribir `wslaragon --help` en cualquier momento para ver la ayuda integrada del comando.
