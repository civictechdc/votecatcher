# Agent Code Quality Notes

Use this when changing Python, refactoring legacy code, or writing tests.

## Python Readability

- Prefer guard clauses and early returns over deep nesting.
- Use `' '.join(filter(None, parts))` for delimited strings built from optional parts.
- Extract repeated blocks when duplication is already obvious; do not invent abstractions for one-off code.
- Use ternaries for simple two-branch defaults. Use full `if` blocks when branches have side effects or complex logic.
- Remove dead wrappers that only delegate without adding behavior.
- Use named constants for repeated literals that carry domain meaning.

## Legacy Refactoring

- Clean only the code you are already touching unless the user asks for a broader refactor.
- Prefer small safe cleanups: flatten conditionals, remove unused imports, extract repeated conditionals, replace long `isinstance` chains with clearer dispatch.
- Preserve behavior first. Add tests before changing risky logic.

## Test Discipline

- Assert behavioral contracts: what the system must do, not how it happens internally.
- Avoid asserting internal method calls unless the call is the public contract.
- Avoid fragile checks like `repr(type(...))` strings.
- Prefer negative contract assertions when useful, such as proving `.all()` is not called for streaming queries.

## Nesting Watch

When loop bodies reach three or more nested levels, pause and flatten with guards, extracted helpers, or clearer condition order.
