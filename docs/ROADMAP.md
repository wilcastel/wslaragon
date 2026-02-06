# 🗺️ Roadmap de WSLaragon

Este documento detalla las funciones implementadas y las mejoras planificadas para el futuro.

## ✅ Completado Recientemente

### 🛠️ Infraestructura y Configuración
- [x] **Gestión Dinámica de Configuración PHP**: Modificar `php.ini` desde el CLI (`memory_limit`, `upload_max_filesize`).
- [x] **Configuración Nginx Avanzada**: Aumento del límite de subida (`client_max_body_size`) para soportar archivos grandes (50MB+).
- [x] **Correcciones de CSP y Alpine.js**: Solución de problemas de `Content Security Policy` para permitir la correcta ejecución de Alpine.js y otros scripts en la interfaz.
- [x] **Reparación de Permisos**: Comando `fix-permissions` para solucionar problemas de escritura.

### 💻 Interfaz y Experiencia de Usuario (UI/UX)
- [x] **Dashboard de Gestión de Servicios**: Nueva página `/feeds/manage` para monitorear el estado de workers y reiniciar servicios fallidos directamente desde la web.
- [x] **Navegación Mejorada en Sidebar**: Carpetas clicables, acciones de "Marcar todo como leído" por carpeta y opciones de vaciado.
- [x] **Flujo de Lectura Continuo**: Redirección automática al siguiente feed o carpeta al marcar todo como leído.

### 🤖 IA y Voice Cloning
- [x] **Soporte para Voice Cloning**: Ajustes en Nginx para permitir subidas de audio grandes y correcciones en la integración con Python.
- [x] **Colab Standalone Updates**: Mejoras en el notebook de Colab (timers, stats de VRAM) para procesamiento remoto.

### 📦 Frameworks y Bases de Datos
- [x] **Laravel con Supabase**: Comando `--supabase` para integración rápida.
- [x] **Soporte Laravel/Public**: Opción para servir sitios desde `public/`.
- [x] **Laravel con PostgreSQL**: Comando `--postgres`.
- [x] **WordPress Auto-Installer**: Comando `--wordpress`.

---

## 🚀 Próximos Pasos (En Progreso)

### Fase 1: Estabilización y Monitoreo (Actual)
- [ ] **Refinar Dashboard de Servicios**: Añadir logs en tiempo real y estadísticas de uso de memoria en la interfaz `/feeds/manage`.
- [ ] **WSLaragon Doctor Extendido**: Diagnóstico más profundo para problemas de SSL y conectividad de base de datos.
- [ ] **Integración de .agent/skills**: Nuevo comando `wslaragon agent init [preset]` para inicializar estructura de skills en proyectos.
    - **Presets Comunes**: Skills base para todos los proyectos (Product Analyst, Architect, Git Manager).
    - **Presets Específicos**: Skills adaptados según tecnología (Laravel Specialist, WordPress Expert, Data Scientist para Python).
- [ ] **Meta-Skill "Skill Creator"**: Un agente experto capaz de entrevistar al usuario para diseñar y generar nuevos skills `.md` automáticamente.

### Fase 2: Gestión de Memoria y Project Context (Nuevo)
- [ ] **Project Memory**: Sistema para resumir y guardar el estado del proyecto en archivos (ej. `.agent/memory/`) para liberar tokens de contexto.
- [ ] **Repositorio de Skills Centralizado**: Capacidad de importar skills desde un repo remoto (inspirado en skills.sh).
- [ ] **Organización Modular**: Carpetas específicas para Requerimientos, UI, QA dentro de `.agent/`.

### Fase 3: Ecosistema Node.js (Pendiente)
- [ ] **Gestor de Aplicaciones Node**: Soporte nativo para iniciar y gestionar procesos de Node.js (PM2 o similar integrado).
- [ ] **Proxy Inverso Automático**: Redirigir dominios `.test` a puertos locales (3000, 5173, etc).

### Fase 4: Alto Rendimiento (Pendiente)
Inspirado en CloudPanel:
- [ ] **Integración con Redis**: Servicio de Redis pre-configurado y comando para activarlo por sitio.
- [ ] **Varnish Cache**: Capa de caché HTTP opcional para sitios de alto tráfico.

### Fase 5: Herramientas Pro
- [ ] **Sistema de Backups**: Comandos para exportar/importar sitios completos (código + BD).
- [ ] **Entornos de Staging**: Clonar un sitio localmente para pruebas seguras (ej. `mi-sitio-staging.test`).

