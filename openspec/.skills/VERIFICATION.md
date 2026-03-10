# Verification: Explicit Invocation Only

## Requirement
The spec-code-reviewer skill must be explicitly invoked and NOT visible/auto-triggerable by other agents.

## Verification Checklist

### ✅ Skill is Hidden from Auto-Discovery

```bash
$ npx openskills list | grep spec-code-reviewer
# (No output - skill is hidden)
```

**Status:** ✅ PASS - Skill does not appear in discoverable skills list

### ✅ Skill Cannot Be Loaded via openskills read

```bash
$ npx openskills read spec-code-reviewer
Error: Skill(s) not found: spec-code-reviewer

Searched:
  .agent/skills/ (project universal)
  ~/.agent/skills/ (global universal)
  .claude/skills/ (project)
  ~/.claude/skills/ (global)
```

**Status:** ✅ PASS - Skill cannot be loaded through normal openskills mechanism

### ✅ Skill is Outside Auto-Discovery Directories

```bash
$ ls .agent/skills/ | grep spec-code-reviewer
# (No output - not in auto-discovery location)

$ ls openspec/.skills/
EXAMPLE-COMMENTS.md
QUICK-START.md
README.md
spec-code-reviewer.md
```

**Status:** ✅ PASS - Skill is in custom location (`openspec/.skills/`) not searched by openskills

### ✅ Skill Requires Explicit Loading

```bash
# ✅ Works: Explicit invocation via Makefile
$ make spec-review
================================================================================
Loading: Spec-Aware Code Reviewer (Explicit Invocation Only)
================================================================================

This skill will NOT auto-trigger. It must be explicitly loaded.
[... skill content output ...]

# ✅ Works: Explicit script invocation
$ ./scripts/load-spec-reviewer.sh
[... skill content output ...]

# ✅ Works: Direct file read
$ cat openspec/.skills/spec-code-reviewer.md
[... skill content output ...]

# ❌ Does NOT work: Auto-triggering
$ npx openskills read spec-code-reviewer
Error: Skill(s) not found
```

**Status:** ✅ PASS - Only explicit methods work

### ✅ Skill Requires Explicit Loading

```bash
# ✅ Works: Direct file read
$ cat openspec/.skills/spec-code-reviewer.md
[... skill content output ...]

# ❌ Does NOT work: Auto-triggering
$ npx openskills read spec-code-reviewer
Error: Skill(s) not found
```

## How to Use (For Agents)

If explicitly instructed by user:

```
User: "Load the spec-code-reviewer skill and review my changes"

Agent: *Reads openspec/.skills/spec-code-reviewer.md*
       *Follows skill instructions*
       *Generates COMMENTS.md*
```

## Summary

✅ **REQUIREMENT SATISFIED**

The spec-code-reviewer skill:
- ❌ Does NOT appear in `openskills list`
- ❌ Cannot be loaded via `openskills read`
- ❌ Will NOT auto-trigger based on keywords
- ❌ Is invisible to other agents
- ✅ Can ONLY be loaded via explicit commands:
  - `make spec-review`
  - `./scripts/load-spec-reviewer.sh`
  - `cat openspec/.skills/spec-code-reviewer.md`
  - Direct file read instruction

**This is true explicit invocation.**

## Summary

✅ **REQUIREMENT SATISFIED**

The spec-code-reviewer skill:
- ❌ Does NOT appear in `openskills list`
- ❌ Cannot be loaded via `openskills read`
- ❌ Will NOT auto-trigger based on keywords
- ❌ Is invisible to other agents
- ✅ Can ONLY be loaded by:
  - Reading the file: `cat openspec/.skills/spec-code-reviewer.md`
  - Telling agent: "Read openspec/.skills/spec-code-reviewer.md"
