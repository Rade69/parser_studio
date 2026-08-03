"""
ExcelDocument — unificiran, keširan pristup .xlsx (openpyxl) i .xls (xlrd).

Generalizacija `_SheetAdapter` obrasca iz deklarant_pro
(importers/vendors/sumaprom/sumaprom_excel_parser.py:32-67), proširena sa:
  - keširanjem (jedan open po fajlu — live preview inače otvara isti fajl
    desetak puta na svaku izmjenu profila),
  - pristupom SVIM sheet-ovima (original čita samo prvi),
  - pretragom header reda,
  - provenancom (Cell zna svoj row/col/sheet).

Pravilo: NULA PySide6 importa.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from core.documents.base import Cell

_XLSX_EXT = {".xlsx", ".xlsm"}
_XLS_EXT = {".xls"}
EXCEL_EXTENSIONS = _XLSX_EXT | _XLS_EXT


class Sheet:
    """Jedan list, kao pravougaona matrica vrijednosti (0-indeksirano)."""

    def __init__(self, name: str, rows: list[list[Any]]) -> None:
        self.name = name
        self._rows = rows
        self.nrows = len(rows)
        self.ncols = max((len(r) for r in rows), default=0)

    def value(self, row: int, col: int) -> Any:
        """Sirova vrijednost; prazan string van opsega (nikad IndexError)."""
        if row < 0 or row >= self.nrows:
            return ""
        r = self._rows[row]
        if col < 0 or col >= len(r):
            return ""
        v = r[col]
        return "" if v is None else v

    def cell(self, row: int, col: int) -> Cell:
        return Cell(value=self.value(row, col), row=row, col=col, sheet=self.name)

    def row_text(self, row: int, sep: str = " ") -> str:
        """Sav tekst jednog reda spojen — za detekciju header reda / ključnih riječi."""
        if row < 0 or row >= self.nrows:
            return ""
        parts = [str(v).strip() for v in self._rows[row] if v is not None and str(v).strip()]
        return sep.join(parts)

    def find_row_containing(
        self, needles: list[str], *, max_rows: int = 30, require_all: bool = True
    ) -> int:
        """Prvi red koji sadrži zadane pojmove (case-insensitive). -1 ako nema.

        `require_all=True` → red mora sadržati SVE pojmove (obrazac koji koriste
        svi postojeći detect_* u deklarant_pro: keyword-AND).
        """
        if not needles:
            return -1
        wanted = [n.upper() for n in needles]
        for row in range(min(max_rows, self.nrows)):
            text = self.row_text(row).upper()
            hits = [w in text for w in wanted]
            if (all(hits) if require_all else any(hits)) and any(hits):
                return row
        return -1

    def __repr__(self) -> str:
        return f"<Sheet {self.name!r} {self.nrows}x{self.ncols}>"


class ExcelDocument:
    """Keširan Excel dokument. Otvara fajl jednom, drži vrijednosti u memoriji."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._sheets: list[Sheet] | None = None
        self._full_text: str | None = None

    @property
    def path(self) -> Path:
        return self._path

    @staticmethod
    def can_open(path: str | Path) -> bool:
        return Path(path).suffix.lower() in EXCEL_EXTENSIONS

    # ── učitavanje ────────────────────────────────────────────────────

    def _load(self) -> list[Sheet]:
        if self._sheets is not None:
            return self._sheets

        ext = self._path.suffix.lower()
        if ext in _XLSX_EXT:
            self._sheets = self._load_xlsx()
        elif ext in _XLS_EXT:
            self._sheets = self._load_xls()
        else:
            raise ValueError(f"Nepodržana ekstenzija za Excel: {ext}")
        return self._sheets

    def _load_xlsx(self) -> list[Sheet]:
        import openpyxl

        wb = openpyxl.load_workbook(self._path, data_only=True, read_only=True)
        try:
            return [
                Sheet(ws.title, [list(r) for r in ws.iter_rows(values_only=True)])
                for ws in wb.worksheets
            ]
        finally:
            wb.close()

    def _load_xls(self) -> list[Sheet]:
        import xlrd

        wb = xlrd.open_workbook(self._path)
        sheets = []
        for s in wb.sheets():
            rows = [
                [s.cell_value(r, c) for c in range(s.ncols)]
                for r in range(s.nrows)
            ]
            sheets.append(Sheet(s.name, rows))
        return sheets

    # ── javni pristup ─────────────────────────────────────────────────

    @property
    def sheets(self) -> list[Sheet]:
        return self._load()

    @property
    def sheet_names(self) -> list[str]:
        return [s.name for s in self._load()]

    def sheet(self, ref: int | str = 0) -> Sheet:
        """Sheet po indeksu ili imenu. Podrazumijevano prvi."""
        sheets = self._load()
        if not sheets:
            raise ValueError(f"Excel fajl nema nijedan list: {self._path}")
        if isinstance(ref, int):
            return sheets[ref]
        for s in sheets:
            if s.name == ref:
                return s
        raise KeyError(f"List {ref!r} ne postoji. Dostupni: {[s.name for s in sheets]}")

    def full_text(self) -> str:
        """Sav tekst svih listova — za detekciju formata (keširano)."""
        if self._full_text is None:
            parts = []
            for s in self._load():
                parts.append(s.name)
                for row in range(s.nrows):
                    t = s.row_text(row)
                    if t:
                        parts.append(t)
            self._full_text = "\n".join(parts)
        return self._full_text

    def close(self) -> None:
        self._sheets = None
        self._full_text = None

    def __repr__(self) -> str:
        loaded = "ucitano" if self._sheets is not None else "neucitano"
        return f"<ExcelDocument {self._path.name!r} ({loaded})>"
