# Ubuntu MCP Runtime Specification

## Purpose
Keep all MCP tools functional on native Ubuntu by aligning service names and agent initialization signatures with Ubuntu conventions.

## Requirements

### Requirement: Ubuntu service names in MCP runtime
The system MUST expose Ubuntu service names for Nginx, MariaDB, and PHP-FPM through the MCP runtime.

#### Scenario: MCP service status query
- GIVEN the MCP server is running on native Ubuntu
- WHEN an agent queries service status
- THEN it MUST receive names such as `nginx`, `mariadb`, and `php8.5-fpm`
- AND it MUST NOT receive WSL2-specific service names

### Requirement: Agent init signature compatibility
The system MUST update agent initialization signatures so agents receive the runtime context needed for Ubuntu operations.

#### Scenario: Agent initializes on Ubuntu
- GIVEN an agent is initialized on native Ubuntu
- WHEN it receives runtime context
- THEN the context MUST include the hosts file path, PHP version, FPM socket, and database user
- AND the agent MUST use these values for subsequent tool calls
