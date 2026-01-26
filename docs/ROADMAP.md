# 🗺️ Roadmap de WSLaragon

Este documento detalla las próximas funciones y mejoras planificadas.

## ✅ Completado Recientemente
- [x] **Gestión Dinámica de Configuración PHP**: Modificar `php.ini` desde el CLI (`memory_limit`, `upload_max_filesize`).
- [x] **Soporte Laravel/Public**: Opción para servir sitios desde el directorio `public/` en lugar de la raíz.
- [x] **Reparación de Permisos**: Comando `fix-permissions` para solucionar problemas de escritura en archivos copiados desde Windows.
- [x] **Validaciones de Seguridad**: Mejor manejo de credenciales `sudo` para evitar bloqueos en la interfaz.

## 🚀 Fase 1: Automatización de Frameworks
- [ ] **WordPress Auto-Installer**: Crear sitio + Descargar WP + Configurar `wp-config.php`.
- [ ] **Laravel Auto-Installer**: Integrar `composer create-project` directamente.
- [ ] **Static Boilerplates**: Plantillas rápidas HTML/Tailwind.

## 🟢 Fase 2: Ecosistema Node.js
- [ ] **Gestor de Aplicaciones Node**: Soporte para Express, Next.js.
- [ ] **Proxy Inverso Automático**: Redirigir dominios `.test` a puertos Node (ej. 3000).

## ⚡ Fase 3: Alto Rendimiento
Inspirado en CloudPanel:
- [ ] **Integración con Redis**: Servicio pre-configurado para Object Cache.
- [ ] **Varnish Cache**: Proxy de caché delante de Nginx.

## 🛠️ Fase 4: Experiencia Pro
- [ ] **Doctor Command**: `wslaragon doctor` para diagnóstico.
- [ ] **Backup System**: Exportar/Importar sitios completos.

