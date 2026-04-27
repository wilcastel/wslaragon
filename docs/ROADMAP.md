# 🗺️ Roadmap de WSLaragon

Este documento detalla las funciones implementadas y las mejoras planificadas para el futuro.

## ✅ Completado Recientemente

### 🔒 SSL Mejorado
- [x] **Certificados con CN correcto**: Generación con openssl (no solo mkcert) para incluir el dominio en el campo CN del certificado.
- [x] **Auto-instalación de CA root**: Instalación automática de la CA root en el almacén de certificados de Windows (con elevación UAC).
- [x] **SAN completos**: Los certificados incluyen DNS + IP (127.0.0.1) como Subject Alternative Names.

### 🗄️ Base de Datos
- [x] **WordPress con MySQL automático**: El flag `--wordpress` ahora crea la base de datos MySQL automáticamente sin necesidad de `--mysql`.
- [x] **phpMyAdmin**: Nuevo tipo de sitio `--phpmyadmin` para gestión visual de bases de datos MySQL.
- [x] **Configuración generated**: El `wp-config.php` de WordPress y `config.inc.php` de phpMyAdmin se generan con las credenciales del `.env`.

### 🛠️ Infraestructura y Configuración
- [x] **Gestión Dinámica de Configuración PHP**: Modificar `php.ini` desde el CLI (`memory_limit`, `upload_max_filesize`).
- [x] **Configuración Nginx Avanzada**: Aumento del límite de subida (`client_max_body_size`) para soportar archivos grandes (50MB+).
- [x] **Correcciones de CSP y Alpine.js**: Solución de problemas de `Content Security Policy` para permitir la correcta ejecución de Alpine.js y otros scripts en la interfaz.
- [x] **Reparación de Permisos**: Comando `fix-permissions` para solucionar problemas de escritura.

### 💻 CLI y Experiencia de Desarrollador (DX)
- [x] **Gestión intuitiva**: Comandos simplificados para crear/eliminar sitios y servicios.



### 📦 Frameworks y Bases de Datos
- [x] **Laravel con Supabase**: Comando `--supabase` para integración rápida.
- [x] **Soporte Laravel/Public**: Opción para servir sitios desde `public/`.
- [x] **Laravel con PostgreSQL**: Comando `--postgres`.
- [x] **WordPress Auto-Installer**: Comando `--wordpress` (con MySQL automático).
- [x] **phpMyAdmin**: Comando `--phpmyadmin` para gestión visual de bases de datos.

---

## 🚀 Próximos Pasos (En Progreso)

### Fase 1: Estabilización y Monitoreo (Completado)
- [x] **WSLaragon Service Monitor**: Comando `wslaragon services status` mejorado para ver estado real de Nginx, PHP, MariaDB y Redis.
- [x] **WSLaragon Doctor Extendido**: Diagnóstico más profundo para problemas de SSL y conectividad de base de datos.
- [x] **Integración de .agent/skills**: Nuevo comando `wslaragon agent init [preset]` para inicializar estructura de skills en proyectos.
    - **Presets Comunes**: Skills base para todos los proyectos (Product Analyst, Architect, Git Manager).
    - **Presets Específicos**: Skills adaptados según tecnología (Laravel Specialist, WordPress Expert, Data Scientist para Python).
- [x] **Meta-Skill "Skill Creator"**: Un agente experto capaz de entrevistar al usuario para diseñar y generar nuevos skills `.md` automáticamente.

### Fase 2: Gestión de Memoria y Project Context (Completado)
- [x] **Project Memory**: Sistema para resumir y guardar el estado del proyecto en archivos (ej. `.agent/memory/`) para liberar tokens de contexto.
- [x] **Organización Modular**: Carpetas específicas para Requerimientos (`specs/`), UI (`ui/`), QA (`qa/`) y skill **UI Designer** para implementar diseños desde imágenes.
- [x] **Importación de Skills**: Comando `wslaragon agent import <url>` para instalar skills desde cualquier URL (Github, Gists, etc).

### Fase 3: Ecosistema Node.js (Completado)
- [x] **Gestor de Aplicaciones Node**: Integración completa con PM2 (`wslaragon node ...`).
- [x] **Proxy Inverso Automático**: Redirección automática a puertos locales con protección de colisiones.
- [x] **CLI Node**: Flags `--node` y `--python` para scaffolding rápido y auto-asignación de puertos.

### Fase 4: Productividad y Seguridad (Completado)
- [x] **Soporte Redis**: Integración en monitor de servicios y diagnósticos (`wslaragon doctor` y `service status`).
- [x] **Sistema de Backups**: Exportación e importación de sitios completos (Archivos + BD + Config) para migración sencilla entre equipos (`wslaragon site export/import`).

### Fase 5: Herramientas Frontend (En Progreso)
- [x] **Advanced Scaffolding**: Integración con Vite para crear proyectos React, Vue, Svelte, etc. (`--vite <template>`) con configuración automática de puertos y SSL.
- [ ] **Project Templates**: Plantillas personalizadas para arrancar proyectos rápidos.

### Fase 6: Calidad y CI/CD (Completado)
- [x] **Cobertura de Tests 99.85%**: 1,114 tests (1,083 unitarios + 31 integración)
- [x] **Strategy Pattern**: Refactor de SiteManager.create_site() — de God Object a 8 creadores
- [x] **Seguridad**: Sin shell=True, sin SQL injection, path traversal protection en backups
- [x] **CI/CD Pipeline**: GitHub Actions con lint + test + build por versión de Python
- [x] **Pre-commit Hooks**: ruff + black + isort + mypy
- [x] **Coverage Threshold**: Mínimo 90% para pasar CI

