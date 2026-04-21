from app.observability.event_validation import validate_event_schema


class TestValidateEventSchema:
    def test_passes_unknown_events_through(self):
        event_dict = {"event": "something_else", "foo": "bar"}
        result = validate_event_schema(None, "info", event_dict)
        assert result == event_dict

    def test_passes_valid_ocr_call(self, capsys):
        event_dict = {
            "event": "ocr_api_call",
            "gen_ai_system": "openai",
            "gen_ai_request_model": "gpt-4o",
            "latency_ms": 100.0,
        }
        result = validate_event_schema(None, "info", event_dict)
        assert result == event_dict
        captured = capsys.readouterr()
        assert "unknown fields" not in captured.err

    def test_warns_on_unknown_ocr_fields(self, capsys):
        event_dict = {
            "event": "ocr_api_call",
            "gen_ai_system": "openai",
            "latency_ms": 100.0,
            "unexpected_field": "oops",
        }
        validate_event_schema(None, "info", event_dict)
        captured = capsys.readouterr()
        assert "unexpected_field" in captured.err
        assert "ocr_api_call" in captured.err

    def test_warns_on_unknown_slow_query_fields(self, capsys):
        event_dict = {
            "event": "slow_query",
            "statement": "SELECT 1",
            "duration_ms": 600.0,
            "threshold_ms": 500.0,
            "bogus": True,
        }
        validate_event_schema(None, "warning", event_dict)
        captured = capsys.readouterr()
        assert "bogus" in captured.err

    def test_ignores_structlog_meta_fields(self, capsys):
        event_dict = {
            "event": "ocr_api_call",
            "gen_ai_system": "openai",
            "latency_ms": 100.0,
            "timestamp": "2026-04-21T00:00:00",
            "level": "info",
            "request_id": "abc123",
        }
        validate_event_schema(None, "info", event_dict)
        captured = capsys.readouterr()
        assert "unknown fields" not in captured.err

    def test_passes_events_without_event_key(self):
        event_dict = {"foo": "bar"}
        result = validate_event_schema(None, "info", event_dict)
        assert result == event_dict
