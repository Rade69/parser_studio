# Domain: evidence package.
# Eksportuje: Locator, Evidence, DocumentEvidence, Candidate, ExtractionContext, cell_to_evidence.
# Ne zna za: SQLite, PySide6, Docling, openpyxl, contract.
"""Evidence domain value objects.

Pet immutable value objects prema V3 sekcija 8:
- Locator: gdje u izvornom dokumentu se nalazi vrijednost
- Evidence: nesto sto je stvarno vidjeno u dokumentu
- DocumentEvidence: standardizovan document model
- Candidate: prijedlog vrijednosti od strane extractora ili AI advisor
- ExtractionContext: state za resolver/producer

Plus compatibility adapter cell_to_evidence za legacy Cell iz core/.
"""
from .candidate import Candidate
from .cell_compat import cell_to_evidence
from .document_evidence import DocumentEvidence
from .evidence import Evidence
from .extraction_context import ExtractionContext
from .locator import Locator

__all__ = [
    "Candidate",
    "DocumentEvidence",
    "Evidence",
    "ExtractionContext",
    "Locator",
    "cell_to_evidence",
]
