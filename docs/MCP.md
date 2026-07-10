# 🤖 Servidor MCP

WSLaragon incluye un servidor **MCP** (Model Context Protocol) que expone casi todo el CLI como herramientas que un asistente de IA (Claude Desktop, Claude Code, o cualquier cliente MCP) puede invocar en lenguaje humano — sin que vos tengas que escribir el comando exacto.

> Ejemplo: en vez de acordarte de `wslaragon site create --headless --backend=wordpress --frontend=sveltekit --url=misitio --no-ssl`, le decís a la IA "creame un sitio headless con backend WordPress y frontend SvelteKit llamado misitio, sin SSL" y listo.

## Instalación

El servidor se instala junto con el paquete (`pip install -e .` desde la raíz del repo, ver [docs/INSTALL.md](INSTALL.md)). Esto registra el comando `wslaragon-mcp` en tu entorno virtual.

Verificá que está disponible:
```bash
which wslaragon-mcp
# o
python -m wslaragon.mcp.server
```

## Registrarlo en Claude Code

```bash
claude mcp add wslaragon-mcp -- /ruta/a/tu/venv/bin/wslaragon-mcp
```

Reemplazá la ruta por la de tu entorno virtual (por ejemplo `~/wslaragon/venv/bin/wslaragon-mcp`).

## Registrarlo en Claude Desktop

Agregá esto a tu `claude_desktop_config.json` (Windows: `%APPDATA%\Claude\claude_desktop_config.json`; dentro de WSL si corrés Claude Desktop en Windows necesitás apuntar al binario accesible desde ahí, o usar `wsl.exe` como wrapper):

```json
{
  "mcpServers": {
    "wslaragon": {
      "command": "/ruta/a/tu/venv/bin/wslaragon-mcp"
    }
  }
}
```

Reiniciá Claude Desktop después de guardar el archivo.

## Qué expone

### Resources (contexto de solo lectura)

| Resource | Contenido |
|---|---|
| `wslaragon://sites` | Todos los sitios registrados (dominio, PHP, MySQL, SSL, puerto de proxy) |
| `wslaragon://services` | Estado actual de nginx, PHP-FPM, MariaDB y Redis |
| `wslaragon://config` | Contenido de `~/.wslaragon/config.yaml` |

### Prompts (flujos guiados)

| Prompt | Qué hace |
|---|---|
| `new_project` | Guía paso a paso para levantar un proyecto nuevo (chequea servicios, crea el sitio, sugiere próximos comandos) |

### Tools (acciones)

Cada tool ejecuta el comando `wslaragon` real correspondiente. Los nombres entre paréntesis son el comando CLI que envuelven.

**Sitios**
- `list_sites` (`site list`)
- `create_site` — sitio individual: PHP, WordPress, Laravel, Node, Python, Vite, Astro (SSG), phpMyAdmin, HTML (`site create`)
- `create_headless_site` — par frontend+backend vinculado, ej. SvelteKit + WordPress (`site create --headless`)
- `delete_site` — borra un sitio (o ambas mitades si es un par headless) (`site delete`)
- `enable_site` / `disable_site` (`site enable` / `site disable`)
- `set_site_public` — apunta la raíz web a `public/` (Laravel/Symfony) (`site public`)
- `fix_site_permissions` (`site fix-permissions`)
- `export_site` / `import_site` — backup/restore completo de un sitio (`site export` / `site import`)
- `enable_site_ssl` — activa SSL en un sitio ya creado (`site ssl`)
- `add_api_proxy` / `remove_api_proxy` / `list_api_proxies` (`site api add/remove/list`)

**PHP**
- `list_php_versions` (`php versions`)
- `switch_php_version` (`php switch`)
- `list_php_extensions` / `enable_php_extension` / `disable_php_extension` (`php extensions` / `php enable-ext` / `php disable-ext`)
- `list_php_config` / `get_php_config` / `set_php_config` (`php config list/get/set`)
- `set_php_upload_limit` — sube `upload_max_filesize`/`post_max_size`/`memory_limit` en todas las versiones de PHP instaladas + `client_max_body_size` de nginx, en un solo llamado (`php upload-limit`)

**MySQL**
- `list_mysql_databases` / `create_mysql_database` / `drop_mysql_database` (`mysql databases/create-db/drop-db`)

**Nginx**
- `list_nginx_config` / `set_nginx_config` (`nginx config list/set`)

**SSL**
- `setup_ssl` — genera la CA root local (primera vez) (`ssl setup`)
- `generate_ssl` — certificado para un dominio puntual (`ssl generate`)
- `delete_ssl_cert` / `list_ssl_certs` (`ssl delete` / `ssl list`)

**Servicios**
- `get_services_status` (`service status`)
- `start_service` / `stop_service` / `restart_service` — acepta `nginx`, `php`, `mysql`, `redis` o `all` (`service start/stop/restart`)

**Node (PM2)**
- `list_node_processes` (`node list`)
- `start_node_process` / `stop_node_process` / `restart_node_process` / `delete_node_process` (`node start/stop/restart/delete`)

**Diagnóstico**
- `run_doctor` (`doctor`)

**Agentes de IA**
- `agent_init` — inicializa `.agent/` con un preset de skills (`agent init --preset --path`)
- `import_skill` (`agent import`)

## Comandos que confirman por consola

`site delete`, `mysql drop-db` y `ssl delete` piden confirmación interactiva en el CLI normal. Las tools correspondientes (`delete_site`, `drop_mysql_database`, `delete_ssl_cert`) responden esas confirmaciones automáticamente por vos — no hace falta que la IA simule un `y` en la conversación, el propio tool ya lo maneja.

## Extender el servidor

El código vive en `src/wslaragon/mcp/server.py`, cubierto al 100% por tests en `tests/unit/test_mcp_server.py`. Cada tool nueva es un wrapper delgado sobre `_run(cmd)` (o `_run_interactive(cmd, input_text)` si el comando real pide confirmación) que arma la lista de argumentos del CLI real y devuelve un string legible. Si agregás un comando nuevo al CLI, agregá su tool acá siguiendo el mismo patrón, y su test correspondiente.
