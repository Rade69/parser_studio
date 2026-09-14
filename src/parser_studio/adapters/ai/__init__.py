# Adapters: ai.
# Posjeduje: NullAdvisor (OFF rezim).
# Zna za: parser_studio.domain.evidence, parser_studio.ports.advisor.
# Ne zna za: openai/anthropic/httpx/dokling (OFF rezim nema eksternih poziva).
"""AI adapters — implementacije Advisor porta.

Trenutno sadrzi samo NullAdvisor (OFF rezim). HttpVisionAdvisor
(provider iza transport apstrakcije) dolazi u G3.
"""
from .null_advisor import NullAdvisor

__all__ = ["NullAdvisor"]
