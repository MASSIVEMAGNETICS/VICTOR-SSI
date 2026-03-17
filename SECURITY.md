# Security Policy

## Supported Versions

We actively maintain the latest release on the `main` branch.  
Older versions may receive security patches on a best-effort basis.

| Branch / Version | Supported |
|-----------------|-----------|
| `main` (latest) | ✅ Yes |
| `develop` | ✅ Yes (pre-release) |
| Older tags | ⚠️ Best-effort only |

---

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Please report vulnerabilities directly and confidentially:

1. **Email:** SECURITY@massivemagnetics.com  
   Use the subject line: `[SECURITY] VICTOR-SSI — <short description>`

2. **PGP Encryption (optional but encouraged):**  
   If you wish to encrypt your report, request our PGP public key from the same email address. We will provide it promptly.

3. **What to include in your report:**
   - Description of the vulnerability and its potential impact
   - Affected component(s) and version/branch
   - Step-by-step reproduction instructions
   - Any proof-of-concept code or screenshots (please avoid destructive tests)
   - Suggested remediation if known

---

## Our Commitment

- We will acknowledge your report within **2 business days**.
- We will provide an initial assessment and timeline within **5 business days**.
- We will notify you when a fix is deployed.
- We will credit reporters in the changelog unless they request anonymity.
- We will not pursue legal action against good-faith security researchers acting responsibly.

---

## Scope

This security policy covers the following components of the VICTOR-SSI repository:

- `gateway/` — API Gateway (FastAPI)
- `desktop/electron/` — Electron desktop wrapper
- `docker-compose.yml` and infrastructure configuration
- GitHub Actions workflows (`.github/workflows/`)
- Scripts (`scripts/`)

Component repositories (ragflow, conscious-river, Liquidation-Analysis) have their own security policies. Please report issues in those repos directly to their maintainers.

---

## Out of Scope

- Vulnerabilities in third-party dependencies that have already been publicly disclosed and have available patches
- Social engineering attacks
- Issues in forked or unofficial versions of this software

---

## Security Best Practices for Operators

- **Never commit `.env` to source control.** Use `.env.example` as a template only.
- **Rotate `JWT_SECRET` regularly** and use a strong, random value in production.
- **Restrict Docker socket access** and run containers as non-root where possible.
- **Enable branch protection** on `main` and require signed commits.
- **Audit dependencies** regularly using `dependabot` (configured in this repo) and `npm audit` / `pip-audit`.
