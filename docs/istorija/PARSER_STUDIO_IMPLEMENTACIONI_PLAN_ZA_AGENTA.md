# Parser Studio — implementacioni plan za agenta

**Verzija:** 1.0
**Osnova:** `PARSER_STUDIO_KONSOLIDOVANI_PLAN_I_PREPORUKE.md` v1.0 + odluka vlasnika projekta da sistem bude maksimalno deterministički, uz mogućnost da se AI uključi u bilo kojoj fazi.
**Namjena:** ovaj dokument se predaje agentu kao radni nalog. Nije arhitektonska rasprava — arhitektura je odlučena u konsolidovanom planu i ovdje se samo prevodi u fajlove, potpise i testove.

---

## 0. Provjereno stanje repozitorija

Sve u ovoj sekciji je provjereno kloniranjem `https://github.com/Rade69/parser_studio` i pokretanjem koda. Agent ne treba ovo ponovo utvrđivati, ali treba potvrditi da se poklapa sa stanjem koje zatekne.

**Postoji i ima sadržaj:**

| Fajl | Linija | Šta je |
|---|---|---|
| `contract/draft_types.py` | 175 | vendorovani `Party`, `InvoiceLine` |
| `contract/import_result.py` | 117 | vendorovani `ImportResult` + doslovno kopiran `validate()` |
| `contract/base_strategy.py` | 54 | vendorovani `ImportStrategy` |
| `contract/drift_check.py` | 123 | AST poređenje imena polja sa živim `deklarant_pro` |
| `contract/CONTRACT_VERSION` | 1 | `deklarant_pro/2026.08` |
| `core/documents/base.py` | 77 | `Cell`, `ExtractionTable`, `Document` protokol |
| `core/documents/excel_document.py` | 174 | keširan čitač `.xlsx`/`.xls` |
| `core/engines/base.py` | 50 | `ProbeResult`, `Engine` protokol |
| `core/engines/excel_headers.py` | 348 | `normalize_header`, `identify_columns`, `find_header_row`, `ExcelHeadersEngine` |
| `tests/unit/` | 537 | 3 test fajla |

**Prazni `__init__.py`, nula koda:** `cli/`, `services/`, `viewmodels/`, `views/`, `views/widgets/`, `views/wizard/`, `core/codegen/`, `core/detect/`, `core/library/`, `core/mapping/`, `core/profile/`, `core/synth/`, `core/transforms/`, `core/verify/`.

**Testovi:** `python -m pytest -q` → `71 passed, 1 skipped in 0.85s`. Preskočeni test je `tests/unit/test_contract.py:124` — traži `DEKLARANT_PRO_ROOT` env varijablu koja nije postavljena. To znači da **drift ugovora nije provjeren nijednom otkad je kopija napravljena**.

**Pristup `deklarant_pro`:** vlasnik je potvrdio da se oba projekta nalaze na istoj particiji i da agent smije koristiti `deklarant_pro` u razvoju i testiranju. Pristup je **samo za čitanje** — vidi pravilo 10 u sekciji 4.

**Zavisnosti u `pyproject.toml`:** PySide6, pdfplumber, openpyxl, xlrd, rapidfuzz, cryptography, pydantic, jinja2. Od toga se u kodu trenutno koriste samo openpyxl, xlrd, rapidfuzz. `pdfplumber` je deklarisan a `PdfDocument` ne postoji.

**Kontradikcije koje agent mora riješiti u M0 (ne ignorisati):**

1. `README.md` opisuje alat kao „deklarativni profil (JSON)" koji korisnik definiše. `PLAN.md` sekcija 4 i konsolidovani plan sekcija 5 to **eksplicitno odbacuju**. README je zastario.
2. `README.md` kaže „bez upotrebe LLM-a". Vlasnik je odlučio suprotno — AI je dozvoljen kao savjetnik u svakoj fazi. README je zastario.
3. Postoje direktoriji `core/profile/` i `views/wizard/` koji pripadaju odbačenom pravcu.
4. `core/engines/base.py` docstring pominje „wizard (korak 3)" — isto zastarjelo.
5. Dva plana u repou (`PLAN.md` v2 i konsolidovani v1.0) se preklapaju. Jedan mora postati istorijski.

---

## 1. Nepromjenjive odluke

Agent ove tačke ne preispituje i ne zaobilazi. Ako naiđe na zahtjev koji ih krši, staje i pita.

1. Krajnji proizvod je **samostalan `.py` parser** koji ne uvozi ništa iz `parser_studio` i radi kod komitenta bez mreže i bez API ključa.
2. **AI nikad ne vraća vrijednost — vraća kandidata sa lokacijom u dokumentu.** Izbor između kandidata, validacija i generisanje koda su deterministički kod.
3. Svaki kandidat, bez obzira na porijeklo, nosi `Locator` i `evidence`.
4. Bez `Locator`-a koji se deterministički verifikuje u dokumentu, AI kandidat se **odbacuje**.
5. Default režim je `ai=off`. Cijeli sistem mora raditi i prolaziti sve testove sa isključenim AI-jem.
6. Generator kompajlira isključivo iz `VendorParserModel` kroz provjerene Jinja2 šablone. **AI ne vidi šablone i ne piše Python kod koji završava u izlaznom fajlu.**
7. Verifikuje se **generisani `.py` fajl**, ne interni engine. Izvoz bez prolaska verifikatora ne postoji.
8. Zabranjeno u svakoj fazi, bez izuzetka: određivanje tarifnog broja iz opisa robe, popunjavanje praznog pravno značajnog polja pretpostavkom, samostalno razrješenje konflikta PDF/Excel, zaokruživanje masa na dvije decimale.
9. Stvarne fakture nikad ne idu u git.
10. `contract/` se ne uređuje ručno da bi test prošao. Ako drift postoji, ažurira se kopija i podiže `CONTRACT_VERSION`.

---

## 2. AI advisor sloj — specifikacija

Ovo je jedini dio koji nije razrađen u konsolidovanom planu, pa je ovdje dat u punom obimu.

### 2.1. Model kandidata

`core/model/locator.py`:

```python
from dataclasses import dataclass
from typing import Literal

SourceKind = Literal["pdf", "excel", "text"]

@dataclass(frozen=True, slots=True)
class Locator:
    path: str                                   # relativna putanja unutar DocumentBundle
    kind: SourceKind
    page: int | None = None                     # pdf
    bbox: tuple[float, float, float, float] | None = None   # pdf: x0, top, x1, bottom
    sheet: str | None = None                    # excel
    row: int | None = None                      # excel (0-indeksirano)
    col: int | None = None                      # excel (0-indeksirano)
    char_span: tuple[int, int] | None = None    # text
```

`core/model/candidate.py`:

```python
Stage = Literal[
    "classify_bundle",        # koji fajl je faktura, koji packing list
    "table_bounds",           # gdje počinje i završava tabela stavki
    "header_concept",         # header ćelija -> ime koncepta
    "line_group",             # koji redovi čine jednu stavku
    "value",                  # vrijednost polja
    "origin_statement",       # izjava o porijeklu
    "vendor_model_fragment",  # prijedlog dijela VendorParserModel
    "diagnostics",            # slobodan tekst za čovjeka, nula uticaja
]

@dataclass(frozen=True, slots=True)
class Candidate:
    stage: Stage
    field: str
    raw_value: str
    locator: Locator
    extractor_id: str        # "excel_headers@v1" ili "ai:vision:header_map@v3"
    evidence: str            # na srpskom, prikazuje se korisniku
    ai_assisted: bool = False
    normalized_value: Any = None
    issues: tuple[str, ...] = ()
```

### 2.2. Protokol savjetnika

`core/ai/advisor.py`:

```python
class Advisor(Protocol):
    advisor_id: str
    stages: frozenset[Stage]

    def propose(self, ctx: StageContext) -> list[Candidate]: ...
```

`StageContext` nosi `DocumentBundle`, trenutnu fazu, već pronađene deterministički kandidate i listu nerazriješenih polja. Advisor se registruje isto kao i deterministički ekstraktor — resolver iz sekcije 6.6 konsolidovanog plana ne zna niti ga zanima odakle je kandidat došao.

Za M4 se isporučuju dvije implementacije:

- `NullAdvisor` — vraća praznu listu. Koristi se kad je `ai=off`.
- `HttpVisionAdvisor` — jedan konkretan provajder iza `AdvisorTransport` apstrakcije, tako da se provajder može zamijeniti bez dodirivanja pozivnih mjesta.

### 2.3. Grounding gate — obavezan

`core/ai/grounding.py`:

```python
@dataclass(frozen=True)
class GroundingVerdict:
    ok: bool
    reason: str
    matched_text: str | None = None

def ground(candidate: Candidate, bundle: DocumentBundle) -> GroundingVerdict: ...
```

Pravila:

- `raw_value` mora biti pronađen na mjestu koje `locator` pokazuje.
- Poređenje: Unicode NFKC, zbijeni razmaci, case-insensitive. Ništa jače od toga — bez fuzzy poklapanja, jer fuzzy dozvoljava halucinaciju da prođe.
- Za `bbox`: riječi iz `PdfDocument` koje se preklapaju sa `bbox` moraju sadržavati `raw_value`.
- Za `sheet/row/col`: vrijednost ćelije mora sadržavati `raw_value`.
- Za `char_span`: isječak teksta mora sadržavati `raw_value`.
- Kandidat sa `stage="diagnostics"` je jedini izuzet — on ni ne ulazi u resolver.
- Odbačeni kandidat se **loguje** (`extractor_id`, `raw_value`, razlog) i prikazuje u izvještaju. Tiho odbacivanje je zabranjeno — bez toga se ne može mjeriti koliko model griješi.

Test koji mora postojati: `test_grounding_odbacuje_halucinirani_broj` — kandidat sa vrijednošću koje nema u dokumentu mora pasti.

### 2.4. Determinizam: keširanje i režimi

`core/ai/cache.py`:

```python
cache_key = sha256(f"{model_id}|{prompt_id}@{prompt_version}|{payload_sha256}".encode()).hexdigest()
```

`payload_sha256` je hash tačnog ulaza koji ide modelu (tekst i/ili rasterizovana stranica), ne fajla na disku — ista stranica iz dva različito imenovana fajla mora dati isti ključ.

Režimi preko `PS_AI_MODE`:

| Režim | Ponašanje | Gdje se koristi |
|---|---|---|
| `off` | `NullAdvisor`, nula mrežnih poziva | default, svi testovi, CI |
| `cache-only` | čita keš, promašaj keša = greška | regresija nad snimljenim odgovorima |
| `live` | poziva model, upisuje u keš | samo interaktivni rad |

CI mora imati test koji pada ako se u `off` režimu pokuša mrežni poziv (monkeypatch transporta koji diže izuzetak).

Keš se čuva uz uzorke, lokalno, van Gita: `samples/<vendor>/.ai-cache/<key>.json`.

### 2.5. Posljedica za izvoz

Svako polje sa `ai_assisted=True` mora biti izričito potvrđeno od čovjeka prije nego što se parser izveze. Izvještaj uz parser nabraja sve AI dodirne tačke, sa `advisor_id`, verzijom prompta i tim što je predloženo.

---

## 3. Milestone-i

Svaki milestone je jedan PR. Redoslijed nije proizvoljan — M4 dolazi poslije M3 namjerno, da bi AI od prvog dana bio „još jedan ekstraktor", a ne poseban put kroz sistem.

### M0 — higijena i razrješenje kontradikcija

Bez novih funkcija. Cilj je da repo prestane tvrditi dvije suprotne stvari.

- Prepisati `README.md`: AI je dozvoljen kao savjetnik, korisnik ne gradi JSON profil, nema wizarda.
- `PLAN.md` → `docs/istorija/PLAN_v2.md` sa zaglavljem „istorijski, zamijenjen konsolidovanim planom".
- Konsolidovani plan → `docs/PLAN.md`, dopunjen sekcijom o AI advisor sloju (sadržaj iz sekcije 2 ovog dokumenta).
- Obrisati `core/profile/` i `views/wizard/`.
- Ispraviti docstring u `core/engines/base.py` (uklonjena referenca na wizard).
- Dodati `.github/workflows/ci.yml`: `ruff check`, `pytest -q` sa `PS_AI_MODE=off`.
- Dodati `core/ai/` i `core/model/` kao prazne pakete sa `__init__.py`.
- **Prvi stvarni drift check.** Postaviti `DEKLARANT_PRO_ROOT` na lokalnu putanju, pokrenuti `python -m contract.drift_check "$DEKLARANT_PRO_ROOT"` i odblokirati preskočeni test `tests/unit/test_contract.py:124`. Ako padne, to nije kvar nego prvi rezultat — kopija u `contract/` nije provjerena otkad je napravljena. Agent tada ažurira kopiju prema živom kodu i podiže `CONTRACT_VERSION`, i u PR opis upisuje tačno koja su se polja razlikovala.

**Gotovo kad:** `pytest -q` daje 72 passed, 0 skipped (drift test sada stvarno radi), `ruff check` čist, nijedan fajl u repou ne pominje „wizard" ili „bez upotrebe LLM-a" kao trenutni pravac.

### M1 — model kandidata i provenance

- `core/model/locator.py`, `core/model/candidate.py` — kako je specificirano u 2.1.
- `core/model/draft.py` — `ExtractionDraft` prema sekciji 6.5 konsolidovanog plana, sa `conflicts` i `unresolved_fields`.
- `core/model/confidence.py` — kategorije `VISOKA`, `POTREBNA_PROVJERA`, `NERIJEŠENO`. **Bez procenata** — konsolidovani plan 6.6 to izričito zabranjuje dok nema kalibracije.
- Adapter `ExtractionTable` → `list[Candidate]` da postojeći `ExcelHeadersEngine` odmah proizvodi kandidate.

**Gotovo kad:** `ExcelHeadersEngine` kroz adapter daje kandidate sa popunjenim `Locator(sheet, row, col)` za svaku ćeliju, i to je pokriveno testom nad postojećim fixture-om iz `test_excel_headers_engine.py`.

### M2 — PDF i bundle

- `core/documents/pdf_document.py` — pdfplumber, kešira `extract_words()` po stranici, čuva `x0, x1, top, bottom`. Isti protokol kao `ExcelDocument`, nula PySide6 importa.
- `core/documents/text_document.py` — normalizovan tekst sa `char_span` mapiranjem nazad na izvor.
- `core/documents/bundle.py` — `DocumentBundle` prema sekciji 6.2: koji fajlovi pripadaju istom poslu, tip po fajlu, autoritativni izvor po polju, `consumed_paths`.
- `core/documents/raster.py` — rasterizacija stranice u PNG. Potrebna za vision advisor u M4; ovdje se pravi jer pripada document sloju.

**Gotovo kad:** test nad sintetičkim PDF-om (generisan u testu, ne stvarna faktura) vraća riječi sa koordinatama, i `DocumentBundle` od PDF+Excel para tačno popunjava `consumed_paths`.

### M3 — registar ekstraktora i prvi deterministički ekstraktori

`core/extract/registry.py` — registracija po fazi, stabilan redoslijed (`extractor_id` sortiran), tako da je izlaz reproducibilan.

Ekstraktori (svaki u svom fajlu pod `core/extract/`), prema sekciji 6.4:

- `label_right.py` — labela + tekst desno
- `label_below.py` — labela + blok ispod
- `excel_header.py` — omotač oko postojećeg `excel_headers`
- `pdf_column_geometry.py` — kolone iz x-opsega riječi
- `value_shape.py` — regex po obliku (ISO zemlja, valuta, tarifni broj, EU/US decimalni format)
- `column_content.py` — prepoznavanje kolone po sadržaju kad header ne postoji

`core/library/concepts.py` — biblioteka sinonima prema sekciji 16: svaka oznaka nosi jezik, očekivani tip vrijednosti, prostorni odnos, prioritet i **negativni kontekst**. Ne ravna lista stringova.

**Gotovo kad:** nad sintetičkim fixture-ima svaki ekstraktor daje kandidate sa `evidence` tekstom na srpskom, i postoji test da dva ekstraktora koja nađu istu vrijednost daju dva odvojena kandidata (resolver ih spaja, ne ekstraktor).

### M4 — AI advisor infrastruktura

- `core/ai/advisor.py`, `core/ai/grounding.py`, `core/ai/cache.py`, `core/ai/transport.py` prema sekciji 2.
- `NullAdvisor` + `HttpVisionAdvisor`.
- Prompt šabloni u `core/ai/prompts/` sa eksplicitnom verzijom u imenu fajla. Svaki prompt traži **isključivo** JSON oblika `Candidate` bez `ai_assisted` polja (to postavlja kod, ne model).
- Snimljeni odgovori kao fixture-i za `cache-only` testove.

**Gotovo kad:** testovi prolaze u sva tri režima (`off`, `cache-only` sa fixture-ima, `live` preskočen bez ključa), grounding test odbacuje halucinaciju, i test dokazuje da `off` režim ne pravi mrežni poziv.

### M5 — resolver i validacije

- `core/resolve/resolver.py` — bira između kandidata kombinujući dokaze (sekcija 6.6). Ne jedan regex, nego skup: header liči na `Quantity` + vrijednosti su pozitivni brojevi + susjedna kolona ima poznate JM + količina × cijena ≈ iznos reda.
- `core/resolve/validators/` — sintaksne, strukturne, aritmetičke, domenske, međudokumentne.
- Izlaz: `ExtractionDraft` sa kategorijom pouzdanosti i razlozima po polju.

**Gotovo kad:** nad sintetičkim uzorcima resolver bira tačnog kandidata, a kad su dokazi u sukobu upisuje konflikt umjesto da bira — pokriveno testom koji namjerno pravi PDF/Excel neslaganje.

### M6 — VendorParserModel i generator

- `core/model/vendor_model.py` — struktura iz sekcije 6.8, pydantic šema, verzionisana.
- `core/codegen/templates/` — Jinja2 šabloni za `detect_*`, `parse_*`, ekstrakciju stranaka, stavki, težina, normalizaciju, fallback, `ImportResult`.
- `core/codegen/generator.py` — model → `.py`.
- `core/codegen/guards.py` — `ast.parse()`, `compile()`, allowlist importa, zabrana `eval`/`exec`/`__import__`/dinamičkog `getattr`, formatter, ruff.

Allowlist importa: Python stdlib + biblioteke koje `deklarant_pro` garantovano distribuira. Bilo kakav `from parser_studio import` u izlazu je greška generatora, ne upozorenje.

**Gotovo kad:** iz ručno sastavljenog `VendorParserModel` nastaje `.py` fajl koji prolazi sve guard provjere i uvozi se u izolovanom procesu.

### M7 — verifikator generisanog parsera

- `core/verify/runner.py` — pokretanje u zasebnom procesu (`python -I`), timeout, privremeni radni direktorijum, hvatanje stdout/stderr.
- `core/verify/compare.py` — poređenje polje po polje sa potvrđenim očekivanim rezultatom.
- `core/verify/detect_corpus.py` — negativni testovi: `detect_*` mora **odbiti** uzorke svih drugih dobavljača i generičke PDF/Excel dokumente.
- `core/verify/gate.py` — izvoz je moguć samo ako pozitivni testovi prolaze, negativni ne daju lažno prihvatanje, i svako `ai_assisted` polje je potvrđeno.
- `core/verify/oracle.py` — sekcija 9 konsolidovanog plana, sada izvodljiva: učita postojeći ručno pisani parser iz `$DEKLARANT_PRO_ROOT/importers/vendors/<dobavljač>/` u zasebnom procesu, pusti ga nad uzorkom, snimi izlaz kao početni očekivani rezultat, pa ga uporedi sa izlazom generisanog parsera polje po polje.

Izlaz starog parsera nije apsolutna istina — konsolidovani plan to izričito kaže. Tretira se kao početni oracle koji korisnik potvrđuje ili koriguje. Kad se razlikuju, izvještaj mora prikazati obje vrijednosti i pustiti čovjeka da odluči, a ne tiho preuzeti stariju.

Napomena o sandboxu koju agent ne smije preskočiti: izolovani proces je mjera stabilnosti, **ne sigurnosna granica**. Kod dolazi iz naših šablona. Ne pisati u komentarima ni dokumentaciji da je izvršavanje „sigurno".

**Gotovo kad:** generisani parser se stvarno pokrene nad svim uzorcima i vrati diff izvještaj; test dokazuje da gate blokira izvoz kad jedan uzorak padne.

### M8 — HTML pregled i regresiona biblioteka

- `services/report/html_report.py` — original naspram rezultata, dokaz po vrijednosti, odbačeni AI kandidati, konflikti.
- `services/samples/index.py` — lokalni indeks uzoraka: interni ID, SHA-256, dobavljač, datum, varijanta, status odobrenja, verzija parsera.
- `cli/psbuild.py` — `psbuild analyze|generate|verify|export`, sve headless.

**Gotovo kad:** cijeli tok od uzorka do verifikovanog `.py` radi iz komandne linije bez Qt-a.

### Poslije M8

PySide6 radni prostor (sekcija 6 konsolidovanog plana), plugin/potpisivanje, OCR ako stvarni uzorci pokažu potrebu. Ne prije.

---

## 4. Pravila rada za agenta

1. **Ne tvrdi da si nešto pokrenuo ako nisi.** Svaki PR sadrži stvarni izlaz `pytest -q`, ne parafrazu.
2. Svaki novi ekstraktor i advisor dolazi sa testom. Bez testa se ne mergeuje.
3. `PS_AI_MODE=off` mora ostati zelen nakon svakog milestone-a. Ako neka funkcija radi samo sa uključenim AI-jem, arhitektura je pogrešna.
4. Ne dodavati zavisnosti bez obrazloženja u PR opisu. `cryptography` i `pydantic` su već deklarisani ali neiskorišteni — ili ih upotrijebi ili ukloni u M0.
5. Ne uređivati `contract/` ručno. Pokreni `python -m contract.drift_check <putanja>` i ako pada, ažuriraj kopiju i podigni `CONTRACT_VERSION`.
6. Nijedna stvarna faktura, `.ai-cache` fajl ni izvještaj sa poslovnim podacima ne ide u git. Provjeri `.gitignore` prije prvog commita sa uzorcima.
7. Kad nešto ne znaš — napiši „ne znam" u PR opisu i navedi šta konkretno treba provjeriti. Ne popunjavaj prazninu pretpostavkom.
8. Poruke korisniku (`evidence`, `reason`, validacione poruke) pišu se na srpskom, jer ih čita deklarant a ne programer.
9. Nazivi polja u `InvoiceLine` su srpski namjerno. Preimenovanje lomi `deklarant_pro`.
10. **`deklarant_pro` se smije samo čitati.** Agent ga koristi za `drift_check` i za oracle iz M7, i ništa više. Ne piše u njega, ne mijenja mu kod, ne kopira generisane parsere u `importers/vendors/`, i nijedan test Parser Studija ne smije dirati taj folder. Ako se ispostavi da izlaz Parser Studija radi tek nakon izmjene u `deklarant_pro`, to se prijavljuje kao nalaz — ne popravlja se u glavnoj aplikaciji. Odvojenost projekata je nepromjenjiva odluka broj 1.

---

## 5. Šta blokira agenta i traži tvoju odluku prije početka

1. **Koja 2–3 dobavljača su pilot.** Bez toga nema korpusa za M7 i nema mjerila uspjeha. Treba jedan lak slučaj (Excel sa čistim header redom) i jedan težak (PDF bez linija tabele, strani jezik). Blokira M7, ne blokira M0–M6.
2. **Koji AI provajder i model** za vision advisor u M4, i da li ključ postoji. Apstrakcija transporta ublažava izbor, ali prompt šabloni se pišu za konkretan model. Blokira M4.
3. **`cryptography` i `pydantic`** — ostaju ili se brišu iz `pyproject.toml` u M0. Prijedlog: `pydantic` ostaje (šema `VendorParserModel` u M6), `cryptography` ispada dok potpisivanje ne postane stvarno.
4. **Potvrda brisanja** `core/profile/` i `views/wizard/`.

**Riješeno:** pristup `deklarant_pro` — vlasnik je potvrdio da su oba projekta na istoj particiji i da agent smije čitati živi kod u razvoju i testiranju. `drift_check` ulazi u M0, oracle u M7.

---

## 6. Kriterijum uspjeha cjeline

Preuzeto iz sekcije 20 konsolidovanog plana, sa jednom dopunom vezanom za AI:

1. Iz uzoraka 2–3 postojeća dobavljača generisati samostalne parsere.
2. Isti ili korisnički potvrđen izlaz kao postojeći ručni parseri.
3. Svi pozitivni testovi uzoraka prolaze.
4. `detect_*` ne presreće fakture drugih dobavljača.
5. Tačan izvor svake ključne vrijednosti.
6. Neriješeni i konfliktni podaci prikazani, ne nagađani.
7. Čitljiv generisani kod.
8. Isti izlaz iz istih uzoraka i iste verzije engine-a — **uključujući `cache-only` režim sa AI-jem**.
9. Kraće vrijeme izrade parsera bez povećanja rizika.
10. **Dopuna:** svaki AI prijedlog koji je ušao u finalni parser je zabilježen, potvrđen od čovjeka, i rekonstruktivan iz keša.
