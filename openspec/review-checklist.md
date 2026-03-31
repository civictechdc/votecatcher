# Review Checklist

## Quality

- [ ] Code follows project conventions (ruff passes)
- [ ] Types are correct (basedpyright passes)
- [ ] No dead code or unused imports
- [ ] Functions are single-purpose (<30 lines)
- [ ] No deep nesting (>3 levels)
- [ ] Meaningful names (no abbreviations)
- [ ] DRY - no duplicated logic
- [ ] YAGNI - no speculative features
- [ ] Tests cover new code (pytest passes)
- [ ] Docstrings on public functions/classes

## Security

- [ ] No hardcoded secrets (gitleaks passes)
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (parameterized queries)
- [ ] Secrets use `SecretStr`, never logged/serialized
- [ ] File paths validated (no traversal)
- [ ] CORS configured correctly
- [ ] Rate limiting on sensitive endpoints
- [ ] Error messages don't leak internals
- [ ] No `eval()`, `exec()`, `__import__()`
- [ ] Dependencies checked (pip-audit)

## Spec Compliance

- [ ] Implementation matches design doc
- [ ] All required files created
- [ ] API endpoints match spec
- [ ] Database schema matches spec
- [ ] Environment variables documented
- [ ] Exit gates defined and passing

## Accessibility (Frontend)

- [ ] Semantic HTML (landmarks, headings, lists)
- [ ] ARIA labels where needed
- [ ] Keyboard navigation (Tab, Enter, Escape)
- [ ] Focus management (visible indicators)
- [ ] Color contrast (WCAG AA)
- [ ] Screen reader announcements for dynamic content

## Performance

- [ ] No N+1 queries
- [ ] Appropriate indexing
- [ ] Pagination on list endpoints
- [ ] No blocking I/O in async code

## Testing

- [ ] Unit tests for new logic
- [ ] Integration tests for endpoints
- [ ] Edge cases covered
- [ ] Error paths tested
- [ ] Tests are deterministic (no flakiness)
