# 🗺️ Roadmap de WSLaragon

Este documento detalla las funciones implementadas y las mejoras planificadas para el futuro.

## ✅ Completado Recientemente

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
- [x] **WordPress Auto-Installer**: Comando `--wordpress`.

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

