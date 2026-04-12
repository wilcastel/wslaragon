# Developer Documentation

This document contains internal development notes for WSLaragon.

## Architecture Overview

### Core Components

```
wslaragon/
├── src/wslaragon/
│   ├── cli/              # Click-based CLI interface
│   │   ├── main.py       # Main CLI entry point
│   │   ├── site_commands.py   # Site management commands
│   │   ├── service_commands.py  # Service management commands
│   │   ├── php_commands.py   # PHP commands
│   │   ├── mysql_commands.py # MySQL commands
│   │   ├── ssl_commands.py   # SSL commands
│   │   ├── node_commands.py  # Node.js/PM2 commands
│   │   ├── nginx_commands.py  # Nginx config commands
│   │   ├── doctor.py     # Diagnostic commands
│   │   └── agent.py      # AI agent integration
│   │
│   ├── core/             # Core functionality
│   │   ├── config.py     # Configuration management (YAML + .env)
│   │   └── services.py   # Systemd service management
│   │
│   └── services/         # Service managers
│       ├── php.py        # PHP version/extension management
│       ├── nginx.py      # Nginx site configuration
│       ├── mysql.py      # MySQL database management
│       ├── sites.py      # Site lifecycle management (delegates to creators)
│       ├── site_creators.py  # Strategy pattern: PHP/Node/Python/WordPress creators
│       ├── ssl.py        # SSL certificate management (mkcert)
│       ├── backup.py     # Site backup/restore
│       └── node/
│           └── pm2.py    # Node.js process management
```

### Configuration Flow

1. `Config` class loads from `~/.wslaragon/config.yaml`
2. Environment variables (`.env`) override config values
3. All managers receive config instance on initialization

### Site Creation Flow (Strategy Pattern)

```
wslaragon site create <name>
  ├── Validate name (alphanumeric + hyphens/underscores)
  ├── Select appropriate SiteCreator:
  │   ├── PHPCreator (PHP/Laravel sites)
  │   ├── NodeCreator (Node.js apps)
  │   ├── PythonCreator (FastAPI/Django)
  │   ├── WordPressCreator (auto-install WP)
  │   └── StaticCreator (plain HTML)
  ├── Creator.execute():
  │   ├── Create directory structure
  │   ├── Generate index file (PHP/HTML/Node/Python)
  │   ├── Setup database (if requested)
  │   ├── Generate SSL certificates (mkcert)
  │   ├── Create Nginx config
  │   └── Update Windows hosts file
  └── Save to sites.json
```

## Testing Strategy

### Test Stats
- **Total tests**: 1,114+ (1,083 unit + 31 integration)
- **Coverage**: 99.85%
- **Threshold**: 90% minimum to pass CI

### Unit Tests

Mock all external dependencies:
- `subprocess.run` - System commands
- `systemctl` - Service management
- File system operations
- Network operations

### Integration Tests

Run with `--run-slow` marker:
```bash
pytest tests/integration/ --run-slow
```

### Fixtures (conftest.py)

- `mock_config` - Config object with test values
- `mock_nginx_manager` - Mock Nginx operations
- `mock_mysql_manager` - Mock MySQL operations
- `temp_dir` - Temporary directory for tests
- `mock_site_data` - Sample site data

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests (requires --run-slow)
pytest tests/integration/ --run-slow

# With coverage (enforces 90% threshold)
pytest --cov=src --cov-fail-under=90

# Makefile targets
make test-unit        # Unit tests only
make test-integration # Integration tests
make test-cov         # With coverage (90% threshold)
make test             # All tests
```

## Common Development Tasks

### Adding a New CLI Command

1. Add command to appropriate module in `cli/` (not main.py directly)
   - Site commands → `site_commands.py`
   - Service commands → `service_commands.py`
   - PHP commands → `php_commands.py`
   - MySQL commands → `mysql_commands.py`
   - SSL commands → `ssl_commands.py`
   - Node commands → `node_commands.py`
   - Nginx commands → `nginx_commands.py`
2. Create manager method if needed in corresponding `services/` module
3. Add tests in `tests/unit/test_<module>_commands.py`

### Adding a New Service Manager

1. Create class in `src/wslaragon/services/`
2. Import in the corresponding CLI module
3. Add CLI commands to appropriate `*_commands.py`
4. Add unit tests in `tests/unit/`

### Modifying Configuration

1. Update `Config` class in `core/config.py`
2. Update default config in `_load_config()`
3. Document in `docs/`

## Performance Considerations

- Lazy load managers (only instantiate when needed)
- Cache site list in memory
- Use subprocess efficiently (combine commands where possible)

## Security Notes

- **No shell=True**: All subprocess calls use argument lists to prevent shell injection
- **No SQL injection**: MySQL module uses parameterized queries
- **Path traversal protection**: Backup module validates and sanitizes paths
- Never log passwords or secrets
- Validate all user inputs
- Store sensitive data in `.env`, not in config files

## Troubleshooting Tests

### Import Errors

```bash
# Ensure src is in PYTHONPATH
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"
```

### Mock Issues

Check that all external dependencies are mocked in tests. Common issues:
- `subprocess.run` not mocked
- `systemctl` commands not mocked
- File operations not mocked

---

*Last updated: 2026*