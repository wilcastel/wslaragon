# Delta for Ubuntu Site Creation

## MODIFIED Requirements

### Requirement: Sudo keep-alive during site creation

The system MUST keep sudo credentials alive only while an explicitly interactive CLI site-creation flow performs legacy elevated operations. The hidden `site create --privilege-mode=interactive|agent` option MUST default to `interactive`. Agent mode MUST require an injected ready privilege client, MUST construct neither `sudo -v` nor `SudoKeepAlive`, and MUST NOT silently downgrade to interactive behavior. MCP-driven normal and headless creation MUST use the fixed helper only for selected validated registration and access operations.
(Previously: Site creation used persistent sudo credentials while it performed elevated operations.)

#### Scenario: Long-running interactive site creation
- GIVEN interactive CLI site creation invokes legacy `sudo` operations for hosts, Nginx, and PHP-FPM changes
- WHEN the operation exceeds the sudo timeout window
- THEN the system MUST refresh sudo credentials before expiration
- AND the operation MUST complete without interactive prompts

#### Scenario: Agent-mode site creation
- GIVEN site creation is explicitly invoked with `--privilege-mode=agent` and an injected ready client
- WHEN privileged registration work is needed
- THEN the system MUST NOT invoke interactive sudo validation or `SudoKeepAlive`
- AND it MUST use the fixed helper boundary

#### Scenario: Agent client is unavailable
- GIVEN site creation is explicitly invoked with `--privilege-mode=agent` without a ready injected client
- WHEN creation begins
- THEN the system MUST return a safe failure
- AND it MUST NOT fall back to interactive creation

### Requirement: ACL-based `www-data` permissions

The system MUST grant `www-data` read access to site files using POSIX ACLs, falling back to `chmod` when ACL tools are unavailable. For agent-mode normal and headless creation, any privileged application of that generated-site access policy MUST be requested through the fixed helper and MUST remain constrained to the validated generated site root.
(Previously: The ACL or chmod policy did not constrain the agent-driven privilege boundary.)

#### Scenario: ACL tools available
- GIVEN `setfacl` is installed
- WHEN a new site directory is created
- THEN the system MUST run `setfacl -R -m u:www-data:rx` on the directory
- AND `www-data` MUST be able to read site files

#### Scenario: ACL tools unavailable
- GIVEN `setfacl` is not installed
- WHEN a new site directory is created
- THEN the system MUST fall back to `chmod -R o+rx` on the directory
- AND the site MUST remain accessible by the web server

#### Scenario: Agent access policy request
- GIVEN an agent-created site has a validated generated root
- WHEN its web-server access policy requires elevation
- THEN the system MUST submit only the generated-root policy through the fixed helper
- AND it MUST NOT authorize permissions outside that root

## ADDED Requirements

### Requirement: Agent-mode registration lifecycle

The system MUST preserve unprivileged ownership of scaffolding, certificates, database creation, and `~/.wslaragon` state in agent mode. Normal creation MUST submit exactly one registration and commit user state only after it succeeds. Headless creation MUST submit backend and frontend registrations; if the second fails, it MUST remove only the completed derived registration, MUST preserve scaffolding, certificates, and database for repair, and MUST NOT commit user state.

#### Scenario: Normal agent creation succeeds
- GIVEN agent-mode normal creation completes its unprivileged work
- WHEN its single registration succeeds
- THEN the system MUST commit user state after that success
- AND it MUST preserve user ownership of unprivileged artifacts

#### Scenario: Headless second registration fails
- GIVEN agent-mode headless creation has successfully registered its backend
- WHEN frontend registration fails
- THEN the system MUST remove only the completed backend-derived registration
- AND it MUST preserve unprivileged artifacts and leave user state uncommitted
