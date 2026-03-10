# Quick Start: Spec-Aware Code Reviewer

⚠️ **EXPLICIT INVOCATION ONLY** - This skill will NOT auto-trigger. You must explicitly load it.

## What This Does

Automatically reviews your code against SPEC.md requirements and generates actionable feedback in COMMENTS.md format.

## How to Load (Required)

This skill is **intentionally hidden** from `npx openskills list` to prevent auto-triggering.

```bash
# Option 1: Direct file read
cat openspec/.skills/spec-code-reviewer.md

# Option 2: Tell your agent
# "Read openspec/.skills/spec-code-reviewer.md and follow its instructions"
```

**Verification:**
```bash
# Should NOT appear here (by design):
npx openskills list | grep spec-code-reviewer
# (No output = correct)
```

### 1. Make Code Changes

```bash
# Implement your feature following SPEC.md
# Write tests following TDD (SPEC.md §7.2)
```

### 2. Run the Review

The skill is already loaded from Step 0. The agent now has the spec-code-reviewer context and will:
- Load SPEC.md requirements
- Check TODO.md for current phase
- Review PROGRESS.md for context
- Analyze your code changes
- Generate COMMENTS.md

No additional command needed - just tell the agent to review.

### 3. Fix Issues

```bash
# Read COMMENTS.md
cat openspec/COMMENTS.md

# Focus on 🔴 BLOCKING issues first
# Then address 🟡 IMPORTANT issues
# Re-run review after fixes
```

## Example Workflow

### Scenario: Completing Phase 2 FileService

```bash
# 1. Implement FileService
vim backend/app/files/file_service.py

# 2. Write tests
vim backend/tests/unit/services/test_file_service.py

# 3. Run tests
cd backend
uv run pytest tests/unit/services/test_file_service.py -v
# Result: 4/10 passing (some failing)

# 4. Review against SPEC
cd /Users/kurian/01 - Projects/votecatcher
npx openskills read spec-code-reviewer

# 5. Read feedback
cat openspec/COMMENTS.md
# Output shows:
# 🔴 BLOCKING: Test attribute names wrong (file_name vs original_filename)
# 🔴 BLOCKING: Async mock setup incorrect
# 🟡 IMPORTANT: Missing RFC 7807 error format

# 6. Fix blockers
# Update test attributes
# Fix async mocks

# 7. Re-run tests
uv run pytest tests/unit/services/test_file_service.py -v
# Result: 10/10 passing ✅

# 8. Re-review
npx openskills read spec-code-reviewer
# Output shows:
# ✅ APPROVED TO PROCEED - All exit criteria met

# 9. Mark task complete in TODO.md
# Move to next task
```

## What Gets Checked

### ✅ Requirements Traceability
- Does code implement what SPEC.md requires?
- Are all Phase X tasks from TODO.md addressed?
- Any missing features?

### ✅ Phase Gate Compliance
- Exit criteria met? (from SPEC.md §7.3)
- Entry criteria for next phase satisfied?
- Can we proceed?

### ✅ Code Quality
- Follows SPEC.md architecture patterns?
- TDD methodology followed?
- Test coverage >85%?

### ✅ Technical Decisions
- Aligns with SPEC.md §8?
- New decisions documented in ADRs?
- Alternatives considered?

## Output Format

### COMMENTS.md Structure

```markdown
# Code Review: [Description]

## Executive Summary
[2-3 sentences, overall assessment]

## Requirements Traceability
[Table: ✅ Implemented | ⚠️ Partial | ❌ Missing]

## Critical Issues
🔴 BLOCKING: [Must fix before proceeding]

## Important Issues
🟡 IMPORTANT: [Should fix, not blocking]

## Phase Gate Assessment
✅/🔴 Can/Cannot Proceed

## Action Items
[ ] Critical items (before sign-off)
[ ] Important items (soon)
[ ] Technical debt
```

## Severity Levels

### 🔴 BLOCKING
- Missing critical feature from SPEC
- Exit criteria not met
- Architecture violation
- Security vulnerability
- **Action:** Must fix before proceeding

### 🟡 IMPORTANT
- Incomplete implementation
- Missing edge cases
- Test coverage below target
- Performance concern
- **Action:** Should fix soon, can proceed with caution

### 🟢 ENHANCEMENT
- Code could be cleaner
- Better error messages
- Documentation gaps
- **Action:** Nice to have, not urgent

## Integration Tips

### With Development Workflow

```bash
# Pre-commit hook
.git/hooks/pre-commit
  npx openskills read spec-code-reviewer
  if grep -q "🔴 CANNOT PROCEED" openspec/COMMENTS.md; then
    echo "Fix blocking issues first"
    exit 1
  fi

# CI/CD pipeline
.github/workflows/review.yml
  - name: Spec Compliance
    run: |
      npx openskills read spec-code-reviewer
      # Fail if blockers found
```

### With Agent Skills

```bash
# Combine with code review excellence
npx openskills read spec-code-reviewer,code-review-excellence

# Add security focus
npx openskills read spec-code-reviewer,security-best-practices

# Debug issues found
npx openskills read spec-code-reviewer,systematic-debugging
```

## Common Patterns

### Pattern 1: Phase Completion Review

```bash
# When you think a phase is done
1. Run exit criteria commands (from TODO.md)
2. npx openskills read spec-code-reviewer
3. Check COMMENTS.md
4. Fix blockers
5. Re-review
6. Mark phase complete in TODO.md
```

### Pattern 2: Feature Implementation Review

```bash
# After implementing a feature
1. Map feature to SPEC.md section
2. npx openskills read spec-code-reviewer
3. Verify architecture fit
4. Check test coverage
5. Assess phase impact
```

### Pattern 3: Bug Fix Review

```bash
# After fixing a bug
1. npx openskills read spec-code-reviewer
2. Check no spec deviation introduced
3. Verify tests added
4. Update PROGRESS.md
```

## Troubleshooting

### Skill Not Loading?

```bash
# Check openskills installed
npm list -g openskills

# Install if needed
npm install -g openskills
```

### COMMENTS.md Not Generated?

Required files:
- ✅ `openspec/SPEC.md` exists
- ✅ `openspec/TODO.md` exists
- ✅ Code changes to review

### False Positives?

1. Check SPEC.md is current
2. Verify TODO.md reflects phase
3. Add context in PROGRESS.md
4. Re-run review

## Tips for Best Results

1. **Keep SPEC.md Updated**
   - Document architecture decisions
   - Update as requirements change
   - Reference in COMMENTS.md

2. **Use TODO.md Actively**
   - Mark tasks in progress
   - Update status regularly
   - Reference current phase

3. **Log in PROGRESS.md**
   - Document decisions made
   - Note blockers encountered
   - Track technical debt

4. **Review COMMENTS.md Thoroughly**
   - Focus on blockers first
   - Understand the "why"
   - Ask questions if unclear

5. **Re-Review After Fixes**
   - Don't assume fixes are correct
   - Verify tests pass
   - Confirm spec compliance

## Example Commands

```bash
# Review specific files
npx openskills read spec-code-reviewer --files backend/app/files/

# Review with context
npx openskills read spec-code-reviewer --phase 2

# Generate review for PR
npx openskills read spec-code-reviewer --pr 42
```

## Support

- **Issues:** Check EXAMPLE-COMMENTS.md for sample output
- **Questions:** Review SPEC.md §7.3 for phase gates
- **Improvements:** Edit `.skills/spec-code-reviewer.md`

---

**Remember:** This reviewer ensures your code matches the specification. Trust the feedback, reference SPEC.md, and fix blockers before proceeding.
