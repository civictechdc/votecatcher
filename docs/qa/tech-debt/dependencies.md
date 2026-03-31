# Dependencies Tech Debt

> Last updated: 2026-03-29
> Source: osv-scanner v2.3.5, Trivy v0.69.3
> Status: Baseline captured (Phase 0)

## Critical

| Finding | Package | CVE | CVSS | Fixed Version | Source |
|---------|---------|-----|------|---------------|--------|
| RCE via deserialization | `langchain-core` 1.1.1 | GHSA-c67j-w6g6-q2cm | 9.3 | 1.2.5 | backend/uv.lock |

## High

| Finding | Package | CVE | CVSS | Fixed Version | Source |
|---------|---------|-----|------|---------------|--------|
| Pillow DoS | `pillow` 12.0.0 | GHSA-cfh3-3jmp-rvhc | 8.9 | 12.1.1 | backend/uv.lock |
| urllib3 info leak | `urllib3` 2.6.0 | GHSA-38jv-5279-wg99 | 8.9 | 2.6.3 | backend/uv.lock |
| python-multipart | `python-multipart` 0.0.20 | GHSA-wp53-j4wj-2cfg | 8.6 | 0.0.22 | backend/uv.lock |
| cryptography | `cryptography` 46.0.3 | GHSA-r6ph-v2qm-q3c2 | 8.2 | 46.0.5 | backend/uv.lock |
| protobuf | `protobuf` 6.33.2 | GHSA-7gcm-g887-7qv7 | 8.2 | 6.33.5 | backend/uv.lock |
| langchain-core (add'l) | `langchain-core` 1.1.1 | GHSA-qh6h-p6c9-ff54 | 7.5 | 1.2.22 | backend/uv.lock |
| pyjwt | `pyjwt` 2.10.1 | GHSA-752w-5fwx-jx9f | 7.5 | 2.12.0 | backend/uv.lock |
| pyasn1 (x2) | `pyasn1` 0.6.1 | GHSA-jr27-m4p2-rc6r, GHSA-63vm-454h-vhhq | 7.5 | 0.6.3 | backend/uv.lock |
| tornado | `tornado` 6.5.2 | GHSA-qjxf-f2mg-c6mc | 8.7 | 6.5.5 | backend/uv.lock |
| orjson | `orjson` 3.11.5 | GHSA-hx9q-6w63-j58v | 7.7 | 3.11.6 | backend/uv.lock |
| rollup | `rollup` 4.57.1 | GHSA-mw96-cpmx-2vgc | 8.8 | 4.59.0 | frontend-svelt/bun.lock |
| storybook | `storybook` 10.2.8 | GHSA-mjf5-7g4m-gx5w | 8.9 | 10.2.10 | frontend-svelt/bun.lock |
| flatted | `flatted` 3.3.3 | GHSA-rf6f-7fwh-wjgh | 8.9 | 3.4.2 | frontend-svelt/bun.lock |
| kysely (x2) | `kysely` 0.28.11 | GHSA-8cpq-38p9-67gx, GHSA-wmrf-hv6w-mr66 | 8.x | 0.28.14 | frontend-svelt/bun.lock |
| minimatch (x6) | `minimatch` 3.1.2, 9.0.5 | Multiple | 8.x | 3.1.4, 9.0.7 | frontend-svelt/bun.lock |
| undici (x5) | `undici` 7.22.0 | Multiple | 7.5 | 7.24.0 | frontend-svelt/bun.lock |

## Medium

26 Medium-severity vulnerabilities across PyPI and npm. See `baselines/osv-baseline.txt` for full list.

## Low / Informational

- **Total**: 63 vulnerabilities (1 Critical, 28 High, 26 Medium, 7 Low, 1 Unknown)
- **Fixable**: 62 of 63 (only `pygments` GHSA-5239-wwwm-4pmq has no fix yet)
- **Ecosystems**: 2 (PyPI: backend/uv.lock, npm: frontend-svelt/bun.lock)
- **35 packages affected** across 255 PyPI packages and 762 npm packages
- **Trivy**: backend/uv.lock has 11 vulns (1 CRITICAL, 10 HIGH); frontend/package-lock.json has 3 vulns
- **Licenses**: 8 packages with UNKNOWN licenses — review needed
