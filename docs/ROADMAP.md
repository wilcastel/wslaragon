# 🗺️ Roadmap de WSLaragon

Este documento detalla las próximas funciones y mejoras planificadas.

## ✅ Completado Recientemente
- [x] **Gestión Dinámica de Configuración PHP**: Modificar `php.ini` desde el CLI (`memory_limit`, `upload_max_filesize`).
- [x] **Soporte Laravel/Public**: Opción para servir sitios desde el directorio `public/` en lugar de la raíz.
- [x] **Reparación de Permisos**: Comando `fix-permissions` para solucionar problemas de escritura en archivos copiados desde Windows.
- [x] **Validaciones de Seguridad**: Mejor manejo de credenciales `sudo` para evitar bloqueos en la interfaz.
- [x] **Static HTML Boilerplate**: Comando `--html` para crear sitios HTML estáticos con estructura completa.
- [x] **WordPress Auto-Installer**: Comando `--wordpress` para crear sitios WordPress completos.
- [x] **Laravel Auto-Installer**: Comando `--laravel=VERSIÓN` para crear sitios Laravel con Composer.
- [x] **Laravel con PostgreSQL**: Comando `--postgres` para Laravel con base de datos PostgreSQL.
- [x] **Laravel con Supabase**: Comando `--supabase` para Laravel con Supabase (PostgreSQL + Supabase config).

## 🚀 Fase 1: Automatización de Frameworks
- [x] ~~WordPress Auto-Installer~~: ~~Crear sitio + Descargar WP + Configurar `wp-config.php`.~~
- [x] ~~Laravel Auto-Installer~~: ~~Integrar `composer create-project` directamente.~~
- [x] ~~Static Boilerplates~~: ~~Plantillas rápidas HTML/Tailwind.~~
- [x] ~~Soporte PostgreSQL~~: ~~Opción `--postgres` para Laravel.~~
- [x] ~~Soporte Supabase~~: ~~Opción `--supabase` para Laravel con Supabase.~~

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

