# 🏗️ Arquitectura y Estructura

Entender cómo se organiza WSLaragon te ayudará a personalizarlo y solucionar problemas.

## 📁 Directorios del Proyecto

```text
/home/wil/baselog/wslaragon/
├── src/wslaragon/       # Código fuente principal (Python)
│   ├── cli/             # Comandos de la terminal
│   ├── core/            # Configuración y lógica base
│   └── services/        # Gestión de Nginx, MySQL, SSL y Sitios
├── venv/                # Entorno virtual de Python
├── docs/                # Documentación oficial
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
