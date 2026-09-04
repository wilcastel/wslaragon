# 🚀 WSLaragon

> **Tu entorno de desarrollo web en Omarchy y WSL2**

WSLaragon combina la facilidad de Laragon con servicios Linux nativos. En
Omarchy, la variante del entorno se denomina Omarchygon.

## ✨ Características Principales

- 🐧 **Linux Nativo**: Funciona sobre Omarchy o WSL2 (Ubuntu 22.04+).
- ⚡ **Velocidad Extrema**: Sin las capas de lentitud de los sistemas archivos compartidos tradicionales.
- 🌐 **Dominios .test**: Gestión automática de dominios locales estilo Laragon.
- 🔒 **SSL/HTTPS Real**: Certificados válidos con candado verde automáticos (CN correcto + SANs).
- 📦 **Frameworks Listos**: Comandos integrados para crear sitios con PHP, MySQL, PostgreSQL, WordPress, Laravel, phpMyAdmin, Vite, Astro (SSG) o HTML estático.
- 🔗 **Sitios Headless Pareados**: Un solo comando (`--headless`) crea un frontend (SvelteKit/Astro) y su backend/API (WordPress/Laravel) enlazados.
- 🛠️ **CLI Moderno**: Un comando único `wslaragon` para controlarlo todo.
- 🔐 **Seguridad**: Configuración flexible mediante archivos `.env`.
- 🗄️ **Multi-Base de Datos**: Soporte para MySQL, PostgreSQL y Supabase (PostgreSQL as a Service local).

## 📂 Índice de Documentación

1.  [**Instalación en Omarchy**](OMARCHY.md): Instalador único, runtime y componentes de Omarchygon.
2.  [**Guía de Instalación WSL2**](INSTALL.md): Configuración para Ubuntu/Windows y CA root.
3.  [**Clonar proyectos**](CLONE.md): Migración desde Git, `.env`, dependencias, bases y PM2.
4.  [**Uso del CLI**](CLI.md): Listado completo de comandos y cómo crear tu primer sitio.
5.  [**SSL y Base de Datos**](SSL-DB.md): Certificados y gestión de bases de datos.
6.  [**Arquitectura**](STRUCTURE.md): Organización del proyecto y archivos.
7.  [**Servidor MCP**](MCP.md): Uso desde clientes MCP.
8.  [**Solución de Problemas**](TROUBLESHOOTING.md): Errores comunes y recuperación.
9.  [**Roadmap**](ROADMAP.md): Funciones implementadas y futuras.
10. [**Contribuir**](CONTRIBUTING.md): Guía para contribuir.
11. [**Desarrollo**](DEVELOPMENT.md): Documentación interna.

## 🚀 Inicio Rápido (60 segundos)

Si ya tienes instalado WSLaragon, crear un sitio es tan fácil como:

```bash
# Sitio WordPress con base de datos automática
wslaragon site create mi-blog --wordpress

# Sitio Laravel con MySQL
wslaragon site create mi-app --laravel=12 --mysql

# phpMyAdmin para gestionar bases de datos
wslaragon site create pma --phpmyadmin

# Sitio PHP simple
wslaragon site create mi-proyecto --php --mysql
```

**🌐 Acceso:** `https://mi-blog.test` | `https://pma.test`
**📂 Código en:** `~/web/mi-blog` | `~/web/pma`

> **⚠️ Importante**: Para que el candado SSL 🔒 aparezca en tu navegador, debés instalar la CA root en Windows. Ver la [Guía de Instalación](INSTALL.md#4-instalar-la-ca-root-para-ssl-️-importante).

---

**¡Bienvenido a WSLaragon / Omarchygon!** 🚀
