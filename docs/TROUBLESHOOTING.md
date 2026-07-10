# 🔧 Guía de Solución de Problemas

## Servicios No Arrancan (502/Error de Conexión)

### Verificar Estado de Servicios

```bash
# Ver estado general
wslaragon service status

# Ver servicios systemd específicos
sudo systemctl status nginx
sudo systemctl status mysql
sudo systemctl status php8.3-fpm
```

### Servicios Caen o No Responden (502 Bad Gateway)

El error 502 típicamente significa que Nginx está funcionando pero el backend no.

#### Caso 1: Aplicación Python/Node no está corriendo

```bash
# Verificar si hay procesos en el puerto esperado
sudo lsof -i :8000  # Para apps Python (ejemplo)
sudo lsof -i :3000  # Para apps Node

# Si no hay nada, iniciar la aplicación
cd ~/web/mi-proyecto
./start.sh
# O
python app.py &
```

#### Caso 2: MySQL no está corriendo

```bash
# Verificar si MySQL acepta conexiones
sudo service mysql status

# Iniciar MySQL
sudo service mysql start

# Habilitar auto-arranque
sudo systemctl enable mysql
```

### Queue Worker de Laravel No Funciona

Si usas `QUEUE_CONNECTION=database` y los jobs no se procesan, lo más práctico es correr el queue worker como un servicio systemd propio (WSLaragon no gestiona esto automáticamente). Reemplazá `<mi-app>` por el nombre de tu sitio y `<usuario>` por tu usuario del sistema:

```bash
# Verificar estado del servicio de queue
sudo systemctl status mi-app-worker.service

# Reiniciar si está fallido
sudo systemctl restart mi-app-worker.service

# Ver logs del servicio
sudo journalctl -u mi-app-worker.service -f

# Ver logs de Laravel
tail -f ~/web/<mi-app>/storage/logs/laravel.log

# Si el servicio no existe, crear uno:
sudo nano /etc/systemd/system/mi-app-worker.service
```

**Contenido típico del servicio:**
```ini
[Unit]
Description=Laravel Queue Worker (<mi-app>)
After=network.target mysql.service

[Service]
Type=simple
User=<usuario>
WorkingDirectory=/home/<usuario>/web/<mi-app>
ExecStart=/usr/bin/php artisan queue:work --daemon --sleep=3 --tries=3
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Activar el servicio
sudo systemctl daemon-reload
sudo systemctl enable mi-app-worker
sudo systemctl start mi-app-worker
```

---

## Problemas Comunes y Soluciones

| Problema | Causa | Solución |
|----------|-------|----------|
| 502 Bad Gateway | Backend no corriendo | Iniciar la app o verificar el puerto |
| 502 en Astro SSG | No aplica — SSG no usa backend | Verificar que `dist/` existe y nginx apunta ahí |
| "Connection refused" (MySQL) | MySQL detenido | `sudo service mysql start` |
| Jobs no se procesan | Queue worker detenido | `sudo systemctl restart mi-app-worker` |
| SSL no funciona | Puerto 443 ocupado | Verificar que no haya otro nginx |
| "Permission denied" en Nginx | Home directory sin permisos | `chmod 755 $HOME` o `wslaragon site fix-permissions mi-sitio` |
| WordPress no puede subir archivos | Permisos incorrectos | `sudo wslaragon site fix-permissions mi-sitio` |
| VSCode no puede guardar archivos | Permisos incorrectos | `sudo wslaragon site fix-permissions mi-sitio` |
| SSL muestra "No seguro" en navegador | CA root no instalada en Windows | Ver [Guía de Instalación → Paso 4](INSTALL.md#4-instalar-la-ca-root-para-ssl-️-importante) |
| Certificado CN dice "mkcert development" | Certificado viejo generado con mkcert puro | Regenerar con `wslaragon ssl generate dominio.test` |
| WordPress muestra "Error establishing a database" | Base de datos no creada | `wslaragon site create blog --wordpress` (ya crea la DB automáticamente) |
| Archivos creados en `/root/web/` con sudo | Bug de HOME en versiones anteriores | Actualizar WSLaragon: `pip install -e .` |

---

## Verificar Logs

```bash
# Logs de Nginx
tail -f /var/log/nginx/error.log

# Logs de sitio específico
tail -f /var/log/nginx/mi-sitio.test.error.log

# Logs de Laravel
tail -f ~/web/<mi-app>/storage/logs/laravel.log

# Logs de aplicaciones Python/Node
tail -f ~/web/<mi-app>/<mi-app>.log
```

---

## Reiniciar Todo el Stack

```bash
# Reiniciar servicios
sudo service nginx restart
sudo service mysql restart
sudo systemctl restart php8.3-fpm

# Reiniciar queue workers
sudo systemctl restart mi-app-worker.service
```
