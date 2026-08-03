# Parser Studio

Alat za poluautomatsko pravljenje parsera faktura za **Deklarant Pro**, bez upotrebe LLM-a.

## Problem

`deklarant_pro` ima ~13 ručno pisanih parsera po dobavljaču (prosjek ~500 linija
po parseru). Svaki novi dobavljač zahtijeva programera.

## Cilj

Deklarant (ne programer) ubaci uzorak fakture → alat mu pomogne da definiše kako
se čita → izbaci **gotov, potpisan `.py` parser** koji `deklarant_pro` odmah
prihvata i koji se može proslijediti komitentu.

## Kako radi (bez LLM-a)

1. **Deklarativni profil (JSON)** — opisuje kako se dokument čita: detekcija
   formata, izbor engine-a, definicija kolona, mapiranje na `InvoiceLine`.
2. **Engine sloj** — parametrizuje već dokazane obrasce iz `deklarant_pro`
   (koordinatni x-opsezi, line-regex, Excel alias-mape).
3. **Sinteza iz primjera (PBE)** — korisnik označi 2+ reda kao "ovo su stavke",
   alat deterministički izvede regex poravnanjem tipiziranih tokena. Bez modela,
   bez API-ja — objašnjivo i testabilno.
4. **Codegen** — iz profila se generiše samostalan `.py` koji izgleda kao ručno
   pisan parser (programer ga može čitati i krpiti), sa ugrađenim profilom za
   round-trip nazad u alat.

## Struktura

```
contract/    VENDOROVANA kopija ugovora deklarant_pro (InvoiceLine, ImportResult, ImportStrategy)
core/        Jezgro — NULA PySide6 importa, testira se headless
viewmodels/  QObject, bez QWidget
views/       QWidget, bez poslovne logike
cli/         psbuild — generisanje parsera iz CI-ja
```

## Razvoj

```bash
pip install -e ".[dev]"
pytest                                              # headless, bez Qt-a
python -m contract.drift_check <putanja_do_deklarant_pro>   # provjera ugovora
```

### Zašto `contract/` postoji

`deklarant_pro` se ne uvozi kao zavisnost (projekti su odvojeni), pa alat drži
**kopiju** ugovora. `drift_check` provjerava da kopija nije zastarjela — to je
jedina odbrana od tihe greške gdje alat generiše parsere kojima nedostaje novo
polje, a interna verifikacija to ne primijeti.

## Sigurnost

- Uzorci faktura sadrže poslovne podatke (naziv firme, JIB, adresa) i **nikad
  ne idu u git** — vidi `.gitignore`.
- Profil ne smije sadržavati slobodan Python kod — samo imenovane transformacije
  iz fiksne biblioteke. Generisani kod prolazi AST provjeru na `eval`/`exec`.
