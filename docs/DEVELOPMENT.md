# Developer Documentation

This document contains internal development notes for WSLaragon.

## Architecture Overview

### Core Components

```
wslaragon/
├── src/wslaragon/
│   ├── cli/              # Click-based CLI interface
│   │   ├── main.py       # Main CLI entry point
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
│       ├── mysql.py     # MySQL database management
│       ├── ssl.py        # SSL certificate management (mkcert)
│       ├── sites.py      # Site lifecycle management
│       ├── backup.py     # Site backup/restore
│       └── node/
│           └── pm2.py    # Node.js process management
```

### Configuration Flow

1. `Config` class loads from `~/.wslaragon/config.yaml`
2. Environment variables (`.env`) override config values
3. All managers receive config instance on initialization

### Site Creation Flow

```
wslaragon site create <name>
  ├── Validate name (alphanumeric + hyphens/underscores)
  ├── Create directory structure
  ├── Generate index file (PHP/HTML/Node/Python)
  ├── Setup database (if requested)
  ├── Generate SSL certificates (mkcert)
  ├── Create Nginx config
  ├── Update Windows hosts file
  └── Save to sites.json
```

## Testing Strategy

### Unit Tests

Mock all external dependencies:
- `subprocess.run` - System commands
- `systemctl` - Service management
- File system operations
- Network operations

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

# Specific module
pytest tests/unit/test_config.py

# With verbose output
pytest -v

# With coverage
pytest --cov=src --cov-report=term
```

## Common Development Tasks

### Adding a New CLI Command

1. Add command to appropriate group in `main.py`
2. Create manager method if needed
3. Add tests in `tests/unit/test_cli.py`

### Adding a New Service Manager

1. Create class in `src/wslaragon/services/`
2. Import in `main.py`
3. Add CLI commands
4. Add unit tests

### Modifying Configuration

1. Update `Config` class in `core/config.py`
2. Update default config in `_load_config()`
3. Document in `docs/`

## Performance Considerations

- Lazy load managers (only instantiate when needed)
- Cache site list in memory
- Use subprocess efficiently (combine commands where possible)

## Security Notes

- Never log passwords or secrets
- Validate all user inputs
- Use parameterized commands (avoid shell injection)
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

*Last updated: 2024*