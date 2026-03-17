# Contributing to VICTOR-SSI

Thank you for your interest in contributing to VICTOR-SSI (Aether Hub)! This document outlines the process and standards for contributing to this project.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Branch Naming Conventions](#branch-naming-conventions)
3. [Pull Request Process](#pull-request-process)
4. [Code Style](#code-style)
5. [Tests](#tests)
6. [Commit Messages](#commit-messages)
7. [Issue Reporting](#issue-reporting)

---

## Getting Started

1. Fork the repository and clone your fork:
   ```bash
   git clone git@github.com:<your-username>/VICTOR-SSI.git
   cd VICTOR-SSI
   ```

2. Bootstrap the component repos:
   ```bash
   ./scripts/bootstrap_submodules.sh --method=clone
   ```

3. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

4. Verify the stack starts:
   ```bash
   docker-compose up --build
   ```

---

## Branch Naming Conventions

Use the following prefixes for branch names:

| Prefix | Purpose | Example |
|--------|---------|---------|
| `feat/` | New features | `feat/rbac-middleware` |
| `fix/` | Bug fixes | `fix/gateway-health-check` |
| `docs/` | Documentation only | `docs/architecture-update` |
| `chore/` | Maintenance, tooling | `chore/update-dependencies` |
| `scaffold/` | New scaffolding / boilerplate | `scaffold/k8s-manifests` |
| `refactor/` | Code restructuring | `refactor/gateway-routing` |
| `test/` | Test additions/fixes | `test/gateway-unit-tests` |

---

## Pull Request Process

1. **Create a branch** from `develop` (or `main` for hotfixes):
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feat/my-feature
   ```

2. **Make your changes.** Keep PRs focused and small — one logical change per PR.

3. **Verify locally:**
   ```bash
   make lint
   make build
   docker-compose up --build
   ```

4. **Open a PR** targeting `develop` (or `main` for hotfixes).
   - Fill in the [PR template](.github/PULL_REQUEST_TEMPLATE.md).
   - Link any related issues using `Fixes #<issue-number>`.

5. **Require at least 1 review** from a CODEOWNER before merging.

6. **Squash merge** is preferred to keep history clean.

---

## Code Style

### Python (gateway/)

- Follow [PEP 8](https://peps.python.org/pep-0008/) with a max line length of 120.
- Use type hints for all function signatures.
- Use `flake8` for linting and `black` for formatting:
  ```bash
  black gateway/ && flake8 gateway/ --max-line-length=120
  ```
- Use `isort` for import ordering:
  ```bash
  isort gateway/
  ```

### JavaScript (desktop/electron/)

- Follow the [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript).
- Use `eslint` for linting:
  ```bash
  cd desktop/electron && npx eslint . --ext .js
  ```

### YAML / Dockerfiles / Shell Scripts

- Validate shell scripts with `shellcheck`.
- Keep Dockerfiles minimal; use slim/alpine base images where possible.
- Sort environment variables alphabetically in `docker-compose.yml`.

---

## Tests

- **Gateway:** Add tests in `gateway/tests/` using `pytest`.
  ```bash
  cd gateway && pytest -q
  ```
- **Desktop:** Add tests using Jest if applicable.
- CI will run tests automatically on push. All tests must pass before merging.
- Do not disable or skip tests without a documented reason.

---

## Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <short summary>

[optional body]

[optional footer]
```

Examples:
```
feat(gateway): add /orchestrator/status endpoint
fix(ci): correct build context for research-agent
docs(readme): update quickstart commands
chore(deps): bump electron to 29.1.0
```

Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `style`, `ci`, `perf`

---

## Issue Reporting

- Search existing issues before opening a new one.
- Use the provided [bug report template](.github/ISSUE_TEMPLATE/bug_report.md) for bugs.
- For security vulnerabilities, see [SECURITY.md](./SECURITY.md) — **do not open public issues for security bugs**.

---

## Code of Conduct

All contributors are expected to follow the [Code of Conduct](./CODE_OF_CONDUCT.md). Please read it before contributing.
