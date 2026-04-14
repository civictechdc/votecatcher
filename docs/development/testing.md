# Testing Guide

## Approval Testing

### When to Use Approval Tests

| Scenario | Use Approval Test | Use Assertion Test |
|----------|-------------------|--------------------|
| Template rendering with many variants | Yes | No |
| Score matrices / regression baselines | Yes | No |
| Single behavior with clear expected value | No | Yes |
| Domain value object validation | No | Yes |
| Config/spec snapshot validation | Yes | No |

### How Approval Tests Work

Approval tests compare output against a golden master (`.approved.txt` file). On first run, a `.received.txt` file is generated. You inspect it, and if correct, rename it to `.approved.txt` to "approve" it.

### Workflow

1. Write the approval test using `verify()` or `verify_all()`
2. Run the test — it fails and creates a `.received.txt` file
3. Inspect the received file content
4. If correct: `mv -f path.received.txt path.approved.txt`
5. Run the test again — it passes
6. Commit the `.approved.txt` file alongside the test

### Running Approval Tests

```bash
uv run pytest tests/unit/domain/test_template_renderer_approval.py -v
```

### Approved File Locations

Approved files live in the same directory as the test file, committed to git.

### Re-approving After Intentional Changes

If you intentionally change `render_template` behavior:

1. Run the test — it fails and creates a new `.received.txt`
2. Inspect the diff between `.approved.txt` and `.received.txt`
3. If the change is intentional: `mv -f path.received.txt path.approved.txt`
4. Commit both the code change and the updated `.approved.txt`
