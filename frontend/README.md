# VoteCatcher Frontend

SvelteKit 5 application for the VoteCatcher campaign management platform.

## Tech Stack

- **Framework**: SvelteKit 2, Svelte 5
- **Language**: TypeScript
- **Styling**: Tailwind CSS v4
- **Auth**: Better Auth
- **ORM**: Drizzle
- **Testing**: Vitest (unit), Playwright (e2e)
- **Linting**: oxlint, oxfmt
- **Package Manager**: Bun 1.3.14

## Quick Start

```bash
bun install
cp .env.example .env
bun run dev
```

Open http://localhost:5173

## Scripts

| Command             | Description                         |
| ------------------- | ----------------------------------- |
| `bun run dev`       | Start dev server                    |
| `bun run build`     | Production build                    |
| `bun run preview`   | Preview production build            |
| `bun run test`      | Run all tests (vitest + playwright) |
| `bun run test:unit` | Run unit tests only                 |
| `bun run test:e2e`  | Run e2e tests only                  |
| `bun run lint`      | Lint with oxlint                    |
| `bun run lint:fix`  | Auto-fix lint issues                |
| `bun run fmt`       | Format with oxfmt                   |
| `bun run fmt:check` | Check formatting                    |
| `bun run check`     | Type check with svelte-check        |

## Project Structure

```
frontend/
├── src/
│   ├── lib/            # Shared code
│   │   ├── components/ # UI components
│   │   ├── server/     # Server-only code (auth, DB)
│   │   └── types/      # TypeScript types
│   ├── routes/         # SvelteKit routes (file-based routing)
│   ├── stories/        # Storybook stories
│   └── hooks.server.ts # Server middleware
├── e2e/                # Playwright end-to-end tests
├── tests/              # Vitest unit/component tests
├── static/             # Static assets
└── drizzle.config.ts   # Drizzle ORM configuration
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable             | Required | Description                        |
| -------------------- | -------- | ---------------------------------- |
| `PUBLIC_API_URL`     | Yes      | Backend API URL (no `/api` suffix) |
| `PUBLIC_DEMO_MODE`   | No       | Enable demo mode client-side       |
| `DEMO_MODE`          | No       | Enable demo mode server-side       |
| `ORIGIN`             | No       | App origin for CORS                |
| `DATABASE_URL`       | No       | PostgreSQL for server-side auth    |
| `BETTER_AUTH_SECRET` | No       | Session encryption secret          |

## Related Documentation

- [Running Locally](../docs/running-locally.md) — full development setup
- [Configuration Modes](../docs/configuration-modes.md) — all config options
- [Root README](../README.md) — project overview
