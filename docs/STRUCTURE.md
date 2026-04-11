# 🏗️ Arquitectura y Estructura

Entender cómo se organiza WSLaragon te ayudará a personalizarlo y solucionar problemas.

## 📁 Directorios del Proyecto

```text
/home/wil/baselog/wslaragon/
├── src/wslaragon/       # Código fuente principal (Python)
│   ├── cli/             # Comandos de la terminal (Click)
│   │   ├── main.py      # Entry point + comandos globales (completion, glossary)
│   │   ├── site_commands.py     # Gestión de sitios (create, list, delete, etc.)
│   │   ├── service_commands.py  # Gestión de servicios (status, start, stop, restart)
│   │   ├── php_commands.py      # Gestión de PHP (versions, switch, extensions, config)
│   │   ├── mysql_commands.py    # Gestión de MySQL (databases, create-db, drop-db)
│   │   ├── ssl_commands.py      # Gestión de SSL (setup, generate, delete, list)
│   │   ├── node_commands.py     # Gestión de Node.js/PM2 (list, start, stop, delete, restart)
│   │   ├── nginx_commands.py    # Gestión de Nginx (config list, config set)
│   │   ├── doctor.py     # Diagnóstico del entorno
│   │   └── agent.py      # Comandos de agentes IA
│   ├── core/            # Configuración y lógica base
│   │   ├── config.py    # Gestión de configuración YAML
│   │   └── services.py  # Gestión de servicios systemd
│   ├── services/        # Gestión de servicios específicos
│   │   ├── php.py       # Gestión de PHP
│   │   ├── nginx.py     # Gestión de Nginx
│   │   ├── mysql.py     # Gestión de MySQL (validación SQL, consultas parametrizadas)
│   │   ├── sites.py     # Gestión de sitios (God Object - pendiente refactor)
│   │   ├── ssl.py       # Gestión de SSL/mkcert
│   │   ├── backup.py    # Backup/restore de sitios (protección contra path traversal)
│   │   ├── node/        # Gestión de Node.js
│   │   │   └── pm2.py   # Gestión de PM2
│   │   └── agent/       # Gestión de agentes IA
│   │       └── agent_manager.py
│   ├── mcp/             # Model Context Protocol server
│   │   └── server.py
│   └── __init__.py
├── tests/               # Test suite
│   ├── unit/            # Tests unitarios (56 tests)
│   └── integration/     # Tests de integración
├── scripts/             # Scripts de instalación y setup
│   └── vars.sh          # Variables compartidas entre scripts
├── docs/                # Documentación oficial
├── venv/                # Entorno virtual de Python
├── .env                 # Configuración local (No subir a Git)
└── .env.example         # Plantilla para el .env
```

## 📁 Datos del Usuario

WSLaragon guarda la persistencia y configuraciones específicas del usuario en:

```text
~/.wslaragon/            # (en tu carpeta home)
├── config.yaml          # Configuración generada automáticamente
├── logs/                # Historial de acciones y errores
├── sites/               # Registro de sitios creados (sites.json)
└── ssl/                 # Certificados .pem generados para tus webs
```

## 🌐 Servicios e IPs

- **Nginx**: Escucha en el puerto 80 (HTTP) y 443 (HTTPS) de WSL.
- **MariaDB**: Escucha en `localhost:3306`.
- **IPs**: WSLaragon configura los hosts para responder tanto en `127.0.0.1` como en `::1`.

---

> [!NOTE]
> Tus webs se crean por defecto en `~/web/` para facilitar el acceso desde Windows mediante la ruta de red `\\wsl.localhost\Ubuntu\home\wil\web`.
