# Domain: concepts.
# Posjeduje: Concept dataclass, ConceptLibrary aggregate.
# Ne zna za: SQLite, PySide6, Docling, openpyxl, contract, adapters, presentation.
"""Concept library — sinonimi i kontekstualne fraze za 20 ciljnih polja (V3_2 C1).

Biblioteka sadrzi:
- Concept: jedan koncept sa sinonimima i kontekstualnim frazama za jedno polje/jezik
- ConceptLibrary: agregat koncepata za SVA 20 polja, multi-language

Lookup:
- library.get(field, language) -> Concept | None
- library.match_alias(normalized_text) -> (field, language) | None  (za Producer match)
"""
from .concept import Concept
from .concept_library import ConceptLibrary

__all__ = ["Concept", "ConceptLibrary"]
