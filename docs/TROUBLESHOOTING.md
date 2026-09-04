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
| WordPress no puede subir archivos | Permisos incorrectos | `wslaragon site fix-permissions mi-sitio --check` y luego `wslaragon site fix-permissions mi-sitio` |
| VSCode no puede guardar archivos | Permisos incorrectos | `wslaragon site fix-permissions mi-sitio --check` y luego `wslaragon site fix-permissions mi-sitio` |
| MariaDB está `running` en Docker pero rechaza `127.0.0.1:3306` | El contenedor perdió su conexión a la red `bridge` | `sudo docker network connect bridge mariadb11 && sudo docker restart mariadb11` |
| SSL muestra "No seguro" en navegador | CA root no instalada en Windows | Ver [Guía de Instalación → Paso 4](INSTALL.md#4-instalar-la-ca-root-para-ssl-️-importante) |
| Certificado CN dice "mkcert development" | Certificado viejo generado con mkcert puro | Regenerar con `wslaragon ssl generate dominio.test` |
| WordPress muestra "Error establishing a database" | Base de datos no creada | `wslaragon site create blog --wordpress` (ya crea la DB automáticamente) |
| Archivos creados en `/root/web/` con sudo | Bug de HOME en versiones anteriores | Actualizar WSLaragon: `pip install -e .` |

---

## Recuperar bases cuando existen `mysql8` y `mariadb11`

En Omarchy pueden quedar instalados los contenedores `mysql8` y `mariadb11`.
Cada uno puede estar conectado a un volumen Docker diferente, por lo que iniciar
el contenedor equivocado hace que phpMyAdmin muestre una instancia vacía. Los
datos normalmente siguen en el volumen original: cambiar de motor **no migra ni
elimina** bases de datos.

### 1. No eliminar ni recrear nada

No ejecutes `docker rm`, `docker volume rm`, el script de instalación ni crees
otra base con el mismo nombre mientras se investiga. Primero lista los
contenedores y volúmenes:

```bash
sudo docker ps -a --no-trunc \
  --format 'table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
sudo docker volume ls
```

### 2. Identificar qué volumen usa cada motor

```bash
sudo docker inspect mysql8 --format \
  'image={{.Config.Image}} mounts={{range .Mounts}}{{.Name}} -> {{.Destination}} {{end}}'
sudo docker inspect mariadb11 --format \
  'image={{.Config.Image}} mounts={{range .Mounts}}{{.Name}} -> {{.Destination}} {{end}}'
```

Si conoces nombres de bases anteriores, puedes localizar sus directorios sin
modificarlos. Sustituye los nombres del ejemplo por los tuyos:

```bash
sudo find /var/lib/docker/volumes -maxdepth 4 -type d -print | \
  grep -E '/(prueba_db|blog_db|laravel_demo_db|readernews_db)$'
```

El volumen que contiene esos directorios es el runtime que se debe conservar.

### 3. Detener ambos motores y seleccionar el correcto

Detener un contenedor es seguro para sus datos y evita que ambos compitan por
`127.0.0.1:3306`:

```bash
sudo docker stop mysql8 mariadb11
wslaragon mysql use mysql8
wslaragon on
```

Usa `mariadb11` en el comando `mysql use` si ese fue el contenedor cuyo volumen
contenía las bases. La selección queda guardada y será respetada por
`wslaragon on`, `wslaragon off` y `wslaragon service start|stop|restart mysql`.

Importante: si ejecutas `wslaragon on` antes de `wslaragon mysql use`, primero
detén el motor que ocupó el puerto y vuelve a iniciar el entorno después de
guardar la selección.

### 4. Validar los datos y el ciclo de encendido

```bash
wslaragon mysql status
wslaragon mysql databases
```

Comprueba también `https://pma.test` y un proyecto que use base de datos. Cuando
las bases esperadas aparezcan, valida que la selección persiste:

```bash
wslaragon off
wslaragon on
wslaragon mysql status
wslaragon mysql databases
```

No elimines el segundo contenedor o su volumen hasta tener una copia de
seguridad y confirmar qué información contiene.

### El contenedor está activo pero no publica el puerto 3306

Si `docker ps` muestra el contenedor como `Up`, pero `docker port` no devuelve
nada y `NetworkSettings.Networks` está vacío, recupera su conexión a la red
Docker. Sustituye `mysql8` por el runtime seleccionado si corresponde:

```bash
sudo docker network connect bridge mysql8
sudo docker restart mysql8
sudo docker port mysql8
```

Después confirma la conexión real con `wslaragon mysql status`. Que Docker
muestre un contenedor como `running` no garantiza por sí solo que MySQL acepte
conexiones en `127.0.0.1:3306`.

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
