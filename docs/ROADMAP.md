# 🗺️ Roadmap de WSLaragon

Este documento detalla las próximas funciones y mejoras planificadas para evolucionar WSLaragon hacia una herramienta de alto rendimiento y versatilidad.

## 🚀 Fase 1: Automatización de Frameworks (Próximamente)
Facilitar el despliegue de tecnologías comunes con un solo comando.

- [ ] **WordPress Auto-Installer**: Crear sitio + Descargar WP + Configurar `wp-config.php` automáticamente.
- [ ] **Laravel Auto-Installer**: Crear sitio + Composer create-project + Generar `.env`.
- [ ] **Static Boilerplates**: Plantillas rápidas para Tailwind, Bootstrap o simplemente HTML limpio.

## 🟢 Fase 2: Ecosistema Node.js
Expandir WSLaragon más allá de PHP para soportar el desarrollo moderno de JavaScript.

- [ ] **Gestor de Aplicaciones Node**: Soporte para lanzar apps de Express, Next.js, etc.
- [ ] **Proxy Inverso Automático**: Configurar Nginx para redirigir dominios `.test` hacia puertos específicos de Node.
- [ ] **Integración con PM2**: Gestión persistente de procesos Node desde el CLI.

## ⚡ Fase 3: Alto Rendimiento (Stack Avanzado)
Inspirado en CloudPanel, queremos ofrecer una infraestructura de caché de nivel empresarial en WSL2.

- [ ] **Integración con Redis**:
    - Servicio de Redis pre-configurado para WSLaragon.
    - Soporte para Object Cache en WordPress y Laravel via Redis.
- [ ] **Varnish Cache Integration**:
    - Implementación de Varnish como proxy de caché delante de Nginx.
    - Plantillas de configuración (.vcl) optimizadas para sitios dinámicos.
- [ ] **Stack "Elite"**: Configuración de un click para el stack: `Varnish -> Nginx -> Redis -> PHP/Node`.

## 🛠️ Fase 4: Experiencia de Usuario Pro
Mejoras en la usabilidad y diagnóstico del sistema.

- [ ] **Doctor Command**: `wslaragon doctor` para detectar problemas de puertos, permisos o servicios caídos.
- [ ] **Backup System**: Comandos para exportar e importar rápidamente sitios completos (Archivos + DB).
- [ ] **Site Templates**: Capacidad de crear tus propias plantillas de sitio personalizadas.

---

> [!NOTE]
> Este roadmap es dinámico y evolucionará según el feedback de la comunidad. ¡Cada contribución nos acerca a ser la mejor alternativa a Laragon en Linux!
