# Versioning

VoteCatcher uses [semantic versioning](https://semver.org/) managed by [commitizen](https://commitizen-tools.github.io/commitizen/).

## Version Scheme

```
MAJOR.MINOR.PATCH[-PRERELEASE.NUMBER]

Examples:
  1.0.0-alpha.1    ← current
  1.0.0-alpha.2    ← prerelease bump
  1.0.0-beta.1     ← promote to beta
  1.0.0            ← stable release
  1.1.0-alpha.1    ← next minor cycle
```

| Segment | When it changes | Example |
|---------|----------------|---------|
| MAJOR | Breaking API changes | `1.x.x` → `2.x.x` |
| MINOR | New features, backwards-compatible | `1.0.x` → `1.1.x` |
| PATCH | Bug fixes, no API changes | `1.0.0` → `1.0.1` |
| PRERELEASE | Alpha/beta/rc cycle | `-alpha.1` → `-alpha.2` |

## Where Versions Live

Commitizen updates all of these in one command:

| File | Format |
|------|--------|
| `.cz.toml` | `version = "1.0.0-alpha.1"` |
| `backend/pyproject.toml` | `version = "1.0.0-alpha.1"` |
| `frontend/package.json` | `"version": "1.0.0-alpha.1"` |

Git tags follow the pattern `v1.0.0-alpha.1`.

## Commands

All version commands use [just](https://github.com/casey/just):

### Check current version

```bash
just version
```

### Auto-bump (reads conventional commits)

```bash
just release
```

Commitizen scans commits since the last tag and decides the bump level:

| Commit prefix | Bump |
|---------------|------|
| `feat:` | MINOR |
| `fix:` | PATCH |
| `feat!:` or `BREAKING CHANGE:` | MAJOR |
| `docs:`, `chore:`, `refactor:` | No bump |

### Manual bump (override auto-detection)

```bash
just release-force patch     # force patch bump
just release-force minor     # force minor bump
just release-force major     # force major bump
```

### Prerelease cycle

```bash
just release-prerelease      # alpha.1 → alpha.2
```

To promote across prerelease stages, edit `.cz.toml` manually:

```toml
# Change from:
version = "1.0.0-alpha.3"
# To:
version = "1.0.0-beta.1"
```

Then commit and tag:

```bash
git add .cz.toml backend/pyproject.toml frontend/package.json
git commit -m "chore: promote to beta"
git tag v1.0.0-beta.1
git push --tags
```

### Stable release (drop prerelease suffix)

```bash
just release-stable
```

## Workflow Example

```text
1.0.0-alpha.1   ← initial setup
       ↓  just release (auto or manual)
1.0.0-alpha.2   ← another alpha
       ↓  promote to beta (edit .cz.toml)
1.0.0-beta.1
       ↓  just release-stable
1.0.0           ← first stable release
       ↓  just release-force minor
1.1.0-alpha.1   ← next cycle
```

## Conventional Commits

Auto-bump relies on [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(backend): add batch export endpoint
fix(frontend): correct pagination offset
docs: update versioning guide
chore(ci): bump action versions
refactor(matching): extract scoring logic
```

**Breaking changes** use `!` after the scope or a `BREAKING CHANGE:` footer:

```
feat(api)!: change /jobs response schema

BREAKING CHANGE: jobs endpoint returns array instead of object.
```

## Configuration

Commitizen config lives in [.cz.toml](../../.cz.toml) at the repo root.

```toml
[tool.commitizen]
name = "cz_conventional_commits"
tag_format = "v$version"
version_scheme = "semver"
version = "1.0.0-alpha.1"
update_changelog_on_bump = true
version_files = [
    "backend/pyproject.toml:version",
    "frontend/package.json:\"version\"",
]
```

## Troubleshooting

### "No commits found since last tag"

Commitizen only bumps when there are conventional commits since the last tag. Use `just release-force` to override.

### Version files out of sync

Commitizen updates all `version_files` in `.cz.toml` atomically. If they drift, fix manually and run `just version` to verify.

### Tag already exists

```bash
git tag -d v1.0.0-alpha.1        # delete local
git push origin :refs/tags/v1.0.0-alpha.1  # delete remote
```
