# Architecture

## Overview
WSLaragon is a Python-based CLI tool for managing local web development environments in WSL2, leveraging native Linux services (Nginx, PHP-FPM, MariaDB).

## Patterns
- **CLI Wrapper**: `click` is used for command handling.
- **Service Managers**: Dedicated classes (`NginxManager`, `PHPManager`) in `services/` encapsulate service logic.
- **Agentic Skills**: Uses `.agent/skills` folder to define AI personas that can be loaded by the user or tools.
