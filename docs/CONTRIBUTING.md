# Contributing to WSLaragon

Thank you for your interest in contributing to WSLaragon!

## Development Setup

### Prerequisites

- Python 3.8+
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
| **ruff** | Linting & imports | `ruff check src/` |
| **black** | Code formatting | `black src/` |
| **isort** | Import sorting | `isort src/` |
| **mypy** | Type checking | `mypy src/` |
| **pytest** | Testing | `pytest` |

### Pre-commit Hooks

Install pre-commit hooks for automatic code quality checks:

```bash
pip install pre-commit
pre-commit install
```

## Testing

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# With coverage
pytest --cov=src --cov-report=html
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
4. Run tests and linters
5. Commit with conventional commits
6. Push to your fork
7. Open a Pull Request

## Directory Structure

```
wslaragon/
├── src/wslaragon/      # Main source code
│   ├── cli/           # CLI commands
│   ├── core/          # Core functionality
│   └── services/      # Service managers
├── tests/             # Test suite
│   ├── unit/          # Unit tests
│   └── integration/   # Integration tests
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