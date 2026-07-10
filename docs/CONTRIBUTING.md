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
- **1,259 tests** total (1,226 unit + 33 integration)
- **100% coverage** on unit tests
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

Ver [docs/STRUCTURE.md](STRUCTURE.md) para la estructura completa del proyecto.

## Getting Help

- Check [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- Open an issue on GitHub
- Check the wiki

---

Happy coding! 🚀