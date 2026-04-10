"""BDD tests for detect-secrets compliance in test fixtures.

Ensures test files use safe URL/API key patterns that don't trigger
detect-secrets false positives, keeping the pre-commit hook clean.

Behavioral spec:
  Given test files with database URLs and API key fixtures
  When detect-secrets scans those files
  Then no secrets are detected (all are false-positive-free patterns)

Categories of false positives addressed:
  - Basic Auth Credentials: user:pass@host patterns in database URLs
  - Secret Keyword: api_key assignment style patterns in test fixtures
  - Hex High Entropy String: UUIDs or hashes that cross entropy threshold
"""

import json
import subprocess
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent

TEST_FILES_WITH_CREDENTIALS = [
    "tests/unit/settings/test_providers.py",
    "tests/unit/test_dead_code_cleanup.py",
    "tests/integration/database/test_models.py",
    "tests/integration/api/test_providers.py",
    "tests/unit/ocr/test_ocr_client_factory.py",
    "tests/unit/ocr/clients/test_gemini_client.py",
    "tests/unit/ocr/clients/test_mistral_client.py",
    "tests/unit/ocr/clients/test_openai_client.py",
    "tests/unit/utils/test_uuid_utils.py",
    "tests/unit/models/test_registered_voter_tracking.py",
]


@pytest.fixture
def scan_results():
    """Run detect-secrets on all test files with credentials and return results."""
    results = {}
    for relpath in TEST_FILES_WITH_CREDENTIALS:
        proc = subprocess.run(
            ["detect-secrets", "scan", relpath],
            capture_output=True,
            text=True,
            cwd=str(BACKEND_DIR),
        )
        if proc.returncode != 0:
            pytest.skip(f"detect-secrets not available: {proc.stderr}")
        scan = json.loads(proc.stdout)
        all_findings = list(scan.get("results", {}).values())
        findings = all_findings[0] if all_findings else []
        results[relpath] = findings
    return results


class TestDetectSecretsCompliance:
    """BDD: Test fixtures must not trigger detect-secrets."""

    def test_no_basic_auth_in_test_urls(self, scan_results):
        """Given test files with database URLs
        When detect-secrets scans them
        Then no 'Basic Auth Credentials' findings exist.

        Use URL construction or scheme-only patterns instead of
        literal user:pass@host strings.
        """
        for filepath, findings in scan_results.items():
            basic_auth = [f for f in findings if f["type"] == "Basic Auth Credentials"]
            assert basic_auth == [], (
                f"{filepath} has Basic Auth false positive on line(s) "
                f"{', '.join(str(f['line_number']) for f in basic_auth)}. "
                f"Use URL construction instead of literal user:pass@host."
            )

    def test_no_secret_keyword_in_test_fixtures(self, scan_results):
        """Given test files with API key fixtures
        When detect-secrets scans them
        Then no 'Secret Keyword' findings exist.

        Use clearly-fake placeholder values like "test-placeholder"
        or construct values via string concatenation.
        """
        for filepath, findings in scan_results.items():
            keywords = [f for f in findings if f["type"] == "Secret Keyword"]
            assert keywords == [], (
                f"{filepath} has Secret Keyword false positive on line(s) "
                f"{', '.join(str(f['line_number']) for f in keywords)}. "
                f"Use clearly-fake placeholder values for API keys."
            )

    def test_no_hex_high_entropy_in_test_data(self, scan_results):
        """Given test files with hex data (UUIDs, hashes)
        When detect-secrets scans them
        Then no 'Hex High Entropy String' findings exist.

        Use lower-entropy test data or construct values dynamically.
        """
        for filepath, findings in scan_results.items():
            hex_findings = [
                f for f in findings if f["type"] == "Hex High Entropy String"
            ]
            assert hex_findings == [], (
                f"{filepath} has Hex High Entropy false positive on line(s) "
                f"{', '.join(str(f['line_number']) for f in hex_findings)}. "
                f"Use lower-entropy test data or string construction."
            )

    def test_all_flagged_files_are_clean(self, scan_results):
        """Given all previously-flagged test files
        When detect-secrets scans them
        Then zero total findings exist across all files.

        This is the comprehensive gate that ensures the pre-commit
        hook will pass for all test fixture files without needing
        baseline allowlist entries.
        """
        total = sum(len(findings) for findings in scan_results.values())
        if total > 0:
            details = []
            for filepath, findings in scan_results.items():
                for f in findings:
                    details.append(f"  {filepath}:{f['line_number']} ({f['type']})")
            pytest.fail(
                f"Found {total} detect-secrets findings in test files:\n"
                + "\n".join(details)
            )
