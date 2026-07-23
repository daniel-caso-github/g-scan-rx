from unittest.mock import MagicMock, patch

from src.infrastructure.scrubbing.null_text_scrubber import NullTextScrubber


def test_null_scrubber_returns_input_unchanged():
    scrubber = NullTextScrubber()
    assert scrubber.scrub("Juan Pérez 30mg") == "Juan Pérez 30mg"


def test_presidio_scrubber_anonymizes_detected_pii():
    mock_result = MagicMock()
    analyzer = MagicMock()
    analyzer.analyze.return_value = [mock_result]

    anonymizer = MagicMock()
    anonymizer.anonymize.return_value = MagicMock(text="<PERSON> 30mg")

    with patch("presidio_analyzer.AnalyzerEngine", return_value=analyzer), \
         patch("presidio_anonymizer.AnonymizerEngine", return_value=anonymizer):
        from src.infrastructure.scrubbing.presidio_text_scrubber import PresidioTextScrubber
        scrubber = PresidioTextScrubber()
        out = scrubber.scrub("Juan Pérez 30mg")

    assert out == "<PERSON> 30mg"


def test_presidio_scrubber_passthrough_when_no_pii():
    analyzer = MagicMock()
    analyzer.analyze.return_value = []
    with patch("presidio_analyzer.AnalyzerEngine", return_value=analyzer), \
         patch("presidio_anonymizer.AnonymizerEngine", return_value=MagicMock()):
        from src.infrastructure.scrubbing.presidio_text_scrubber import PresidioTextScrubber
        scrubber = PresidioTextScrubber()
        out = scrubber.scrub("Amoxicilina 500mg")
    assert out == "Amoxicilina 500mg"


def test_presidio_scrubber_fails_closed_on_error():
    analyzer = MagicMock()
    analyzer.analyze.side_effect = RuntimeError("nlp down")
    with patch("presidio_analyzer.AnalyzerEngine", return_value=analyzer), \
         patch("presidio_anonymizer.AnonymizerEngine", return_value=MagicMock()):
        from src.infrastructure.scrubbing.presidio_text_scrubber import PresidioTextScrubber
        scrubber = PresidioTextScrubber()
        out = scrubber.scrub("algo con PII")
    assert out == "[REDACTED]"
