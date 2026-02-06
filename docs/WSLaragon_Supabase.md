# WSLaragon + Supabase Integration Guide

## 🎉 Integración Completada

Has integrado exitosamente Supabase con WSLaragon en tu entorno WSL. Ahora puedes gestionar proyectos con bases de datos MariaDB (existentes) y Supabase PostgreSQL (nuevos).

## 📁 Estructura de Archivos

```
~/
├── supabase-docker/          # Stack completo de Supabase Docker
│   ├── docker-compose.yml    # Configuración de containers
│   └── .env                  # Variables de entorno de Supabase
├── supabase-data/            # Datos persistentes de Supabase
└── .wslaragon/               # Configuración extendida de WSLaragon
    ├── config.yaml           # Configuración principal actualizada
    ├── supabase.py          # Gestor de Supabase
    ├── create_project_simple.py  # Creador de proyectos con Supabase
    └── templates/           # Templates para proyectos con Supabase
        ├── laravel-supabase.env
        ├── node-supabase.env
        └── python-supabase.env
```

## 🚀 Comandos Principales

### Gestión de Supabase
```bash
# Iniciar Supabase
python3 ~/.wslaragon/supabase.py start

# Detener Supabase
python3 ~/.wslaragon/supabase.py stop

# Verificar estado
python3 ~/.wil/.wslaragon/supabase.py status

# Obtener información de conexión
python3 ~/.wslaragon/supabase.py info
```

### Creación de Proyectos
```bash
# Proyecto Laravel CON Supabase
python3 ~/.wslaragon/create_project_simple.py miapp laravel --supabase

# Proyecto Node CON Supabase
python3 ~/.wslaragon/create_project_simple.py miapp node --supabase

# Proyecto Python CON Supabase
python3 ~/.wslaragon/create_project_simple.py miapp python --supabase

# Proyecto SIN Supabase (MariaDB tradicional)
python3 ~/.wslaragon/create_project_simple.py miapp laravel
```

## 🔗 Puertos de Servicios

| Servicio | Puerto | URL |
|----------|--------|-----|
| Supabase Studio | 8080 | http://localhost:8080 |
| Supabase API Gateway | 8081 | http://localhost:8081 |
| Supabase API SSL | 8082 | https://localhost:8082 |
| Analytics | 8083 | http://localhost:8083 |
| PostgreSQL Direct | 5433 | localhost:5433 |

## 💾 Configuración de Base de Datos

### Supabase PostgreSQL
- **Host**: localhost
- **Puerto**: 5433
- **Usuario**: postgres
- **Password**: WSL_Supabase_2026_Secure_Passw0rd!
- **Base de datos**: supabase

### MariaDB (existente)
- **Host**: localhost
- **Puerto**: 3306
- **Usuario**: root
- **Password**: ncdsDln68*/

## 🔥 Uso en Proyectos

### Laravel con Supabase
El .env generado incluye:
```env
DB_CONNECTION=pgsql
DB_HOST=localhost
DB_PORT=5433
DB_DATABASE=miapp_db
DB_USERNAME=postgres
DB_PASSWORD=ncdsDln68*/

SUPABASE_URL=http://localhost:8081
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
```

### Node.js con Supabase
```env
DATABASE_URL=postgresql://postgres:password@localhost:5433/miapp_db
SUPABASE_URL=http://localhost:8081
SUPABASE_ANON_KEY=...
```

### Python con Supabase
```env
DATABASE_URL=postgresql://postgres:password@localhost:5433/miapp_db
SUPABASE_URL=http://localhost:8081
SUPABASE_KEY=...
```

## 🛠️ Configuración Manual de Nginx

Para proyectos creados con el script simple:

```bash
# Copiar configuración
sudo cp /home/wil/temp_configs/miapp.conf /etc/nginx/sites-available/

# Activar sitio
sudo ln -s /etc/nginx/sites-available/miapp.conf /etc/nginx/sites-enabled/

# Probar y recargar
sudo nginx -t && sudo systemctl reload nginx
```

## 🌐 Acceso a Dominios

Agrega al archivo hosts de Windows:
```
127.0.0.1 miapp.test
```

Luego accede a: https://miapp.test

## 🔄 Workflow de Desarrollo

1. **Iniciar Supabase**: `python3 ~/.wslaragon/supabase.py start`
2. **Crear proyecto**: `python3 ~/.wslaragon/create_project_simple.py miapp laravel --supabase`
3. **Configurar Nginx**: Manualmente como se muestra arriba
4. **Desarrollar**: Usa las variables de entorno del .env generado
5. **Acceder**: https://miapp.test para web, http://localhost:8080 para Supabase Studio

## 📊 Monitoreo

- **Supabase Studio**: Panel de administración visual
- **API Health Check**: `curl http://localhost:8081/rest/v1/`
- **Containers**: `cd ~/supabase-docker && docker compose ps`

## 🔧 Troubleshooting

### Si Supabase no inicia:
```bash
cd ~/supabase-docker
docker compose down
docker compose up -d
```

### Si un proyecto no se conecta a Supabase:
1. Verifica que Supabase esté corriendo
2. Revisa las credenciales en el .env
3. Confirma el puerto (5433 para PostgreSQL)

### Para reiniciar todo:
```bash
# Detener Supabase
python3 ~/.wslaragon/supabase.py stop

# Reiniciar
python3 ~/.wslaragon/supabase.py start
```

¡Listo! Ahora tienes WSLaragon con Supabase completamente integrado.