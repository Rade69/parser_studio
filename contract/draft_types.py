"""
VENDOROVANA kopija ugovora iz deklarant_pro/core/draft/draft.py.

NE UREĐIVATI RUČNO — ovo je kopija, ne original. Izvor:
    deklarant_pro/core/draft/draft.py  (Party: l.44-66, InvoiceLine: l.74-202)

Kopirano je SAMO ono što parser mora znati: Party i InvoiceLine. Sve ostalo iz
originala (DeclarationDraft, NaimenovanjeDraft, LineDecisionState) alat ne
koristi.

Jedina namjerna razlika u odnosu na original: `decision_state` je ovdje opaque
(prima bilo šta i čuva kako jeste) umjesto da se parsira u `LineDecisionState` —
alat ne treba `core.decision.decision_model`, a nijedan parser to polje ionako ne
popunjava (parseri proizvode SIROVE stavke, decision_state nastaje kasnije u
aplikaciji).

Provjera odstupanja: `contract/drift_check.py`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple


def _s(v: Any) -> str:
    return "" if v is None else str(v).strip()


def _f(v: Any) -> float:
    try:
        if v is None or v == "":
            return 0.0
        return float(str(v).replace(",", "."))
    except Exception:
        return 0.0


@dataclass(slots=True)
class Party:
    name: str = ""
    address: str = ""
    city: str = ""
    country: str = ""
    vat_or_id: str = ""

    @classmethod
    def from_any(cls, v: Any) -> "Party":
        if isinstance(v, cls):
            return v
        if isinstance(v, dict):
            return cls(
                name=_s(v.get("name") or v.get("naziv") or v.get("Naziv")),
                address=_s(v.get("address") or v.get("adresa") or v.get("Adresa")),
                city=_s(v.get("city") or v.get("grad") or v.get("Grad")),
                country=_s(v.get("country") or v.get("drzava") or v.get("Drzava")),
                vat_or_id=_s(
                    v.get("vat_or_id") or v.get("id") or v.get("ID") or v.get("JIB")
                ),
            )
        return cls(name=_s(v))


@dataclass(slots=True)
class InvoiceLine:
    """Sirova stavka iz fakture (XLSX/PDF) – normalizovana.

    KRITIČNO: nazivi polja su SRPSKI namjerno (projektno pravilo deklarant_pro,
    AGENTS.md). Preimenovanje na engleski lomi sve importere.
    """

    line_no: int = 0
    invoice_number: str = ""

    naziv_robe: str = ""
    product_code: str = ""
    tarifni_broj: str = ""
    tariff_suffix: str = "000"
    zemlja_porijekla: str = ""
    povlastica: str = ""

    # EUR.1 podaci
    eur1_number: str = ""
    has_origin_statement: bool = False
    is_authorized_exporter: bool = False
    no_preference: bool = False

    # Confidence za zemlju porijekla
    country_confidence: str = ""
    country_source: str = ""
    country_conflict_details: str = ""

    tariff_similarity: float = 0.0

    jm: str = ""
    kolicina: float = 0.0
    cijena_jed: float = 0.0
    iznos: float = 0.0
    valuta: str = "EUR"

    bruto_kg: float = 0.0
    neto_kg: float = 0.0

    exporter: Party = field(default_factory=Party)
    importer: Party = field(default_factory=Party)

    raw: Dict[str, Any] = field(default_factory=dict)

    decision_state: Any = None

    assigned_naimenovanje_id: str = ""
    assigned_naimenovanje_ordinal: int = 0

    def key(self) -> Tuple[str, str, str]:
        """KLJUČ za grupisanje: tarifni broj + zemlja porijekla + povlastica."""
        return (_s(self.tarifni_broj), _s(self.zemlja_porijekla), _s(self.povlastica))

    @classmethod
    def from_any(cls, v: Any, default_currency: str = "EUR") -> "InvoiceLine":
        """Prihvata dict-ove iz različitih importera i normalizuje ih u InvoiceLine."""
        if isinstance(v, cls):
            return v
        if not isinstance(v, dict):
            return cls(naziv_robe=_s(v), valuta=default_currency)

        naziv = (
            v.get("naziv_robe") or v.get("Naziv robe") or v.get("opis")
            or v.get("description") or ""
        )
        product_code = (
            v.get("product_code") or v.get("kod") or v.get("Kod")
            or v.get("sifra") or v.get("code") or ""
        )
        tarif = (
            v.get("tarifni_broj") or v.get("Tarifni broj") or v.get("tarif")
            or v.get("hs") or ""
        )
        zemlja = (
            v.get("zemlja_porijekla") or v.get("Zemlja porijekla") or v.get("origin")
            or v.get("Country_of_origin_code") or ""
        )
        pref = (
            v.get("povlastica") or v.get("Povlastica") or v.get("preference")
            or v.get("Preference_code") or ""
        )

        jm = v.get("jm") or v.get("JM") or v.get("unit") or ""
        kolicina = _f(v.get("kolicina") or v.get("Kolicina") or v.get("qty") or 0)
        cijena_jed = _f(v.get("cijena_jed") or v.get("Cijena") or v.get("price") or 0)
        iznos = _f(v.get("iznos") or v.get("Iznos") or v.get("amount") or 0)
        valuta = _s(
            v.get("valuta") or v.get("Valuta") or v.get("currency") or default_currency
        )

        bruto = _f(v.get("bruto_kg") or v.get("Bruto") or v.get("gross") or 0)
        neto = _f(v.get("neto_kg") or v.get("Neto") or v.get("net") or 0)

        return cls(
            line_no=int(_f(v.get("line_no") or v.get("Line") or 0)),
            naziv_robe=_s(naziv),
            product_code=_s(product_code),
            tarifni_broj=_s(tarif),
            zemlja_porijekla=_s(zemlja),
            povlastica=_s(pref),
            jm=_s(jm),
            kolicina=kolicina,
            cijena_jed=cijena_jed,
            iznos=iznos,
            valuta=valuta or default_currency,
            bruto_kg=bruto,
            neto_kg=neto,
            exporter=Party.from_any(v.get("exporter") or {}),
            importer=Party.from_any(v.get("importer") or {}),
            raw=dict(v),
            decision_state=v.get("decision_state"),
        )
