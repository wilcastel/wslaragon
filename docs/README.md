# 🚀 WSLaragon

> **Tu Entorno de Desarrollo Web Profesional en WSL2**

WSLaragon es un ecosistema potente diseñado para transformar Windows + WSL2 en un entorno de desarrollo web profesional, rápido y automatizado. Combina la facilidad de uso de Laragon con la potencia nativa de Linux.

## ✨ Características Principales

- 🐧 **Linux Nativo**: Corre directamente sobre WSL2 (Ubuntu 22.04+).
- ⚡ **Velocidad Extrema**: Sin las capas de lentitud de los sistemas archivos compartidos tradicionales.
- 🌐 **Dominios .test**: Gestión automática de dominios locales estilo Laragon.
- 🔒 **SSL/HTTPS Real**: Certificados válidos con candado verde automáticos (CN correcto + SANs).
- 📦 **Frameworks Listos**: Comandos integrados para crear sitios con PHP, MySQL, PostgreSQL, WordPress, Laravel, phpMyAdmin o HTML estático.
- 🛠️ **CLI Moderno**: Un comando único `wslaragon` para controlarlo todo.
- 🔐 **Seguridad**: Configuración flexible mediante archivos `.env`.
- 🗄️ **Multi-Base de Datos**: Soporte para MySQL, PostgreSQL y Supabase (PostgreSQL as a Service local).

## 📂 Índice de Documentación

1.  [**Guía de Instalación**](INSTALL.md): Requisitos, configuración inicial paso a paso y **instalación de CA root para SSL**.
2.  [**Uso del CLI**](CLI.md): Listado completo de comandos y cómo crear tu primer sitio.
3.  [**SSL y Base de Datos**](SSL-DB.md): Cómo confiar en el certificado en Windows, generación de certificados y gestión de bases de datos.
4.  [**Arquitectura**](STRUCTURE.md): Entiende cómo se organiza el proyecto y dónde están tus archivos.
5.  [**Solución de Problemas**](TROUBLESHOOTING.md): Diagnóstico y soluciones para errores comunes (502, permisos, SSL, MySQL).
6.  [**Roadmap**](ROADMAP.md): Próximas funciones planificadas (Node.js, Redis, Varnish).
7.  [**Contribuir**](CONTRIBUTING.md): Guía para desarrolladores que quieren contribuir.
8.  [**Desarrollo**](DEVELOPMENT.md): Documentación interna para desarrolladores.

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

**¡Bienvenido al futuro del desarrollo web en Windows!** 🚀