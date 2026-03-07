# Simulation Testing Guide

This guide explains how to use simulation mode for testing and development of VoteCatcher.
## What is Simulation Mode?
Simulation mode bypasses real OCR processing and returns realistic mock data. This enables:
- Testing without OCR API credentials
- Testing without file uploads
- Fast iteration during development
- Reliable test data for E2E tests
## When to Use Simulation
### Development
- Testing UI components that depend on match results
- Debugging pagination and table display
- Developing new features that interact with match data
- Performance testing with large datasets
### Testing
- E2E tests that verify results table rendering
- Integration tests for pagination controls
- Regression tests for match result display
### Demos
- Stakeholder demonstrations without real data
- Quick prototypes of new features
- Training scenarios
## How to Enable Simulation
### Frontend UI
1. Navigate to `/workspace/demo`
2. Find the "Use Simulated Data" checkbox in the results section
3. Check the box to enable simulation
4. The checkbox state persists in localStorage
### Backend API
Call the endpoint directly:
```bash
curl http://localhost:8080/workspace/ocr/simulate/{task_id}
```
The task_id can be any string - it same ID returns consistent results.
Example:
```bash
curl http://localhost:8080/workspace/ocr/simulate/test-123
```
## Simulated Data Structure
### Response Format
```json
{
  "results": {
    "column_data": [
      {"name": "ocr_name", "position_idx": 0, "data_type": "string"},
      {"name": "ocr_address", "position_idx": 1, "data_type": "string"},
      {"name": "matched_name", "position_idx": 2, "data_type": "string"},
      {"name": "matched_address", "position_idx": 3, "data_type": "string"},
      {"name": "match_score", "position_idx": 4, "data_type": "float"},
      {"name": "ocr_date", "position_idx": 5, "data_type": "string"},
      {"name": "ocr_ward", "position_idx": 6, "data_type": "int"}
    ],
    "result_data": [
      {
        "row_idx": 0,
        "values": [
          {"value": "John Smith", "column_idx": 0, "data_type": "string"},
          {"value": "123 Main St", "column_idx": 1, "data_type": "string"},
          ...
        ]
      }
    ]
  }
}
```
### Column Definitions
| Column | Type | Description |
|--------|------|-------------|
| ocr_name | string | Name extracted from petition |
| ocr_address | string | Address extracted from petition |
| matched_name | string | Matched voter registration name |
| matched_address | string | Matched voter registration address |
| match_score | float | Match confidence (0.5-1.0) |
| ocr_date | string | Date from petition |
| ocr_ward | int | Ward number from petition |
### Data Characteristics
- **Row count**: 50-200 rows per request
- **Match score**: Random between 0.5 and 1.0
- **Match rate**: ~70% of rows have high-confidence matches
- **Deterministic**: Same task_id always returns same results (seeded)
## Testing Patterns
### Pattern 1: Basic Simulation Test
```typescript
test('simulation returns expected columns', async ({ page }) => {
  await page.goto('/workspace/demo');
  await page.check('#simulation-checkbox');
  await expect(page.locator('#results-table')).toBeVisible();
});
```
### Pattern 2: Pagination Test
```typescript
test('simulation results pagination works', async ({ page }) => {
  await page.goto('/workspace/demo');
  // Enable simulation
  await page.check('#simulation-checkbox');
  // Trigger matching
  await page.click('#run-matching');
  // Wait for results
  await expect(page.locator('.pagination-info')).toBeVisible();
  // Test pagination
  const nextButton = page.locator('button:has-text("Next")');
  if (await nextButton.isEnabled()) {
    await nextButton.click();
    await expect(page.locator('.page-2')).toBeVisible();
  }
});
```
### Pattern 3: Direct API Test
```typescript
test('simulation API returns valid data', async ({ request }) => {
  const response = await request.get('/workspace/ocr/simulate/test-123');
  expect(response.status()).toBe(200);
  
  const data = await response.json();
  expect(data.results.column_data).toHaveLength(7);
  expect(data.results.result_data.length).toBeGreaterThan(50);
});
```
## Troubleshooting
### Simulation Toggle Not Working
**Symptom**: Checkbox doesn't enable simulation
**Solutions**:
1. Check localStorage for `featureFlags_overrides` key
2. Verify feature flags store initialized in `+layout.svelte`
3. Check browser console for errors
### No Results Appear
**Symptom**: Results table shows "No matches yet"
**Solutions**:
1. Verify simulation mode is enabled (checkbox checked)
2. Check that files were uploaded (required for UI flow)
3. Wait longer for async operation (up to 10 seconds)
4. Check backend logs for errors
### Pagination Not Working
**Symptom**: All results on one page or pagination missing
**Solutions**:
1. Check total result count (< 25 results won't paginate)
2. Verify Pagination component is rendered
3. Check pageSize and currentPage state
### API Errors
**Symptom**: 404 or 500 errors from simulation endpoint
**Solutions**:
1. Verify backend is running on port 8080
2. Check workspace routing is configured
3. Ensure CORS is properly configured
## API Reference
### GET /workspace/ocr/simulate/{task_id}
Generate simulated OCR match results.
**Parameters**:
- `task_id` (path): Any string - used to seed random data
**Response**:
```json
{
  "results": {
    "column_data": [...],
    "result_data": [...]
  }
}
```
**Status Codes**:
- `200`: Success
- `500`: Server error
## Related Documentation
- [Running Locally](./running-locally.md) - Full setup instructions
- [Feature Flags](./running-locally.md#feature-flags) - Feature flag configuration
- [E2E Testing](./running-locally.md#e2e-testing-with-simulation-mode) - E2E test details
