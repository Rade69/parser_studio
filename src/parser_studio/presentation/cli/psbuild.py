# Presentation: cli/psbuild.
# Posjeduje: CLI entry point sa import/analyze/confirm komandama.
# Zna za: parser_studio.application, parser_studio.bootstrap, parser_studio.domain.
# Ne zna za: SQLite direktno, Docling, contract.
"""CLI entry point za Parser Studio.

Migriran iz legacy cli/psbuild.py (A7 cleanup).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from parser_studio.bootstrap import build_default_application

VERSION = "0.2.0"


def cmd_import(args, app) -> int:
    """Import komanda: ucitaj .xlsx, ispisi sazetak."""
    from parser_studio.application.ingest.import_document import ImportRequest

    result = app[0].execute(ImportRequest(path=Path(args.path)))
    print(f"Document: {result.document.source_path}")
    print(f"Cells: {len(result.document.cells)}")
    print(f"Sheets: {len(result.document.pages)}")
    return 0


def cmd_analyze(args, app) -> int:
    """Analyze komanda: import + analyze, ispisi kandidate po polju."""
    from parser_studio.application.extraction.analyze_invoice import (
        AnalyzeInvoice,
        AnalyzeRequest,
    )
    from parser_studio.application.ingest.import_document import (
        ImportDocument,
        ImportRequest,
    )

    import_doc: ImportDocument = app[0]
    analyze_uc: AnalyzeInvoice = app[1]

    import_result = import_doc.execute(ImportRequest(path=Path(args.path)))
    target_fields = (
        "kolicina", "cijena_jed", "iznos", "naziv_robe",
        "tarifni_broj", "zemlja_porijekla",
    )
    draft = analyze_uc.execute(
        AnalyzeRequest(
            document=import_result.document,
            target_fields=target_fields,
        )
    )
    for field in target_fields:
        candidates = draft.candidates_for(field)
        print(f"{field}: {len(candidates)} candidate(s)")
    return 0


def cmd_confirm(args, app) -> int:
    """Confirm komanda: import + analyze + confirm sa --field vrijednostima."""
    from parser_studio.application.extraction.analyze_invoice import (
        AnalyzeRequest,
    )
    from parser_studio.application.ingest.import_document import (
        ImportRequest,
    )
    from parser_studio.application.review.confirm_invoice import (
        ConfirmInvoice,
        ConfirmRequest,
        FieldConfirmation,
    )
    from parser_studio.domain.evidence.locator import Locator

    import_result = app[0].execute(ImportRequest(path=Path(args.path)))
    target_fields = tuple(f.split("=", 1)[0] for f in args.field)
    draft = app[1].execute(
        AnalyzeRequest(
            document=import_result.document,
            target_fields=target_fields,
        )
    )

    confirmations = []
    for field_value in args.field:
        field, value = field_value.split("=", 1)
        confirmations.append(
            FieldConfirmation(
                field=field,
                raw_value=None,
                normalized_value=value,
                locator=Locator(
                    source_path=str(import_result.document.source_path),
                    kind="excel",
                ),
                confirmed=True,
            )
        )

    confirm_uc: ConfirmInvoice = app[2]
    events = confirm_uc.execute(
        ConfirmRequest(
            draft=draft,
            confirmations=tuple(confirmations),
            actor=args.actor,
        )
    )
    print(f"Confirmed {len(events)} field(s)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Kreiraj argparse parser za psbuild CLI."""
    parser = argparse.ArgumentParser(
        prog="psbuild", description="Parser Studio CLI"
    )
    parser.add_argument(
        "--version", action="version", version=f"psbuild {VERSION}"
    )
    subparsers = parser.add_subparsers(dest="command")

    p_import = subparsers.add_parser("import", help="Import dokument")
    p_import.add_argument("path", help="Putanja do .xlsx/.xls")

    p_analyze = subparsers.add_parser("analyze", help="Import + analyze")
    p_analyze.add_argument("path")

    p_confirm = subparsers.add_parser(
        "confirm", help="Import + analyze + confirm"
    )
    p_confirm.add_argument("path")
    p_confirm.add_argument(
        "--field", action="append", required=True, help="field=value"
    )
    p_confirm.add_argument(
        "--actor", default="user:cli", help="user id za learning event"
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Glavna CLI funkcija. Vraca exit code.

    --version se obrađuje automatski od strane argparse (action="version").
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # In-memory SQLite repo za CLI testiranje
    # Produkcija koristi file-based preko env var
    app = build_default_application(db_path=":memory:")
    try:
        try:
            if args.command == "import":
                return cmd_import(args, app)
            elif args.command == "analyze":
                return cmd_analyze(args, app)
            elif args.command == "confirm":
                return cmd_confirm(args, app)
            else:
                parser.print_help()
                return 1
        except (FileNotFoundError, ValueError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    finally:
        # SQLite repo je cetvrti element tuple-a
        app[3].close()


if __name__ == "__main__":
    sys.exit(main())
