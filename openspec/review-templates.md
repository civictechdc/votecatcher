# Review Templates

## Decision Template

For presenting developer concerns to user:

```markdown
## Developer Concern - User Decision Required

### D[N]: [Issue Title]

**Developer Remark:**
> [Exact quote from developer notes]

**Options:**

| Option | Pros | Cons |
|--------|------|------|
| A) [Name] | [Pro] | [Con] |
| B) [Name] | [Pro] | [Con] |

**Recommendation:** Option X ([reason])

**Your decision:** _______
```

---

## Finding Template

For documenting code issues:

```markdown
#### R[N]: [Issue Title]

**File:** `path/to/file.py:LINE`

**Code:**
```python
# Relevant code snippet
```

**Issue:** [Why this is a problem]

**Fix:**
```python
# Corrected code
```

**Citation:** [Link to docs/spec/standard]

**Severity:** 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low
```

---

## Phase Review Template

For updating phase document:

```markdown
## Reviewer Section

**Reviewer:** [Name]
**Date:** YYYY-MM-DD
**Status:** 🔴 Blocked | 🟡 Needs Changes | 🟢 Approved

### Developer Remarks Triage

| ID | Category | Resolution |
|----|----------|------------|
| D1 | Concern | ✅ Option A chosen per user |
| D2 | Question | ✅ Clarified: [answer] |
| D3 | Blocker | ⏳ Pending user decision |

### Findings

| ID | Severity | File | Issue | Action |
|----|----------|------|-------|--------|
| R1 | 🔴 | `file.py:45` | SQL injection | Fix before merge |
| R2 | 🟡 | `file.py:23` | Missing docstring | Nice to have |

### Details

[Detailed finding entries using template above]

### Summary

- **Blocking:** R1
- **Required before merge:** R1
- **Nice to have:** R2, R3

### Developer Must Read

Before next phase:
1. Fix R1 (SQL injection)
2. Resolve D3 (awaiting user decision)
```

---

## Scanner Results Template

For documenting automated findings:

```markdown
### Automated Scan Results

| Scanner | Status | Issues |
|---------|--------|--------|
| ruff | ✅ Pass | 0 |
| basedpyright | ✅ Pass | 0 |
| bandit | ⚠️ Warning | 2 (see below) |
| gitleaks | ✅ Pass | 0 |

#### Bandit Findings

| ID | Test | File | Severity | Action |
|----|------|------|----------|--------|
| B1 | B101 | `test_file.py` | Low | Assert in test, expected |
```
