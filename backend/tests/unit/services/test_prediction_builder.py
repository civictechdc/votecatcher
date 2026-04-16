"""Unit tests for PredictionBuilder.

BDD-style tests verifying the extracted prediction builder produces
identical output to both CampaignQueryService and ResultsQueryService
private methods.
"""

import uuid
from types import SimpleNamespace

from sqlmodel import Session

from app.data.database.model.match_result import ConfidenceLevel, MatchResult
from app.data.database.model.registered_voter import RegisteredVoter


def _make_voter(
    session: Session,
    first_name: str = "John",
    last_name: str = "Doe",
    street: str = "123 Main St",
    city: str = "DC",
    state: str = "DC",
    zip_code: str = "20001",
) -> RegisteredVoter:
    voter = RegisteredVoter(
        region_id=uuid.uuid4(),
        name_data={"first_name": first_name, "last_name": last_name},
        address_data={"street": street, "city": city, "state": state, "zip": zip_code},
        data_hash=f"hash-{first_name}-{last_name}",
    )
    session.add(voter)
    session.flush()
    return voter


def _stub_voter(
    name_data: dict | None = None,
    address_data: dict | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(name_data=name_data, address_data=address_data)


def _make_match_result(
    ocr_result_id: int,
    voter_id: int | None = None,
    rank: int = 1,
    similarity_score: float = 0.9,
    confidence_level: ConfidenceLevel = ConfidenceLevel.HIGH,
) -> MatchResult:
    return MatchResult(
        ocr_result_id=ocr_result_id,
        matcher_job_id=1,
        voter_id=voter_id,
        rank=rank,
        similarity_score=similarity_score,
        confidence_level=confidence_level,
    )


class TestFormatVoterName:
    """Feature: Voter name formatting.

    As the prediction builder
    I want to format voter name_data into a display string
    So that predictions show readable names.
    """

    def test_formats_first_and_last_name(self):
        """Scenario: Both first and last name present."""
        from app.services.prediction_builder import PredictionBuilder

        voter = _stub_voter(name_data={"first_name": "Jane", "last_name": "Smith"})
        result = PredictionBuilder.format_voter_name(voter)
        assert result == "Jane Smith"

    def test_formats_first_name_only(self):
        """Scenario: Only first name present."""
        from app.services.prediction_builder import PredictionBuilder

        voter = _stub_voter(name_data={"first_name": "Alice"})
        result = PredictionBuilder.format_voter_name(voter)
        assert result == "Alice"

    def test_formats_last_name_only(self):
        """Scenario: Only last name present."""
        from app.services.prediction_builder import PredictionBuilder

        voter = _stub_voter(name_data={"last_name": "Bob"})
        result = PredictionBuilder.format_voter_name(voter)
        assert result == "Bob"

    def test_returns_empty_for_empty_name_data(self):
        """Scenario: name_data is empty dict."""
        from app.services.prediction_builder import PredictionBuilder

        voter = _stub_voter(name_data={})
        result = PredictionBuilder.format_voter_name(voter)
        assert result == ""

    def test_returns_empty_for_none_name_data(self):
        """Scenario: name_data is None."""
        from app.services.prediction_builder import PredictionBuilder

        voter = _stub_voter(name_data=None)
        result = PredictionBuilder.format_voter_name(voter)
        assert result == ""


class TestFormatVoterAddress:
    """Feature: Voter address formatting.

    As the prediction builder
    I want to format voter address_data into a display string
    So that predictions show readable addresses.
    """

    def test_formats_full_address(self):
        """Scenario: All address fields present."""
        from app.services.prediction_builder import PredictionBuilder

        voter = _stub_voter(
            address_data={
                "street": "123 Main St",
                "city": "DC",
                "state": "DC",
                "zip": "20001",
            }
        )
        result = PredictionBuilder.format_voter_address(voter)
        assert result == "123 Main St, DC, DC, 20001"

    def test_formats_partial_address(self):
        """Scenario: Only street and city present."""
        from app.services.prediction_builder import PredictionBuilder

        voter = _stub_voter(
            address_data={"street": "456 Oak Ave", "city": "Springfield"}
        )
        result = PredictionBuilder.format_voter_address(voter)
        assert result == "456 Oak Ave, Springfield"

    def test_returns_empty_for_empty_address_data(self):
        """Scenario: address_data is empty dict."""
        from app.services.prediction_builder import PredictionBuilder

        voter = _stub_voter(address_data={})
        result = PredictionBuilder.format_voter_address(voter)
        assert result == ""

    def test_returns_empty_for_none_address_data(self):
        """Scenario: address_data is None."""
        from app.services.prediction_builder import PredictionBuilder

        voter = _stub_voter(address_data=None)
        result = PredictionBuilder.format_voter_address(voter)
        assert result == ""


class TestBuildPredictions:
    """Feature: Prediction building from match results.

    As the prediction builder
    I want to build voter predictions grouped by OCR result ID
    So that services can display ranked candidate voters per OCR result.
    """

    def test_empty_match_results_returns_empty_dict(self):
        """Scenario: No match results yields empty predictions."""
        from app.services.prediction_builder import PredictionBuilder

        result = PredictionBuilder.build([], {})
        assert result == {}

    def test_single_match_with_voter(self, session: Session):
        """Scenario: One match result with a voter."""
        from app.services.prediction_builder import PredictionBuilder

        voter = _make_voter(session)
        match = _make_match_result(ocr_result_id=10, voter_id=voter.id)
        session.add(match)
        session.commit()

        voters_by_id = {voter.id: voter}
        result = PredictionBuilder.build([match], voters_by_id)

        assert 10 in result
        assert len(result[10]) == 1
        pred = result[10][0]
        assert pred.rank == 1
        assert pred.voter_name == "John Doe"
        assert pred.voter_address == "123 Main St, DC, DC, 20001"
        assert pred.similarity_score == 0.9
        assert pred.confidence == "HIGH"

    def test_single_match_without_voter(self):
        """Scenario: Match result with voter_id=None yields empty name/address."""
        from app.services.prediction_builder import PredictionBuilder

        match = _make_match_result(ocr_result_id=10, voter_id=None)
        result = PredictionBuilder.build([match], {})

        assert 10 in result
        pred = result[10][0]
        assert pred.voter_name == ""
        assert pred.voter_address == ""

    def test_predictions_sorted_by_rank(self):
        """Scenario: Multiple predictions per OCR sorted by rank ascending."""
        from app.services.prediction_builder import PredictionBuilder

        matches = [
            _make_match_result(ocr_result_id=10, voter_id=None, rank=3),
            _make_match_result(ocr_result_id=10, voter_id=None, rank=1),
            _make_match_result(ocr_result_id=10, voter_id=None, rank=2),
        ]
        result = PredictionBuilder.build(matches, {})

        assert len(result[10]) == 3
        assert result[10][0].rank == 1
        assert result[10][1].rank == 2
        assert result[10][2].rank == 3

    def test_groups_by_ocr_result_id(self, session: Session):
        """Scenario: Multiple OCR results each get their own prediction list."""
        from app.services.prediction_builder import PredictionBuilder

        voter1 = _make_voter(session, first_name="Alice", last_name="A")
        voter2 = _make_voter(session, first_name="Bob", last_name="B")
        matches = [
            _make_match_result(ocr_result_id=10, voter_id=voter1.id),
            _make_match_result(ocr_result_id=20, voter_id=voter2.id),
        ]

        voters_by_id = {voter1.id: voter1, voter2.id: voter2}
        result = PredictionBuilder.build(matches, voters_by_id)

        assert 10 in result
        assert 20 in result
        assert result[10][0].voter_name == "Alice A"
        assert result[20][0].voter_name == "Bob B"

    def test_confidence_level_serialized_as_string(self):
        """Scenario: ConfidenceLevel enum serialized to uppercase string."""
        from app.services.prediction_builder import PredictionBuilder

        match = _make_match_result(
            ocr_result_id=10, confidence_level=ConfidenceLevel.MEDIUM
        )
        result = PredictionBuilder.build([match], {})

        assert result[10][0].confidence == "MEDIUM"


class TestPredictionBuilderParity:
    """Feature: PredictionBuilder matches existing service output.

    As a developer
    I want PredictionBuilder to produce identical output to both services
    So that the extraction is a true refactor with no behavioral change.
    """

    def test_parity_with_campaign_service(self, session: Session):
        """Scenario: PredictionBuilder output matches CampaignQueryService private method."""
        from app.services.campaign_query_service import CampaignQueryService
        from app.services.prediction_builder import PredictionBuilder

        voter = _make_voter(session)
        match = _make_match_result(ocr_result_id=10, voter_id=voter.id)
        session.add(match)
        session.commit()

        voters_by_id = {voter.id: voter}

        builder_result = PredictionBuilder.build([match], voters_by_id)

        campaign_service = CampaignQueryService(session)
        campaign_result = campaign_service._build_campaign_predictions([match])

        assert len(builder_result) == len(campaign_result)
        assert len(builder_result[10]) == len(campaign_result[10])

        bp = builder_result[10][0]
        cp = campaign_result[10][0]

        assert bp.rank == cp.rank
        assert bp.voter_name == cp.voter_name
        assert bp.voter_address == cp.voter_address
        assert bp.similarity_score == cp.similarity_score
        assert bp.confidence == cp.confidence

    def test_parity_with_results_service(self, session: Session):
        """Scenario: PredictionBuilder output matches ResultsQueryService private method."""
        from app.services.prediction_builder import PredictionBuilder
        from app.services.results_query_service import ResultsQueryService

        voter = _make_voter(session)
        match = _make_match_result(ocr_result_id=10, voter_id=voter.id)
        session.add(match)
        session.commit()

        voters_by_id = {voter.id: voter}

        builder_result = PredictionBuilder.build([match], voters_by_id)

        results_service = ResultsQueryService(session)
        results_result = results_service._build_predictions_from_match_results([match])

        assert len(builder_result) == len(results_result)
        assert len(builder_result[10]) == len(results_result[10])

        bp = builder_result[10][0]
        rp = results_result[10][0]

        assert bp.rank == rp.rank
        assert bp.voter_name == rp.voter_name
        assert bp.voter_address == rp.voter_address
        assert bp.similarity_score == rp.similarity_score
        assert bp.confidence == rp.confidence
