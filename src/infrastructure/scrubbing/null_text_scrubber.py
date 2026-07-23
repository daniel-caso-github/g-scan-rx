from src.domain.ports.text_scrubber import TextScrubber


class NullTextScrubber(TextScrubber):
    """No-op scrubber. Used when presidio is unavailable (dev / offline)."""

    def scrub(self, text: str) -> str:
        return text
