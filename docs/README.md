# 🚀 WSLaragon

> **Tu Entorno de Desarrollo Web Profesional en WSL2**

WSLaragon es un ecosistema potente diseñado para transformar Windows + WSL2 en un entorno de desarrollo web profesional, rápido y automatizado. Combina la facilidad de uso de Laragon con la potencia nativa de Linux.

## ✨ Características Principales

- 🐧 **Linux Nativo**: Corre directamente sobre WSL2 (Ubuntu 22.04+).
- ⚡ **Velocidad Extrema**: Sin las capas de lentitud de los sistemas archivos compartidos tradicionales.
- 🌐 **Dominios .test**: Gestión automática de dominios locales estilo Laragon.
- 🔒 **SSL/HTTPS Real**: Certificados válidos con candado verde automáticos.
- 📦 **Frameworks Listos**: Comandos integrados para crear sitios con PHP, MySQL, PostgreSQL, WordPress, Laravel o HTML estático.
- 🛠️ **CLI Moderno**: Un comando único `wslaragon` para controlarlo todo.
- 🔐 **Seguridad**: Configuración flexible mediante archivos `.env`.
- 🗄️ **Multi-Base de Datos**: Soporte para MySQL, PostgreSQL y Supabase (PostgreSQL as a Service local).

## 📂 Índice de Documentación

1.  [**Guía de Instalación**](INSTALL.md): Requisitos y configuración inicial paso a paso.
2.  [**Uso del CLI**](CLI.md): Listado completo de comandos y cómo crear tu primer sitio.
3.  [**SSL y Base de Datos**](SSL-DB.md): Cómo confiar en el certificado en Windows y configurar MariaDB.
4.  [**Arquitectura**](STRUCTURE.md): Entiende cómo se organiza el proyecto y dónde están tus archivos.
5.  [**Solución de Problemas**](TROUBLESHOOTING.md): Diagnóstico y soluciones para errores comunes (502, queue workers, MySQL).
6.  [**Roadmap**](ROADMAP.md): Próximas funciones planificadas (Node.js, Redis, Varnish).

## 🚀 Inicio Rápido (60 segundos)

Si ya tienes instalado WSLaragon, crear un sitio es tan fácil como:

```bash
wslaragon site create mi-proyecto --php --mysql --ssl
```

**🌐 Acceso:** `https://mi-proyecto.test`  
**📂 Código en:** `~/web/mi-proyecto`  

---

**¡Bienvenido al futuro del desarrollo web en Windows!** 🚀