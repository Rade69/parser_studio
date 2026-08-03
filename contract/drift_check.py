"""
Provjera odstupanja (drift) vendorovanog ugovora od živog deklarant_pro koda.

Zašto postoji: `contract/` je KOPIJA. Ako neko u deklarant_pro doda/preimenuje
polje na `InvoiceLine`, svi već generisani parseri i dalje rade (koriste keyword
argumente), ali NOVI parseri koje alat generiše mogu propustiti novo polje, a
verifikacija nivoa 8 (preview == generisano) bi i dalje prolazila jer obje strane
koriste istu zastarjelu kopiju. Ovo je tiha greška — zato provjera.

Poredi se SAMO skup imena polja dataclass-a i signature apstraktnih metoda —
ne cijeli izvorni kod, jer se docstringovi namjerno razlikuju.

Upotreba:
    python -m contract.drift_check "C:/Users/.../deklarant_pro"
"""
from __future__ import annotations

import ast
import sys
from dataclasses import fields as dataclass_fields
from pathlib import Path

# Šta se poredi: (vendorovana klasa, relativna putanja u deklarant_pro, ime klase)
_CHECKS = [
    ("Party", "core/draft/draft.py", "Party"),
    ("InvoiceLine", "core/draft/draft.py", "InvoiceLine"),
    ("ImportResult", "importers/import_result.py", "ImportResult"),
]

# Polja koja se NAMJERNO razlikuju (vidi docstring u draft_types.py)
_ALLOWED_DIFFS: dict[str, set[str]] = {}


def _ast_dataclass_field_names(source_path: Path, class_name: str) -> list[str]:
    """Izvuci imena polja dataclass-a iz izvornog koda, bez importovanja modula."""
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            names = []
            for stmt in node.body:
                # AnnAssign = "ime: tip = default" — to je dataclass polje
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    names.append(stmt.target.id)
            return names
    raise LookupError(f"Klasa {class_name} nije pronađena u {source_path}")


def check(deklarant_pro_root: Path) -> tuple[bool, list[str]]:
    """Vrati (ok, poruke). ok=False znači da je ugovor odstupio."""
    from contract import draft_types, import_result

    vendored_ns = {
        "Party": draft_types.Party,
        "InvoiceLine": draft_types.InvoiceLine,
        "ImportResult": import_result.ImportResult,
    }

    messages: list[str] = []
    ok = True

    if not deklarant_pro_root.is_dir():
        return False, [f"Putanja do deklarant_pro ne postoji: {deklarant_pro_root}"]

    for vendored_name, rel_path, live_class in _CHECKS:
        live_path = deklarant_pro_root / rel_path
        if not live_path.is_file():
            ok = False
            messages.append(f"❌ {vendored_name}: izvor ne postoji — {live_path}")
            continue

        try:
            live_names = _ast_dataclass_field_names(live_path, live_class)
        except (LookupError, SyntaxError) as exc:
            ok = False
            messages.append(f"❌ {vendored_name}: {exc}")
            continue

        vendored_names = [f.name for f in dataclass_fields(vendored_ns[vendored_name])]
        allowed = _ALLOWED_DIFFS.get(vendored_name, set())

        missing = [n for n in live_names if n not in vendored_names and n not in allowed]
        extra = [n for n in vendored_names if n not in live_names and n not in allowed]

        if missing:
            ok = False
            messages.append(
                f"❌ {vendored_name}: deklarant_pro ima polja koja kopija NEMA: {missing}"
            )
        if extra:
            ok = False
            messages.append(
                f"❌ {vendored_name}: kopija ima polja koja deklarant_pro NEMA: {extra}"
            )
        if not missing and not extra:
            messages.append(f"✅ {vendored_name}: {len(vendored_names)} polja, poklapa se")

    return ok, messages


def main() -> int:
    # Windows konzola je cp1252 — emoji u porukama je puca (isti problem opisan u
    # deklarant_pro/AGENTS.md). Prebaci stdout na UTF-8 prije prvog ispisa.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

    if len(sys.argv) < 2:
        print("Upotreba: python -m contract.drift_check <putanja_do_deklarant_pro>")
        return 2
    ok, messages = check(Path(sys.argv[1]))
    for m in messages:
        print(m)
    if not ok:
        print(
            "\nUgovor je ODSTUPIO. Prije generisanja novih parsera ažuriraj "
            "contract/ i podigni CONTRACT_VERSION."
        )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
