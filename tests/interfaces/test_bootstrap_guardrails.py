from unittest.mock import patch

import pytest

from src.interfaces.api.bootstrap import (
    GUARDRAIL_DEGRADED,
    Bootstrap,
    GuardrailBootstrapError,
)


def test_pii_guardrail_degraded_when_presidio_missing():
    with patch(
        "src.infrastructure.guardrails.pii_guardrail.PiiGuardrail",
        side_effect=ImportError("no presidio"),
    ), patch("src.interfaces.api.bootstrap.settings") as s:
        s.guardrails_required = False
        guardrail, status = Bootstrap._build_pii_guardrail()
    assert status == GUARDRAIL_DEGRADED


def test_injection_guardrail_degraded_when_llmguard_missing():
    with patch(
        "src.infrastructure.guardrails.injection_guardrail.InjectionGuardrail",
        side_effect=ImportError("no llm-guard"),
    ), patch("src.interfaces.api.bootstrap.settings") as s:
        s.guardrails_required = False
        guardrail, status = Bootstrap._build_injection_guardrail()
    assert status == GUARDRAIL_DEGRADED


def test_pii_guardrail_fail_closed_aborts_when_required():
    with patch(
        "src.infrastructure.guardrails.pii_guardrail.PiiGuardrail",
        side_effect=ImportError("no presidio"),
    ), patch("src.interfaces.api.bootstrap.settings") as s:
        s.guardrails_required = True
        with pytest.raises(GuardrailBootstrapError):
            Bootstrap._build_pii_guardrail()


def test_injection_guardrail_fail_closed_aborts_when_required():
    with patch(
        "src.infrastructure.guardrails.injection_guardrail.InjectionGuardrail",
        side_effect=ImportError("no llm-guard"),
    ), patch("src.interfaces.api.bootstrap.settings") as s:
        s.guardrails_required = True
        with pytest.raises(GuardrailBootstrapError):
            Bootstrap._build_injection_guardrail()


def test_scrubber_falls_back_to_null_when_presidio_missing():
    from src.infrastructure.scrubbing.null_text_scrubber import NullTextScrubber

    with patch(
        "src.infrastructure.scrubbing.presidio_text_scrubber.PresidioTextScrubber",
        side_effect=ImportError("no presidio"),
    ):
        scrubber = Bootstrap._build_scrubber()
    assert isinstance(scrubber, NullTextScrubber)
