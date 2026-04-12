# Contributing to WSLaragon

Thank you for your interest in contributing to WSLaragon!

## Development Setup

### Prerequisites

- Python 3.9+
- Git
- mkcert (for SSL)
- WSL2 (for full functionality)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/your-username/wslaragon.git
cd wslaragon

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linters
make lint
```

## Code Quality

We use several tools to maintain code quality:

| Tool | Purpose | Command |
|------|---------|---------|
| **ruff** | Linting, formatting & imports | `ruff check src/`, `ruff format src/` |
| **mypy** | Type checking | `mypy src/` |
| **pytest** | Testing (90% coverage threshold) | `pytest --cov-fail-under=90` |

### Pre-commit Hooks

Install pre-commit hooks for automatic code quality checks:

```bash
pip install pre-commit
pre-commit install
```

## Testing

### Test Statistics
- **1,114+ tests** total (1,083 unit + 31 integration)
- **99.85% coverage**
- **90% minimum** threshold to pass CI

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests (requires --run-slow marker)
pytest tests/integration/ --run-slow

# Makefile targets
make test             # All tests
make test-unit        # Unit tests only
make test-integration # Integration tests
make test-cov         # With coverage (90% threshold)
```

### Writing Tests

- Place tests in `tests/unit/` or `tests/integration/`
- Follow the naming convention: `test_*.py`
- Use pytest fixtures from `conftest.py`
- Mock external dependencies (subprocess, systemctl, etc.)

### Test Markers

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.requires_sudo` - Tests requiring sudo

## Code Style

- Follow PEP 8
- Use type hints where possible
- Keep lines under 100 characters
- Use descriptive variable names
- Add docstrings to public functions

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linters (`make check`)
5. Commit with conventional commits
6. Push to your fork
7. Open a Pull Request

## Directory Structure

```
wslaragon/
├── src/wslaragon/      # Main source code
│   ├── cli/           # CLI commands
│   │   ├── main.py    # Entry point
│   │   ├── site_commands.py
│   │   ├── service_commands.py
│   │   ├── php_commands.py
│   │   ├── mysql_commands.py
│   │   ├── ssl_commands.py
│   │   ├── node_commands.py
│   │   ├── nginx_commands.py
│   │   ├── doctor.py
│   │   └── agent.py
│   ├── core/          # Core functionality
│   │   ├── config.py
│   │   └── services.py
│   └── services/      # Service managers
│       ├── php.py
│       ├── nginx.py
│       ├── mysql.py
│       ├── sites.py
│       ├── site_creators.py  # Strategy pattern
│       ├── ssl.py
│       ├── backup.py
│       └── node/pm2.py
├── tests/             # Test suite
│   ├── conftest.py    # Shared fixtures
│   ├── unit/          # Unit tests (27 files)
│   └── integration/   # Integration tests (3 files)
├── docs/              # Documentation
├── scripts/           # Setup scripts
└── .github/           # GitHub workflows
```

## Getting Help

- Check [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- Open an issue on GitHub
- Check the wiki

---

Happy coding! 🚀