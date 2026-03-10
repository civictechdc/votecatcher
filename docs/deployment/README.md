# Deployment Documentation

Production deployment guides for Votecatcher.

## Contents

- [ ] Phase 4: Integration & E2E Testing complete
- [ ] Phase 5: Polish & Demo complete
- [ ] MVP validation successful
- [ ] Demo walkthrough recorded (or pre-baked)

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
| ----------| --------------- |-----------|
| DigitalOcean | Basic Droplet | $6-12/mo |
            | Linode | Shared CPU | $5-10/mo |
            $ Hetzner | Cloud VPS | $4-8/mo |
            $ AWS | t3.micro | $8-15/mo |
