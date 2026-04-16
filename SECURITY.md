# Security Policy

## Reporting Vulnerabilities

We take security seriously. If you discover a security vulnerability, please report it privately to us via [GitHub Private Vulnerability Reporting](https://github.com/civictechdc/votecatcher/security/advisories/new).

**Do not** disclose vulnerabilities publicly before we have a chance to address them.

### Reporting Process

1. Submit your report through GitHub's Private Vulnerability Reporting
2. Include details about the vulnerability, reproduction steps, and affected versions
3. We will acknowledge your report within 7 days when possible
4. We will work with you to validate and fix the issue
5. Once a fix is released, we will credit you in the advisory unless you prefer anonymity

## Response Timeline

This is a volunteer-run project, so we cannot provide guaranteed SLAs. We do our best to:

- Acknowledge reports within 7 days when possible
- Provide an initial assessment within 14 days
- Release a fix for critical vulnerabilities within 30 days (depending on severity and volunteer availability)

Response times may vary based on severity, volunteer availability, and complexity of the issue.

## Supported Versions

VoteCatcher is currently in pre-1.0 development. Only the latest release receives security updates.

| Version | Supported |
|---------|-----------|
| Latest (pre-1.0) | ✅ Yes |
| All older versions | ❌ No |

**Recommendation:** Always upgrade to the latest release for security fixes.

## Disclosure Policy

We follow coordinated disclosure:

1. Vulnerabilities are fixed before public disclosure
2. A security advisory is published alongside the fix release
3. Reporters are credited in the advisory unless they prefer anonymity
4. Public disclosure happens only after a fix is available

## Security Best Practices for Self-Hosters

If you're self-hosting VoteCatcher, follow these security practices:

### Environment Variables

- **Never commit API keys or secrets** to version control
- Use environment variables for all sensitive configuration
- Copy `.env.example` files to `.env` and fill in your values
- See `backend/.env.example` and `frontend/.env.example` for all required secrets

Required secrets:
- `DATABASE_URL` — database connection string
- `BETTER_AUTH_SECRET` — session encryption key
- `OCR_PROVIDER_API_KEY` — LLM/OCR provider key (unless using simulation mode)
- `SUPABASE_SERVICE_KEY` — Supabase admin key (if using Supabase)

### Database Security

- **Use PostgreSQL in production**, not SQLite
- Create a dedicated database user with strong credentials
- Restrict database access to the application server only
- Use environment variables for database credentials, not config files
- Enable SSL for database connections in production

### Supabase (if applicable)

- Use separate anon and service keys
- Store the service key securely — it has full database access
- Never expose the service key to client-side code
- Use Row Level Security (RLS) policies for data access control

### Production Deployment

- **Always use HTTPS** in production
- Use a reverse proxy (nginx, Caddy) with SSL/TLS termination
- Keep dependencies updated: `just security-scan`
- Monitor GitHub Dependabot alerts and code scanning results
- Review logs regularly for suspicious activity

### Pre-Deployment Checklist

Before deploying to production:

```bash
# Run security scans
just security-scan

# Check for known vulnerabilities
just sca
```

Verify:
- [ ] Environment variables are set and not committed
- [ ] HTTPS is enabled
- [ ] Database credentials are strong
- [ ] OCR provider API key is restricted
- [ ] Dependencies are up to date

## Scope

### In Scope

- Application code in `backend/` and `frontend/`
- Dependencies (Python and Node.js packages)
- Authentication and authorization mechanisms
- Input validation and sanitization
- API security
- Database access controls
- Configuration management

### Out of Scope

- Social engineering attacks
- Denial of service attacks against self-hosted instances
- Issues in third-party services (e.g., Supabase, OpenAI)
- Issues requiring physical access to infrastructure
- Issues already disclosed publicly (without coordination)

## Security Tools

VoteCatcher uses these security tools:

| Tool | Purpose | Usage |
|------|---------|-------|
| `just security-scan` | Run all security scans | Pre-deployment |
| Dependabot | Automated dependency updates | GitHub integration |
| GitHub Code Scanning | SAST via CodeQL | CI pipeline |
| Bandit | Python security linter | CI pipeline |
| `uv audit` | Python dependency vulnerabilities | CI pipeline |
| `bun audit` | Node.js dependency vulnerabilities | CI pipeline |

See [CONTRIBUTING.md](CONTRIBUTING.md) for CI security checks.
