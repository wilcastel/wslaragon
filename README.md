# WSLaragon

🚀 **Laragon-style development environment manager for WSL2**

WSLaragon es una herramienta de gestión de entorno de desarrollo estilo Laragon diseñada específicamente para WSL2. Permite gestionar fácilmente servicios web como PHP, Nginx y MySQL, con soporte para múltiples sitios, SSL con mkcert y configuración automática del archivo hosts de Windows.

## ✨ Características

### 🐘 Gestión de PHP
- **Múltiples versiones**: Soporta cambio entre diferentes versiones de PHP
- **Configuración INI**: Modificación directa de php.ini
- **Extensiones**: Activar/desactivar extensiones PHP fácilmente
- **PHP-FPM**: Gestión del servicio PHP-FPM

### 🌐 Gestión de Nginx
- **Virtual Hosts**: Creación y gestión automática de sitios
- **Configuración SSL**: Soporte HTTPS con certificados válidos
- **Recarga automática**: Aplicación de configuraciones sin reiniciar
- **Optimización**: Configuraciones optimizadas para desarrollo

### 🗄️ Gestión de MySQL
- **Base de datos**: Crear, eliminar y listar bases de datos
- **Usuarios**: Gestión de usuarios y permisos
- **Backup/Restore**: Copias de seguridad automáticas
- **Optimización**: Configuraciones para desarrollo

### 🌍 Gestión de Sitios
- **Dominios .test**: Configuración automática de dominios locales
- **Plantillas**: Soporte para diferentes tipos de proyectos
- **SSL/TLS**: Certificados válidos con mkcert
- **Windows Hosts**: Integración con el archivo hosts de Windows

### 🔐 SSL con mkcert
- **Certificados locales**: Certificados SSL válidos para desarrollo
- **CA local**: Autoridad certificadora local automática
- **Múltiples dominios**: Soporte para certificados SAN
- **Windows Integration**: Instalación automática en Windows

### 🖥️ Interfaces
- **CLI completa**: Interfaz de línea de comandos potente
- **Web UI**: Panel de control web opcional
- **API REST**: API para integración con otras herramientas
- **Autocompletado**: Soporte para bash/zsh

### 🤖 Agentes de IA
- **Estructura estandarizada**: `.agent/` con skills, memoria y especificaciones
- **Integración**: Comandos para inicializar e importar habilidades
- **Productividad**: Skills listos para usar (UI Designer, Librarian)

### 🚀 Ecosistema Node.js
- **Gestión de Procesos**: Integración nativa con PM2
- **Scaffolding**: Configuración automática de Proxy y puertos
- **Soporte Fullstack**: Listo para Next.js, Nuxt, Python, etc.

## 📋 Requisitos

### Sistema
- **WSL2** con Ubuntu 20.04+ o Debian 10+
- **Windows 10/11** para integración con hosts
- **Python 3.8+** instalado
- **Permisos sudo** para configuración de servicios

### Software (Configurado para tu entorno)
```bash
# Tu entorno actual:
- PHP 8.3 ✅
- MariaDB ✅  
- Nginx ✅
- mkcert ✅
- Proyectos en: /home/wil/web ✅

# Si faltara alguna dependencia:
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx mariadb-server php8.3 php8.3-fpm

# mkcert para SSL
curl -L https://dl.filippo.io/mkcert/latest?for=linux/amd64 -o mkcert
chmod +x mkcert && sudo mv mkcert /usr/local/bin/
```

## 🚀 Instalación para tu Entorno

### Método 1: Script para tu Setup Específico

```bash
# En tu directorio wslaragon:
cd /home/wil/baselog/wslaragon
chmod +x scripts/setup-env.sh
./scripts/setup-env.sh
```

### Método 2: Instalación Paso a Paso

```bash
# 1. Ir al directorio del proyecto
cd /home/wil/baselog/wslaragon

# 2. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar WSLaragon
pip install -e .

# 4. Crear configuración personalizada
./scripts/setup-env.sh

# 5. Iniciar interfaz web
sudo systemctl start wslaragon-web
```

### Método 3: Verificar Instalación

```bash
# Ejecutar test completo
./scripts/test-setup.sh
```

## 🎖️ Uso Rápido

### CLI Commands

```bash
# Verificar instalación
wslaragon --version

# Crear un sitio
wslaragon site create myproject --php --mysql --ssl

# Listar sitios
wslaragon site list

# Gestionar servicios
wslaragon service status
wslaragon service start nginx
wslaragon service restart mysql

# Gestionar PHP
wslaragon php versions
wslaragon php switch 8.0
wslaragon php extensions

# Gestionar MySQL
wslaragon mysql databases
wslaragon mysql create-db myapp_db

# Gestionar SSL
wslaragon ssl setup
wslaragon ssl generate myproject.test

# Gestionar Agentes
wslaragon agent init
wslaragon agent import https://url-to-skill.md

# Gestionar Node (PM2)
wslaragon node start my-app
wslaragon node list
```

### Web Interface

Accede al panel web en **http://localhost:8080**

- Dashboard con estado de servicios
- Gestión visual de sitios
- Configuración de PHP y MySQL
- Logs y monitoreo

## 📚 Ejemplos de Uso

### Crear Sitios con Diferentes Configuraciones

```bash
# Sitio PHP simple
wslaragon site create blog --php

# Sitio Laravel con MySQL y SSL
wslaragon site create laravel-app --php --mysql --ssl --database laravel_db

# Sitio estático
wslaragon site create portfolio --no-php --ssl

# Sitio Node.js (con PM2 y puerto automático)
wslaragon site create api-node --node

# Sitio Python (con PM2 y puerto automático)
wslaragon site create api-python --python
```

### Gestión de PHP

```bash
# Ver versiones instaladas
wslaragon php versions

# Cambiar versión
wslaragon php switch 8.2

# Configurar php.ini
wslaragon php config set memory_limit 512M
wslaragon php config set max_execution_time 300

# Gestionar extensiones
wslaragon php enable-ext redis
wslaragon php disable-ext xdebug
```

### Configuración SSL

```bash
# Setup inicial de SSL
wslaragon ssl setup

# Generar certificado
wslaragon ssl generate mysite.test

# Ver certificados
wslaragon ssl list
```

### MySQL Management

```bash
# Listar bases de datos
wslaragon mysql databases

# Crear base de datos
wslaragon mysql create-db myapp --user myuser --password mypass

# Backup
wslaragon mysql backup myapp --path /backups/

# Crear usuario
wslaragon mysql create-user myuser --password mypass --grant "ALL PRIVILEGES ON myapp.*"
```

## ⚙️ Configuración

La configuración principal se encuentra en `~/.wslaragon/config.yaml`:

```yaml
php:
  version: "8.3"
  ini_file: "/etc/php/8.3/fpm/php.ini"
  extensions_dir: "/usr/lib/php/20230831"

nginx:
  config_dir: "/etc/nginx"
  sites_available: "/etc/nginx/sites-available"
  sites_enabled: "/etc/nginx/sites-enabled"

mysql:
  data_dir: "/var/lib/mysql"
  config_file: "/etc/mysql/my.cnf"

ssl:
  ca_file: "~/.wslaragon/ssl/rootCA.pem"
  ca_key: "~/.wslaragon/ssl/rootCA-key.pem"

sites:
  tld: ".test"
  document_root: "/var/www"

windows:
  hosts_file: "/mnt/c/Windows/System32/drivers/etc/hosts"
```

## 📂 Estructura de Directorios

```
~/.wslaragon/
├── config.yaml          # Configuración principal
├── sites/               # Configuraciones de sitios
│   └── sites.json     # Base de datos de sitios
├── ssl/                 # Certificados SSL
│   ├── rootCA.pem     # Certificado CA
│   └── rootCA-key.pem # Clave CA
└── logs/               # Logs de WSLaragon

/var/www/
├── myproject.test/      # Raíz del sitio
│   └── index.php      # Archivo inicial
├── blog.test/
└── portfolio.test/
```

## 🐛 Troubleshooting

### Problemas Comunes

#### 1. Permisos de sudo
```bash
# Agregar usuario a sudoers sin contraseña
echo "$USER ALL=(ALL) NOPASSWD: /usr/sbin/nginx, /usr/sbin/service" | sudo tee /etc/sudoers.d/wslaragon
```

#### 2. Problemas con hosts de Windows
```bash
# Verificar si hosts es accesible
ls -la /mnt/c/Windows/System32/drivers/etc/hosts

# Si no funciona, editar manualmente en Windows
# Ejecutar como administrador y agregar:
# 127.0.0.1 myproject.test
```

#### 3. SSL no funciona
```bash
# Reinstalar CA
mkcert -uninstall
mkcert -install

# Verificar instalación
mkcert -CAROOT
```

#### 4. PHP-FPM no inicia
```bash
# Verificar configuración
sudo nginx -t

# Ver logs
sudo journalctl -u php8.3-fpm -f
```

### Logs Importantes

```bash
# Nginx
sudo tail -f /var/log/nginx/error.log

# PHP-FPM
sudo journalctl -u php8.3-fpm -f

# MySQL
sudo journalctl -u mysql -f

# WSLaragon
tail -f ~/.wslaragon/logs/wslaragon.log
```

## 🔧 Desarrollo

### Configurar para Desarrollo

```bash
# Clonar repositorio
git clone https://github.com/your-username/wslaragon.git
cd wslaragon

# Entorno de desarrollo
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# O usar Makefile para tareas comunes
make install-dev   # Instalar dependencias
make test          # Ejecutar tests
make lint          # Ejecutar linters
make format        # Formatear código
make check         # Verificar todo (lint + types + test)
```

### Pre-commit Hooks

```bash
# Instalar pre-commit para checks automáticos
pip install pre-commit
pre-commit install
```

### Tests

```bash
# Todos los tests
pytest

# Tests unitarios
make test-unit

# Tests con coverage
make test-cov
```

### Estructura del Código

```
src/wslaragon/
├── core/               # Módulos centrales
│   ├── config.py       # Gestión de configuración
│   └── services.py     # Gestión de servicios systemd
├── services/           # Gestión de servicios específicos
│   ├── php.py          # Gestión de PHP
│   ├── nginx.py        # Gestión de Nginx
│   ├── mysql.py        # Gestión de MySQL
│   ├── sites.py        # Gestión de sitios
│   ├── ssl.py          # Gestión de SSL
│   ├── backup.py       # Backup/restore de sitios
│   └── node/           # Gestión de Node.js/PM2
│       └── pm2.py
├── cli/                # Interfaz CLI (Click)
│   ├── main.py         # Entry point + comandos globales
│   ├── site_commands.py
│   ├── service_commands.py
│   ├── php_commands.py
│   ├── mysql_commands.py
│   ├── ssl_commands.py
│   ├── node_commands.py
│   ├── nginx_commands.py
│   ├── doctor.py
│   └── agent.py
└── __init__.py
```

## 🤝 Contribuir

1. Fork del proyecto
2. Crear feature branch (`git checkout -b feature/amazing-feature`)
3. Commit cambios (`git commit -m 'Add amazing feature'`)
4. Push al branch (`git push origin feature/amazing-feature`)
5. Abrir Pull Request

## 📄 Licencia

Este proyecto está licenciado bajo la MIT License - ver el archivo [LICENSE](LICENSE) para detalles.

## 🙏 Agradecimientos

- **Laragon** - Inspiración inicial y concepto
- **mkcert** - Certificados SSL locales válidos
- **Click** - Framework CLI para Python
- **Flask** - Framework web para el panel
- **Rich** - CLI hermosa y moderna

## 📞 Soporte

- **Issues**: [GitHub Issues](https://github.com/your-username/wslaragon/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/wslaragon/discussions)
- **Wiki**: [Documentación extendida](https://github.com/your-username/wslaragon/wiki)

---

**WSLaragon** - Tu entorno de desarrollo WSL2, simplificado. 🚀