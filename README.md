# WSLaragon

🚀 **Laragon-style development environment manager for WSL2**

WSLaragon es una herramienta de gestión de entorno de desarrollo estilo Laragon diseñada específicamente para WSL2. Permite gestionar fácilmente servicios web como PHP, Nginx y MySQL, con soporte para múltiples sitios (WordPress, Laravel, Vite, Astro, SvelteKit, sitios headless pareados, Node.js/Python), SSL con mkcert y configuración automática del archivo hosts de Windows.

## ✨ Características

### 🐘 Gestión de PHP
- **Múltiples versiones**: Soporta cambio entre diferentes versiones de PHP
- **Configuración INI**: Modificación directa de php.ini (`php config`)
- **Límite de subida global**: `php upload-limit` ajusta `upload_max_filesize`, `post_max_size`, `memory_limit` y tiempos de ejecución en TODAS las versiones de PHP instaladas y en Nginx, en un solo comando
- **Extensiones**: Activar/desactivar extensiones PHP fácilmente
- **PHP-FPM**: Gestión del servicio PHP-FPM

### 🌐 Gestión de Nginx
- **Virtual Hosts**: Creación y gestión automática de sitios
- **Configuración SSL**: Soporte HTTPS con certificados válidos
- **Recarga automática**: Aplicación de configuraciones sin reiniciar
- **Configuración global**: `nginx config` para ajustar valores como `client_max_body_size`

### 🗄️ Gestión de MySQL
- **Base de datos**: Crear, eliminar y listar bases de datos (`mysql create-db`, `mysql drop-db`, `mysql databases`)

### 🌍 Gestión de Sitios
- **Dominios .test**: Configuración automática de dominios locales
- **Plantillas**: WordPress, Laravel, Vite, Astro (SSG o con islas API/headless), phpMyAdmin, HTML estático, Node.js, Python
- **Sitios headless pareados**: `--headless` crea un frontend y un backend/API vinculados (ej. SvelteKit + WordPress) compartiendo una raíz de proyecto
- **API Proxies**: `site api` gestiona proxies reversos por sitio
- **SSL/TLS**: Certificados válidos con mkcert
- **Windows Hosts**: Integración con el archivo hosts de Windows
- **Backup/Restore**: Exportar e importar sitios completos (`site export` / `site import`)

### 🔐 SSL con mkcert
- **Certificados locales**: Certificados SSL válidos para desarrollo
- **CA local**: Autoridad certificadora local automática (`ssl setup`)
- **Múltiples dominios**: Soporte para certificados SAN
- **Windows Integration**: Instalación automática en Windows

### 🩺 Diagnóstico
- **`doctor`**: Chequeo de servicios, puertos, certificados SSL y configuraciones críticas

### 🤖 Agentes de IA
- **Estructura estandarizada**: `.agent/` con skills, memoria y especificaciones (`agent init`)
- **Integración**: Comandos para inicializar e importar habilidades (`agent import`)
- **Productividad**: Skills listos para usar (UI Designer, Librarian)
- **Servidor MCP**: Usá WSLaragon desde Claude en lenguaje humano — ver [docs/MCP.md](docs/MCP.md)

### 🚀 Ecosistema Node.js
- **Gestión de Procesos**: Integración nativa con PM2 (`node start`, `node stop`, `node restart`, `node list`)
- **Scaffolding**: Configuración automática de Proxy y puertos
- **Soporte Fullstack**: Listo para Next.js, Nuxt, Python, etc.

## 📋 Requisitos

### Sistema
- **WSL2** con Ubuntu 20.04+ o Debian 10+
- **Windows 10/11** para integración con hosts
- **Python 3.9+** instalado
- **Permisos sudo** para configuración de servicios

### Software
- PHP (FPM + CLI)
- MariaDB/MySQL
- Nginx
- mkcert (para SSL local)

Si te falta alguna dependencia:
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx mariadb-server php8.3 php8.3-fpm

# mkcert para SSL
curl -L https://dl.filippo.io/mkcert/latest?for=linux/amd64 -o mkcert
chmod +x mkcert && sudo mv mkcert /usr/local/bin/
```

## 🚀 Instalación

Ver **[docs/INSTALL.md](docs/INSTALL.md)** para la guía completa (setup automático con `scripts/setup-env.sh`, instalación manual con `pip install -e .`, y verificación con `scripts/test-setup.sh`).

Resumen rápido:
```bash
git clone <url-del-repo>
cd wslaragon

python3 -m venv venv
source venv/bin/activate
pip install -e .

./scripts/setup-env.sh
```

## 🎖️ Uso Rápido

```bash
# Verificar instalación
wslaragon --version

# Crear un sitio PHP + MySQL + SSL
wslaragon site create myproject --php --mysql --ssl

# Crear un sitio WordPress (la base de datos se crea automáticamente)
wslaragon site create mi-blog --wordpress

# Crear un sitio headless pareado: frontend SvelteKit + backend WordPress
# Genera misitio.test (frontend) y api.misitio.test (backend), raíz compartida
wslaragon site create --headless --backend=wordpress --frontend=sveltekit --url=misitio

# Listar sitios
wslaragon site list

# Gestionar servicios
wslaragon service status
wslaragon service start nginx
wslaragon service restart mysql

# Gestionar PHP
wslaragon php versions
wslaragon php switch 8.2
wslaragon php extensions

# Subir el límite de tamaño de archivos en TODAS las versiones de PHP + Nginx de una vez
wslaragon php upload-limit 1G

# Gestionar MySQL
wslaragon mysql databases
wslaragon mysql create-db myapp_db

# Gestionar SSL
wslaragon ssl setup
wslaragon ssl generate myproject.test

# Diagnóstico
wslaragon doctor

# Gestionar Agentes
wslaragon agent init
wslaragon agent import https://url-to-skill.md

# Gestionar Node (PM2)
wslaragon node start my-app
wslaragon node list
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
  client_max_body_size: "512M"

mysql:
  data_dir: "/var/lib/mysql"
  config_file: "/etc/mysql/mariadb.conf.d/50-server.cnf"

ssl:
  ca_file: "~/.wslaragon/ssl/rootCA.pem"
  ca_key: "~/.wslaragon/ssl/rootCA-key.pem"

sites:
  tld: ".test"
  document_root: "~/web"

windows:
  hosts_file: "/mnt/c/Windows/System32/drivers/etc/hosts"
```

> Bajo `sudo`, WSLaragon resuelve automáticamente el `document_root` al home del usuario real (`$SUDO_USER`), no al de `root`.

## 📂 Estructura de Directorios

```
~/.wslaragon/
├── config.yaml          # Configuración principal
├── sites/                # Configuraciones de sitios
│   └── sites.json        # Base de datos de sitios
├── ssl/                   # Certificados SSL
│   ├── rootCA.pem         # Certificado CA
│   └── rootCA-key.pem     # Clave CA
└── logs/                  # Logs de WSLaragon

~/web/
├── myproject/             # Raíz del sitio (dominio: myproject.test)
│   └── index.php
├── mi-blog/
└── misitio/               # Raíz compartida de un sitio headless
    ├── front/              # misitio.test
    └── back/               # api.misitio.test
```

## 🧪 Tests

**1,259 tests** (1,226 unitarios en 25 archivos + 33 de integración) | 100% de cobertura | 90% mínimo requerido

```bash
make test              # Todos los tests
make test-unit         # Solo unitarios
make test-integration  # Solo integración (usa --run-slow)
make test-cov          # Con cobertura (falla si < 90%)
```

Ver **[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)** para más detalles del flujo de desarrollo.

## 📚 Documentación

Este README es solo la puerta de entrada. La referencia completa vive en `docs/`:

- **[docs/README.md](docs/README.md)** — índice general de la documentación
- **[docs/CLI.md](docs/CLI.md)** — manual completo de todos los comandos del CLI, con ejemplos
- **[docs/INSTALL.md](docs/INSTALL.md)** — guía de instalación paso a paso
- **[docs/STRUCTURE.md](docs/STRUCTURE.md)** — estructura del código y arquitectura
- **[docs/MCP.md](docs/MCP.md)** — servidor MCP: usá WSLaragon desde Claude en lenguaje humano
- **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** — solución de problemas comunes
- **[docs/SSL-DB.md](docs/SSL-DB.md)** — detalles de SSL y bases de datos
- **[docs/ROADMAP.md](docs/ROADMAP.md)** — funciones implementadas y planificadas
- **[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)** — cómo contribuir al proyecto
- **[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)** — flujo de desarrollo, tests, linters
- **[docs/glosario.md](docs/glosario.md)** — glosario de comandos (también disponible en vivo vía `wslaragon --glossary`)

También podés consultar la ayuda interactiva en cualquier momento:
```bash
wslaragon --help
wslaragon --glossary       # o wslaragon -g
wslaragon glossary php     # filtrar por término
```

## 🤝 Contribuir

1. Fork del proyecto
2. Crear feature branch (`git checkout -b feature/amazing-feature`)
3. Commit cambios (`git commit -m 'feat: add amazing feature'`)
4. Push al branch (`git push origin feature/amazing-feature`)
5. Abrir Pull Request

Ver **[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)** para más detalles.

## 📄 Licencia

Este proyecto está licenciado bajo la MIT License - ver el archivo [LICENSE](LICENSE) para detalles.

## 🙏 Agradecimientos

- **Laragon** - Inspiración inicial y concepto
- **mkcert** - Certificados SSL locales válidos
- **Click** - Framework CLI para Python
- **Rich** - CLI hermosa y moderna

## 📞 Soporte

- **Issues**: [GitHub Issues](https://github.com/your-username/wslaragon/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/wslaragon/discussions)

---

**WSLaragon** - Tu entorno de desarrollo WSL2, simplificado. 🚀
