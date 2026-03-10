# Deployment Documentation

Production deployment guides for Votecatcher.

## Contents

Deployment documentation will be added in Phase 5 (after MVP completion).

## Planned Topics

- Single VPS deployment ($5-20/mo)
- Docker Compose setup
- Environment configuration
- Database setup (PostgreSQL)
- SSL/TLS certificates
- Backup strategies
- Monitoring and logging
- Security hardening

## Current Status

Votecatcher is in active development (Phase 3). Production deployment guides will be written after:

- [ ] Phase 4: Integration & E2E Testing complete
- [ ] Phase 5: Polish & Demo complete
- [ ] MVP validation successful

## Quick Reference

For local development, see [Running Locally](../running-locally.md).

## Technology Stack

Production deployment will use:

- **Application Server**: Uvicorn (FastAPI)
- **Reverse Proxy**: Nginx
- **Database**: PostgreSQL
- **Process Manager**: Systemd or Docker
- **SSL**: Let's Encrypt (Certbot)

## Estimated Costs

Target: $5-20/month for single VPS deployment

| Provider | Instance Type | Est. Cost |
|----------|---------------|-----------|
| DigitalOcean | Basic Droplet | $6-12/mo |
| Linode | Shared CPU | $5-10/mo |
| Hetzner | Cloud VPS | $4-8/mo |
| AWS | t3.micro | $8-15/mo |

## Questions?

See [PROGRESS.md](../../openspec/PROGRESS.md) for development status and timeline.
