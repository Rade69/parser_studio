"""Parser Studio composition root.

Wiring između use case-ova, portova i adaptera.

Ovo je skelet kreiran u A1 (src/parser_studio/ package layout).
Popunjava se u A5 (application use cases) kada se uvedu ImportDocument,
AnalyzeInvoice, ReviewInvoice, ConfirmInvoice i ostali use case-ovi.

Ne zna za infrastrukturu (SQLite, Docling, PySide6, AI provider).
Ne sadrži business logiku — samo dependency injection.
"""