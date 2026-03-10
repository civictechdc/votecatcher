# OpenSpec Skills

Custom skills for the Votecatcher project that integrate with the OpenSpec workflow.

⚠️ **IMPORTANT: Explicit Invocation Only**
These skills are intentionally kept outside `.agent/skills/` to prevent auto-triggering. They will NOT appear in `npx openskills list` and will NOT be automatically loaded by agents. You must explicitly load them.

## Available Skills

### spec-code-reviewer

**Purpose:** Reviews code changes against SPEC.md requirements to identify implementation gaps and produce actionable feedback.

**⚠️ Explicit Invocation Required**
This skill will NOT auto-trigger. It must be explicitly loaded using one of the methods below.

**How to Load (Choose One):**

```bash
# Option 1: Direct file read
cat openspec/.skills/spec-code-reviewer.md

# Option 2: Tell your agent explicitly
# "Read the file at openspec/.skills/spec-code-reviewer.md and follow its instructions"
```

**Verification:**
```bash
# Should NOT appear in this list:
npx openskills list | grep spec-code-reviewer
# (No output = correct, skill is hidden)
```

**Why Explicit-Only?**
- Prevents accidental auto-triggering during normal development
- Ensures intentional, focused spec compliance reviews
- Avoids interfering with other review workflows
- Keeps the skill context isolated to when you actually need it

**What NOT to Expect:**
```bash
# ❌ This will NOT work:
npx openskills read spec-code-reviewer
# Error: Skill not found (by design)

# ❌ Agents will NOT auto-load it based on keywords
# Even if you mention "review" or "SPEC.md", this skill won't trigger

# ❌ It won't appear in skills list
npx openskills list
# (spec-code-reviewer intentionally absent)

# ❌ No Makefile target
make spec-review
# make: *** No rule to make target 'spec-review'. Stop.
```

**Output:** `COMMENTS.md` with:
- Requirements traceability matrix
- Critical blocking issues (🔴)
- Important issues (🟡)
- Phase gate assessment
- Test coverage analysis
- Actionable recommendations

**Example Output:**
```markdown
# Code Review: FileService Implementation

## Executive Summary
FileService implements PDF cropping correctly but missing confidence 
calibration required by SPEC.md §3.4. Cannot proceed to Phase 3.

## Phase Gate Assessment
🔴 CANNOT PROCEED - 1 blocking issue

### Exit Criteria Status
- [x] File upload creates crops correctly
- [ ] Confidence thresholds calibrated with user ⬅️ BLOCKING
```

## Integration with Development Workflow

### Pre-Commit Review

Add to your workflow:
```bash
# Before committing phase work
npx openskills read spec-code-reviewer

# Review COMMENTS.md
# Fix blocking issues
# Commit when approved
```

### CI/CD Integration

The skill can be integrated into GitHub Actions:
```yaml
- name: Spec Compliance Check
  run: |
    npx openskills read spec-code-reviewer
    if grep -q "🔴 CANNOT PROCEED" COMMENTS.md; then
      echo "Blocking issues found"
      exit 1
    fi
```

### Phase Sign-off Process

1. Complete implementation tasks
2. Run exit criteria commands (from TODO.md)
3. Load spec-code-reviewer skill
4. Review COMMENTS.md
5. Address blocking issues
6. Re-review until approved
7. Mark phase complete in TODO.md

## Skill Composition

This skill works well with:
- `code-review-excellence` - For detailed code review patterns
- `verification-before-completion` - For exit criteria validation
- `test-driven-development` - When tests are missing
- `systematic-debugging` - When issues are found

## Customization

### Adjusting Review Depth

The skill focuses on requirements gaps. For deeper code review:
```bash
npx openskills read spec-code-reviewer,code-review-excellence
```

### Security Focus

For security-focused review:
```bash
npx openskills read spec-code-reviewer,security-best-practices
```

## Troubleshooting

### Skill Not Loading

Ensure you have openskills installed:
```bash
npm install -g openskills
```

### COMMENTS.md Not Generated

The skill requires:
- `openspec/SPEC.md` to exist
- `openspec/TODO.md` to exist
- Code changes to review (git diff or file changes)

### False Positives

If the reviewer flags issues that are actually correct:
1. Check SPEC.md is up to date
2. Verify TODO.md reflects current phase
3. Add context in PROGRESS.md
4. Re-run review

## Contributing

To improve this skill:
1. Edit `.skills/spec-code-reviewer.md`
2. Test with real code changes
3. Adjust patterns based on findings
4. Document new scenarios

## Files

```
openspec/.skills/
├── README.md                 # This file
└── spec-code-reviewer.md     # Main reviewer skill
```

## Related Documentation

- [SPEC.md](../SPEC.md) - Technical specification
- [TODO.md](../TODO.md) - Implementation tasks
- [PROGRESS.md](../PROGRESS.md) - Progress tracking
- [../.agent-workspace/](../.agent-workspace/) - Design documents

---

**Version:** 1.0.0
**Last Updated:** 2026-03-09
