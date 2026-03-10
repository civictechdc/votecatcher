# ADR-0004: Python Linting and Type Checking Configuration

## Status

Accepted

## Context

The codebase uses Python 3.12+ with FastAPI and SQLModel. During Phase 0 setup, we encountered:

1. Pre-existing code using tabs for indentation (ruff W191 warnings)
2. Ruff formatter configured for tabs but W191 rule disallows tabs
3. Type checking producing 1000+ warnings about unknown types in third-party libraries
4. Critical type errors in demo_* files that would block Phase 1 work
5. Need for industry-standard code quality checks without blocking development

## Decision

Configure ruff and basedpyright with industry-standard rules while pragmatically handling pre-existing code:

### Ruff Configuration

```toml
[tool.ruff]
lint.select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM"]
lint.ignore = ["E203", "W191"]  # E203 for black compatibility, W191 for tab indentation

[tool.ruff.format]
indent-style = "tab"  # Existing codebase uses tabs

[tool.ruff.lint.isort]
known-first-party = ["app"]
```

**Rules added:**
- `I` - Import sorting (isort)
- `N` - Naming conventions
- `UP` - PyUpgrade (modernize code)
- `B` - Flake8-bugbear (detect common bugs)
- `C4` - Flake8-comprehensions
- `SIM` - Flake8-simplify

### Basedpyright Configuration

```toml
[tool.basedpyright]
typeCheckingMode = "standard"
exclude = ["app/data/database/local/demo_*.py"]

# Relax noisy warnings for third-party libraries
reportAny = "none"
reportUnknownVariableType = "none"
reportUnknownMemberType = "none"
reportUnknownArgumentType = "none"
reportUnknownParameterType = "none"
reportExplicitAny = "none"

# Keep critical errors
reportMissingImports = "error"
reportOptionalMemberAccess = "error"
reportOptionalOperand = "error"
reportUnreachable = "error"
```

## Consequences

### Positive

- **Incremental improvement**: Can add strictness over time without blocking current work
- **Industry standard checks**: Catches common bugs (B), naming issues (N), modernization opportunities (UP)
- **Clear upgrade path**: Can remove demo_* excludes and tighten type checking incrementally
- **Developer velocity**: Warnings don't block builds, errors do

### Negative

- **Technical debt**: demo_* files excluded from type checking may hide real issues
- **Inconsistent style**: Tabs remain in codebase (already pervasive)
- **Reduced type safety**: Unknown types from pandas/SQLModel won't be caught

### Neutral

- **Trade-off**: Pragmatism over perfection - prioritizing forward progress over fixing all pre-existing issues
- **Maintenance**: Configuration should be reviewed each phase to tighten rules

## Alternatives Considered

1. **Fix all errors before proceeding**
   - Pros: Clean slate, maximum type safety
   - Cons: 1000+ warnings, would delay Phase 1 significantly
   - Why not chosen: Pre-existing code not blocking MVP delivery

2. **Use mypy instead of basedpyright**
   - Pros: More widely adopted
   - Cons: Slower, less accurate type inference for modern Python
   - Why not chosen: basedpyright is faster and better for Pydantic/SQLModel

3. **Enforce spaces, reformat entire codebase**
   - Pros: Consistency with PEP 8 recommendation
   - Cons: Large diff, potential merge conflicts, no functional benefit
   - Why not chosen: Tabs already pervasive, not worth the churn

## Future Improvements

Phase by phase, we should:

1. **Phase 1**: Type-check `app/settings/settings_repo.py` and `app/data/database/local/demo_*.py`
2. **Phase 2**: Type-check `app/ocr/**`, `app/routers/file_route.py`, and `app/matching/fuzzy_match_helper.py`
3. **Phase 4**: Remove all temporary excludes, verify full type coverage
4. **Phase 5**: Consider enabling `reportUnusedImport = "error"` after cleanup
5. **Post-MVP**: Evaluate switching to spaces if team prefers

## Temporary Excludes Registry

| File Pattern | Exclude Reason | Target Phase for Removal |
|--------------|----------------|--------------------------|
| `app/data/database/local/demo_*.py` | Demo DB code, will be replaced in Phase 1 | Phase 1 |
| `app/settings/settings_repo.py` | Settings management, needs type hints | Phase 1 |
| `app/ocr/**` | OCR clients/handlers, complex async code | Phase 2 |
| `app/routers/file_route.py` | File upload routes, uses pandas | Phase 2 |
| `app/matching/fuzzy_match_helper.py` | Fuzzy matching, pandas integration | Phase 2 |

## References

- [Ruff rule definitions](https://docs.astral.sh/ruff/rules/)
- [Basedpyright configuration](https://docs.basedpyright.com/latest/configuration/config-files/)
- [PEP 8 - Style Guide](https://peps.python.org/pep-0008/)

---

**Date:** 2026-03-09
**Decision Makers:** Developer Agent (with user approval)
