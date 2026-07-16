# Archive Report: ubuntu-main-adaptation

## Archive Metadata

| Field | Value |
|-------|-------|
| Change name | ubuntu-main-adaptation |
| Archive date | 2026-07-15 |
| Artifact store | hybrid (Engram + OpenSpec) |
| Delivery strategy | force-chained |
| Chain strategy | stacked-to-main |
| Archive location | `openspec/changes/archive/2026-07-15-ubuntu-main-adaptation/` |
| Archive type | intentional-with-warnings |

## Executive Summary

The `ubuntu-main-adaptation` change has been archived. All implementation PRs (Phases 1–6) and the post-verify remediation batch (R1–R6) are complete. The verification report shows **PASS WITH WARNINGS**: zero critical findings, zero blockers, 15/15 requirements and 21/21 scenarios covered by tests, with the unit suite passing at 99.67 % coverage. Two Phase 7 VM/sudo integration tasks (7.2 and 7.3) were intentionally left as follow-up work, along with non-blocking findings F3–F8. The archive proceeded under explicit orchestrator instruction to close the SDD cycle with documented follow-ups.

## Artifact Provenance

### Engram observations

| Artifact | Observation ID | Topic |
|----------|---------------|-------|
| proposal | #237 | `sdd/ubuntu-main-adaptation/proposal` |
| spec | #238 | `sdd/ubuntu-main-adaptation/spec` |
| design | #239 | `sdd/ubuntu-main-adaptation/design` |
| tasks | #240 | `sdd/ubuntu-main-adaptation/tasks` |
| apply-progress | #242 | `sdd/ubuntu-main-adaptation/apply-progress` |
| verify-report | #245 | `sdd/ubuntu-main-adaptation/verify-report` |
| archive-report | (this report) | `sdd/ubuntu-main-adaptation/archive-report` |

No Engram review topics (`sdd/ubuntu-main-adaptation/review/*`) were found.

### OpenSpec files (archived)

| Artifact | Archived path |
|----------|---------------|
| proposal | `openspec/changes/archive/2026-07-15-ubuntu-main-adaptation/proposal.md` |
| exploration | `openspec/changes/archive/2026-07-15-ubuntu-main-adaptation/exploration.md` |
| specs | `openspec/changes/archive/2026-07-15-ubuntu-main-adaptation/specs/*/spec.md` |
| design | `openspec/changes/archive/2026-07-15-ubuntu-main-adaptation/design.md` |
| tasks | `openspec/changes/archive/2026-07-15-ubuntu-main-adaptation/tasks.md` |
| apply-progress | `openspec/changes/archive/2026-07-15-ubuntu-main-adaptation/apply-progress.md` |
| verify-report | `openspec/changes/archive/2026-07-15-ubuntu-main-adaptation/verify-report.md` |
| archive-report | `openspec/changes/archive/2026-07-15-ubuntu-main-adaptation/archive-report.md` |

## Task Completion Summary

| Phase | Status |
|-------|--------|
| Phase 1: Foundation | ✅ Complete |
| Phase 2: PHP-FPM & Nginx Wiring | ✅ Complete |
| Phase 3: Hosts, Sudo Keep-Alive & Permissions | ✅ Complete |
| Phase 4: MySQL User & Site Creators | ✅ Complete |
| Phase 5: Installer Scripts & Docs | ✅ Complete |
| Phase 6: MCP Runtime Alignment | ✅ Complete |
| Phase 7.1: Unit/integration/static verification | ✅ Complete |
| Phase 7.2: Ubuntu VM integration (`site create` for WordPress, Laravel, headless) | ⏳ Deferred follow-up |
| Phase 7.3: End-to-end harness checks (SSL/hosts, FPM socket, `php upload-limit`, `install.sh`) | ⏳ Deferred follow-up |
| Remediation R1–R6 (F1/F2 fixes and re-verification) | ✅ Complete |

Implementation tasks 1.1–6.3 and remediation tasks R1–R6 are checked complete in the persisted tasks artifact. Tasks 7.2 and 7.3 remain unchecked because they require a real Ubuntu VM/sudo environment that was not available in the apply/verify environment. They are documented as accepted follow-ups rather than stale checkboxes.

## Spec Sync

The change introduced seven new domains. Because `openspec/specs/` had no existing main specs, each delta spec was promoted directly to a new main spec.

| Domain | Action | Requirements | Scenarios |
|--------|--------|--------------|-----------|
| ubuntu-host-management | Created | 2 | 3 |
| ubuntu-php-fpm | Created | 3 | 5 |
| ubuntu-mysql-user | Created | 1 | 2 |
| ubuntu-site-creation | Created | 2 | 3 |
| ubuntu-installer | Created | 2 | 4 |
| ubuntu-mcp-runtime | Created | 2 | 2 |
| ubuntu-project-artifacts | Created | 3 | 2 |
| **Total** | **7 created** | **15** | **21** |

Source of truth now reflects the new behavior at:
- `openspec/specs/ubuntu-host-management/spec.md`
- `openspec/specs/ubuntu-php-fpm/spec.md`
- `openspec/specs/ubuntu-mysql-user/spec.md`
- `openspec/specs/ubuntu-site-creation/spec.md`
- `openspec/specs/ubuntu-installer/spec.md`
- `openspec/specs/ubuntu-mcp-runtime/spec.md`
- `openspec/specs/ubuntu-project-artifacts/spec.md`

## Verification State

| Metric | Value |
|--------|-------|
| Verdict | `pass_with_warnings` |
| Critical findings | 0 |
| Blockers | 0 |
| Requirements | 15/15 |
| Scenarios | 21/21 |
| Unit tests | 1369 passed, 99.67 % coverage |
| Integration tests | 32 passed, 1 skipped (`--no-cov`) |
| Shell lint | `shellcheck -x --severity=warning scripts/*.sh` clean |
| Python compile | syntax OK for requested files |

## Review Gate

No native review receipt or review ledger artifacts were present in either Engram or OpenSpec. The orchestrator explicitly chose to archive the change with open warnings and deferred VM verification. This archive is therefore marked as **intentional-with-warnings**.

## Accepted Follow-Ups (F3–F8)

| ID | Severity | Summary | Disposition |
|----|----------|---------|-------------|
| F3 | WARNING | Phase 7 VM integration tasks not executed | Deferred to a follow-up verification session on a fresh Ubuntu VM |
| F4 | WARNING | Installer sudoers lists may be missing `tee`, `setfacl`, `chmod`, `chown` | Fix before first release; document passwordless-sudo workaround if needed |
| F5 | WARNING | Spec-required deprecation note for `root` default missing | Add note to `docs/UBUNTU.md` and/or `config.py` before release |
| F6 | SUGGESTION | MCP instructions still WSL2-centric | Update when refreshing MCP branding |
| F7 | SUGGESTION | Placeholder repository URL in `scripts/install.sh` | Replace with real URL before public release |
| F8 | SUGGESTION | Integration test skipped due to missing MCP `app` export | Export/mock `app` or update the integration test |

## Risks

- F3 means end-to-end Ubuntu behavior (site creation, SSL/hosts, PHP-FPM socket detection, install/uninstall) has not been exercised on a real system.
- F4 means the installer may grant insufficient sudo privileges for `sudo tee`, `setfacl`, `chmod`, and `chown` operations on native Ubuntu.
- F5 leaves a spec-required deprecation notice unfulfilled, which may confuse users who still see `root` as the default on WSL2.

## Archive Verification

- [x] Main specs updated correctly (7 new specs created)
- [x] Change folder moved to archive
- [x] Archive contains all artifacts (proposal, exploration, specs, design, tasks, apply-progress, verify-report, archive-report)
- [x] Active changes directory no longer has `ubuntu-main-adaptation`
- [x] No CRITICAL issues in verification report
- [x] Archive report persisted to Engram and OpenSpec

## SDD Cycle State

Planned ✅ → Specified ✅ → Designed ✅ → Tasked ✅ → Applied ✅ → Verified (pass with warnings) ✅ → Archived ✅

The change is closed in the SDD pipeline. Follow-up work is tracked above.
