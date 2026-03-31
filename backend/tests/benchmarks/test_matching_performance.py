import pytest
from rapidfuzz import fuzz


class TestMatchingPerformance:
	@pytest.mark.benchmark(group="fuzzy-match")
	def test_fuzzy_match_ratio_performance(self, benchmark):
		test_pairs = [
			("John Smith", "Jon Smit"),
			("123 Main St", "123 Main Street"),
			("Robert Johnson", "Rob Johnston"),
			("Oak Avenue", "Oak Ave"),
		]

		def run_matches():
			return [fuzz.ratio(a, b) for a, b in test_pairs * 100]

		result = benchmark(run_matches)
		assert len(result) == 400

	@pytest.mark.benchmark(group="fuzzy-match")
	def test_fuzzy_match_partial_ratio_performance(self, benchmark):
		test_pairs = [
			("John Smith", "Jon Smit"),
			("123 Main St", "123 Main Street"),
			("Robert Johnson", "Rob Johnston"),
			("Oak Avenue", "Oak Ave"),
		]

		def run_matches():
			return [fuzz.partial_ratio(a, b) for a, b in test_pairs * 100]

		result = benchmark(run_matches)
		assert len(result) == 400
