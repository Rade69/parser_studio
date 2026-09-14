# Domain: concepts/concept_library.
# Posjeduje: ConceptLibrary aggregate (20 polja × 4 jezika).
# Ne zna za: SQLite, PySide6, Docling, openpyxl, contract, adapters.
"""ConceptLibrary — agregat koncepata za SVA 20 ciljnih polja (V3_2 C1).

Sadrzi sinonime i kontekstualne fraze u 4 jezika:
- bs (bosanski)
- hr (hrvatski)
- sr (srpski)
- en (engleski)

Lookup API:
- get(field, language) -> Concept | None
- match_alias(normalized_text) -> tuple[str, str] | None  # (field, language)
- all_fields() -> tuple[str, ...]
"""
from __future__ import annotations

from .concept import Concept, _normalize_for_match

# Svaki concept: (field, language, synonyms_tuple, context_phrases_tuple)
# Sinonimi iz prakse BHS faktura + engleski termini.
_CONCEPTS_DATA: tuple[tuple[str, str, tuple[str, ...], tuple[str, ...]], ...] = (
    # 9 invoice polja
    (
        "invoice_number", "bs",
        ("Broj fakture", "Broj računa", "Faktura br.", "Inv. br."),
        ("broj fakture",),
    ),
    (
        "invoice_number", "hr",
        ("Broj računa", "Broj fakture", "Račun br.", "Faktura br."),
        ("broj računa",),
    ),
    (
        "invoice_number", "sr",
        ("Broj fakture", "Broj računa", "Faktura br.", "Inv. br."),
        ("broj fakture",),
    ),
    (
        "invoice_number", "en",
        ("Invoice No", "Invoice Number", "Invoice #", "Inv. No"),
        ("invoice number",),
    ),
    (
        "invoice_date", "bs",
        ("Datum fakture", "Datum računa", "Datum izdavanja"),
        ("datum fakture",),
    ),
    (
        "invoice_date", "hr",
        ("Datum računa", "Datum fakture", "Datum izdavanja"),
        ("datum računa",),
    ),
    (
        "invoice_date", "sr",
        ("Datum fakture", "Datum računa", "Datum izdavanja"),
        ("datum fakture",),
    ),
    (
        "invoice_date", "en",
        ("Invoice Date", "Date", "Issue Date"),
        ("date",),
    ),
    (
        "currency", "bs",
        ("Valuta", "Currency", "Oznaka valute"),
        (),
    ),
    (
        "currency", "hr",
        ("Valuta", "Currency", "Oznaka valute"),
        (),
    ),
    (
        "currency", "sr",
        ("Valuta", "Valuta oznaka", "Currency"),
        (),
    ),
    (
        "currency", "en",
        ("Currency", "Curr.", "Currency Code"),
        ("currency",),
    ),
    (
        "seller_name", "bs",
        ("Prodavac", "Prodavač", "Isporučilac", "Seller"),
        ("prodavac",),
    ),
    (
        "seller_name", "hr",
        ("Prodavatelj", "Isporučitelj", "Seller"),
        ("prodavatelj",),
    ),
    (
        "seller_name", "sr",
        ("Prodavac", "Isporučilac", "Prodaja"),
        ("prodavac",),
    ),
    (
        "seller_name", "en",
        ("Seller", "Supplier", "Vendor"),
        ("seller", "supplier"),
    ),
    (
        "seller_tax_id", "bs",
        ("PIB prodavca", "JIB prodavca", "Tax ID prodavca", "PDV broj"),
        ("pib",),
    ),
    (
        "seller_tax_id", "hr",
        ("OIB prodavatelja", "Tax ID prodavatelja", "PDV broj"),
        ("oib",),
    ),
    (
        "seller_tax_id", "sr",
        ("PIB prodavca", "JIB prodavca", "PDV broj"),
        ("pib",),
    ),
    (
        "seller_tax_id", "en",
        ("Seller Tax ID", "VAT Number", "Tax ID"),
        ("tax id",),
    ),
    (
        "buyer_name", "bs",
        ("Kupac", "Naručilac", "Buyer"),
        ("kupac",),
    ),
    (
        "buyer_name", "hr",
        ("Kupac", "Naručitelj", "Buyer"),
        ("kupac",),
    ),
    (
        "buyer_name", "sr",
        ("Kupac", "Naručilac", "Buyer"),
        ("kupac",),
    ),
    (
        "buyer_name", "en",
        ("Buyer", "Customer", "Purchaser"),
        ("buyer",),
    ),
    (
        "buyer_tax_id", "bs",
        ("PIB kupca", "JIB kupca", "Tax ID kupca"),
        (),
    ),
    (
        "buyer_tax_id", "hr",
        ("OIB kupca", "Tax ID kupca", "PDV broj kupca"),
        (),
    ),
    (
        "buyer_tax_id", "sr",
        ("PIB kupca", "JIB kupca", "PDV broj kupca"),
        (),
    ),
    (
        "buyer_tax_id", "en",
        ("Buyer Tax ID", "Customer Tax ID", "VAT Number"),
        (),
    ),
    (
        "incoterm", "bs",
        ("Incoterm", "Uslovi isporuke", "Paritet"),
        ("incoterms",),
    ),
    (
        "incoterm", "hr",
        ("Incoterm", "Paritet", "Uvjeti isporuke"),
        ("incoterms",),
    ),
    (
        "incoterm", "sr",
        ("Incoterm", "Paritet", "Uslovi isporuke"),
        ("incoterms",),
    ),
    (
        "incoterm", "en",
        ("Incoterm", "Incoterms", "Terms of Delivery"),
        ("incoterms",),
    ),
    (
        "origin_statement", "bs",
        ("Izjava o porijeklu", "Porijeklo robe", "Deklaracija o porijeklu"),
        ("porijeklo",),
    ),
    (
        "origin_statement", "hr",
        ("Izjava o podrijetlu", "Podrijetlo robe", "Deklaracija o podrijetlu"),
        ("podrijetlo",),
    ),
    (
        "origin_statement", "sr",
        ("Izjava o poreklu", "Poreklo robe", "Deklaracija o poreklu"),
        ("poreklo",),
    ),
    (
        "origin_statement", "en",
        ("Origin Statement", "Declaration of Origin", "Country of Origin"),
        ("origin",),
    ),
    # 11 item polja
    (
        "redni_broj", "bs",
        ("R.br.", "Redni broj", "Rb", "Pozicija"),
        ("r.br",),
    ),
    (
        "redni_broj", "hr",
        ("R.br.", "Redni broj", "Stavka"),
        ("r.br",),
    ),
    (
        "redni_broj", "sr",
        ("R.br.", "Redni broj", "Pozicija"),
        ("r.br",),
    ),
    (
        "redni_broj", "en",
        ("No.", "#", "Item No", "Line"),
        ("item no",),
    ),
    (
        "sifra_proizvoda", "bs",
        ("Šifra", "Šifra proizvoda", "Kat. broj", "Kataloški broj"),
        ("šifra",),
    ),
    (
        "sifra_proizvoda", "hr",
        ("Šifra", "Šifra proizvoda", "Kat. broj"),
        ("šifra",),
    ),
    (
        "sifra_proizvoda", "sr",
        ("Šifra", "Šifra proizvoda", "Kat. broj"),
        ("šifra",),
    ),
    (
        "sifra_proizvoda", "en",
        ("Code", "Product Code", "SKU", "Article No"),
        ("code",),
    ),
    (
        "naziv_robe", "bs",
        ("Naziv", "Naziv robe", "Opis", "Proizvod"),
        ("naziv",),
    ),
    (
        "naziv_robe", "hr",
        ("Naziv", "Naziv robe", "Opis", "Proizvod"),
        ("naziv",),
    ),
    (
        "naziv_robe", "sr",
        ("Naziv", "Naziv robe", "Opis", "Proizvod"),
        ("naziv",),
    ),
    (
        "naziv_robe", "en",
        ("Description", "Item", "Product", "Goods"),
        ("description",),
    ),
    (
        "tarifni_broj", "bs",
        ("Tarifni broj", "HS kod", "Carinska šifra", "Tarifa"),
        ("tarifni",),
    ),
    (
        "tarifni_broj", "hr",
        ("Tarifni broj", "HS kod", "Carinska šifra"),
        ("tarifni",),
    ),
    (
        "tarifni_broj", "sr",
        ("Tarifni broj", "HS kod", "Carinska šifra"),
        ("tarifni",),
    ),
    (
        "tarifni_broj", "en",
        ("HS Code", "Tariff Code", "Customs Code"),
        ("hs code",),
    ),
    (
        "jedinica_mjere", "bs",
        ("JM", "Jedinica mjere", "Mjera", "Jedinica"),
        ("jedinica",),
    ),
    (
        "jedinica_mjere", "hr",
        ("JM", "Jedinica mjere", "Mjera"),
        ("jedinica",),
    ),
    (
        "jedinica_mjere", "sr",
        ("JM", "Jedinica mjere", "Jedinica"),
        ("jedinica",),
    ),
    (
        "jedinica_mjere", "en",
        ("UoM", "Unit", "Unit of Measure", "UM"),
        ("unit",),
    ),
    (
        "kolicina", "bs",
        ("Količina", "Kol.", "Qty", "Komada"),
        ("kolicina",),
    ),
    (
        "kolicina", "hr",
        ("Količina", "Kol.", "Qty"),
        ("kolicina",),
    ),
    (
        "kolicina", "sr",
        ("Količina", "Kol.", "Qty"),
        ("kolicina",),
    ),
    (
        "kolicina", "en",
        ("Quantity", "Qty", "Amount"),
        ("quantity",),
    ),
    (
        "jedinicna_cijena", "bs",
        ("Cijena", "Jedinična cijena", "Unit Price", "Cijena po jedinici"),
        ("cijena",),
    ),
    (
        "jedinicna_cijena", "hr",
        ("Cijena", "Jedinična cijena", "Unit Price"),
        ("cijena",),
    ),
    (
        "jedinicna_cijena", "sr",
        ("Cijena", "Jedinična cena", "Jedinična cijena"),
        ("cijena",),
    ),
    (
        "jedinicna_cijena", "en",
        ("Unit Price", "Price", "Unit Cost"),
        ("price",),
    ),
    (
        "iznos", "bs",
        ("Iznos", "Vrijednost", "Ukupno", "Total"),
        ("iznos",),
    ),
    (
        "iznos", "hr",
        ("Iznos", "Vrijednost", "Ukupno"),
        ("iznos",),
    ),
    (
        "iznos", "sr",
        ("Iznos", "Vrednost", "Ukupno"),
        ("iznos",),
    ),
    (
        "iznos", "en",
        ("Amount", "Total", "Value", "Line Total"),
        ("amount",),
    ),
    (
        "zemlja_porijekla", "bs",
        ("Porijeklo", "Zemlja porijekla", "Država porijekla"),
        ("porijeklo",),
    ),
    (
        "zemlja_porijekla", "hr",
        ("Podrijetlo", "Zemlja podrijetla", "Država podrijetla"),
        ("podrijetlo",),
    ),
    (
        "zemlja_porijekla", "sr",
        ("Poreklo", "Zemlja porekla", "Država porekla"),
        ("poreklo",),
    ),
    (
        "zemlja_porijekla", "en",
        ("Origin", "Country of Origin", "Made in"),
        ("origin",),
    ),
    (
        "neto_masa", "bs",
        ("Neto masa", "Neto težina", "Net Weight"),
        ("neto",),
    ),
    (
        "neto_masa", "hr",
        ("Neto masa", "Neto težina", "Net Weight"),
        ("neto",),
    ),
    (
        "neto_masa", "sr",
        ("Neto masa", "Neto težina", "Net Weight"),
        ("neto",),
    ),
    (
        "neto_masa", "en",
        ("Net Weight", "Net Mass", "Net Wt"),
        ("net weight",),
    ),
    (
        "bruto_masa", "bs",
        ("Bruto masa", "Bruto težina", "Gross Weight"),
        ("bruto",),
    ),
    (
        "bruto_masa", "hr",
        ("Bruto masa", "Bruto težina", "Gross Weight"),
        ("bruto",),
    ),
    (
        "bruto_masa", "sr",
        ("Bruto masa", "Bruto težina", "Gross Weight"),
        ("bruto",),
    ),
    (
        "bruto_masa", "en",
        ("Gross Weight", "Gross Mass", "Gross Wt"),
        ("gross weight",),
    ),
)


class ConceptLibrary:
    """Agregat koncepata za SVA 20 ciljnih polja.

    Lookup:
    - get(field, language) -> Concept | None
    - match_alias(normalized_text) -> (field, language) | None
    - all_fields() -> tuple[str, ...]
    """

    SUPPORTED_LANGUAGES: tuple[str, ...] = ("bs", "hr", "sr", "en")

    def __init__(self, concepts: tuple[Concept, ...] | None = None) -> None:
        if concepts is None:
            # Auto-build iz _CONCEPTS_DATA
            concepts = tuple(
                Concept(field=f, language=l, synonyms=s, context_phrases=p)
                for f, l, s, p in _CONCEPTS_DATA
            )
        # Index: (field, language) -> Concept
        self._by_key: dict[tuple[str, str], Concept] = {}
        # Index: normalized_alias -> (field, language)
        self._alias_index: dict[str, tuple[str, str]] = {}
        for concept in concepts:
            key = (concept.field, concept.language)
            if key in self._by_key:
                raise ValueError(f"Duplicate concept: {key}")
            self._by_key[key] = concept
            for syn in concept.synonyms:
                normalized = _normalize_for_match(syn)
                if not normalized:
                    continue
                if normalized in self._alias_index:
                    # First match wins (avoid ambiguity)
                    continue
                self._alias_index[normalized] = (concept.field, concept.language)

    def get(self, field: str, language: str) -> Concept | None:
        """Vrati Concept za polje + jezik, ili None."""
        return self._by_key.get((field, language))

    def match_alias(self, normalized_text: str) -> tuple[str, str] | None:
        """Vrati (field, language) za exact match sinonima.

        Case-insensitive, NFKC + strip dijakritika (vidi _normalize_for_match).
        """
        if not normalized_text:
            return None
        key = _normalize_for_match(normalized_text)
        if not key:
            return None
        return self._alias_index.get(key)

    def all_fields(self) -> tuple[str, ...]:
        """Vrati sortirane listu svih polja pokrivenih u library."""
        return tuple(sorted({key[0] for key in self._by_key}))

    def languages_for(self, field: str) -> tuple[str, ...]:
        """Vrati jezike za koje postoji Concept za zadano polje."""
        return tuple(
            lang
            for (f, lang) in self._by_key
            if f == field
        )

    def __len__(self) -> int:
        return len(self._by_key)


__all__ = ["ConceptLibrary"]
