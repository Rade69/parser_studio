# Parser Studio — konsolidovani plan, arhitektura i preporuke

**Verzija:** 1.0  
**Datum:** 3. avgust 2026.  
**Status:** razvojni dokument / arhitektonska osnova

---

## 1. Svrha dokumenta

Ovaj dokument objedinjuje:

- prvobitni plan za Parser Studio;
- naknadno razjašnjenje odnosa sa aplikacijom Deklarant Pro;
- tehničku analizu održivosti predloženog pristupa;
- preporuke za arhitekturu, testiranje, generisanje koda i fazni razvoj.

Najvažnije razjašnjenje je sljedeće:

> **Parser Studio je potpuno samostalna aplikacija. Deklarant Pro ne koristi njegov engine, bazu, profile niti bilo koji njegov runtime. Jedini proizvod Parser Studija je samostalan `.py` parser koji se u Deklarant Pro uvozi i koristi kao postojeći ručno pisani parseri.**

Parser Studio je, dakle, razvojni alat za automatsko projektovanje, generisanje i provjeru parsera — nije dio svakodnevnog toka rada Deklarant Pro aplikacije.

---

## 2. Problem koji Parser Studio rješava

Deklarant Pro trenutno koristi približno 13 ručno pisanih parsera po dobavljaču. Svaki novi dobavljač zahtijeva:

1. pregled nekoliko PDF i/ili Excel faktura;
2. razumijevanje njihove strukture;
3. ručno pisanje regexa, pravila, koordinata i fallback logike;
4. testiranje nad više uzoraka;
5. uklapanje parsera u postojeći ugovor Deklarant Pro aplikacije.

Prosječan parser ima oko 500 linija koda. Glavno usko grlo nije samo pisanje koda, nego ponavljanje istog procesa otkrivanja strukture dokumenta.

Parser Studio treba automatizovati najveći dio tog procesa tako da korisnik:

- ubaci nekoliko uzoraka fakture;
- pregleda šta je alat prepoznao;
- ispravi greške ili označi problem;
- dobije gotov i testiran `.py` parser.

Cilj nije apsolutna automatizacija svakog mogućeg dokumenta. Realan cilj je:

> **smanjiti izradu novog parsera sa višesatnog programerskog rada na kontrolisan postupak analize, pregleda i generisanja, uz minimalnu intervenciju programera samo kod novih klasa problema.**

---

## 3. Čvrste granice sistema

### 3.1. Parser Studio radi

- učitavanje i analizu PDF/Excel uzoraka;
- automatsko prepoznavanje stranaka, stavki, tarifa, porijekla, količina, cijena, težina, valuta i Incoterms podataka;
- prikaz izvornog dokumenta naspram rezultata;
- čuvanje dokaza o izvoru svake vrijednosti;
- izgradnju internog modela strukture konkretnog dobavljača;
- generisanje čitljivog Python parsera;
- izvršavanje i testiranje upravo generisanog parsera;
- izvoz gotovog `.py` fajla i pratećeg izvještaja.

### 3.2. Parser Studio ne radi

- svakodnevni uvoz faktura u poslovnom radu;
- kreiranje ASYCUDA deklaracija;
- direktno mijenjanje podataka u Deklarant Pro;
- obaveznu LLM analizu;
- runtime obradu dokumenata kod klijenta;
- ručno crtanje kolona i konfiguracioni wizard za korisnika;
- generisanje parsera koji zavisi od Parser Studio biblioteka.

### 3.3. Deklarant Pro dobija samo

- jedan samostalan `.py` parser;
- eventualno manifest/metapodatke ako se kasnije uvede plugin instalacija;
- parser koji koristi samo ugovor i pomoćne funkcije već dostupne u Deklarant Pro.

---

## 4. Osnovni princip: univerzalna inteligencija, poseban izlaz

Parser Studio treba imati zajednički engine koji prepoznaje obrasce prisutne u različitim fakturama. Međutim, rezultat njegove analize mora biti poseban parser za konkretnog dobavljača.

To znači:

- univerzalna logika postoji u Parser Studiju;
- vendor-specifična pravila automatski se otkrivaju;
- ta pravila se kompajliraju u zaseban `.py` fajl;
- generisani parser ne zavisi od Parser Studija.

Ovo uklanja lažnu dilemu između „jednog univerzalnog parsera“ i „posebnog parsera po dobavljaču“.

Ispravan model je:

> **zajednički generator + automatski otkriven vendor model + samostalni generisani parser.**

---

## 5. Važna korekcija originalne ideje

Originalna ideja opravdano odbacuje ručno kreirane profile. Ipak, ne treba odbaciti svaki oblik vendor-specifičnog modela.

Treba razlikovati:

### Pogrešan profil

- korisnik ručno bira engine;
- mapira kolone;
- crta granice;
- gradi boolean pravila;
- uređuje JSON polje po polje.

### Ispravan interni model

- Parser Studio ga automatski izvodi iz više uzoraka;
- korisnik ga ne mora razumjeti niti ručno uređivati;
- sadrži stabilna sidra, kolone, regexe, varijante rasporeda i fallback pravila;
- služi kao ulaz u generator Python koda.

Interni model može se zvati, na primjer, `VendorParserModel`, ali on nije konačni proizvod niti runtime zavisnost.

---

## 6. Predložena arhitektura Parser Studija

### 6.1. Contract sloj

Zadržati postojeći `contract/` sloj sa kopijama:

- `InvoiceLine`;
- `Party`;
- `ImportResult`;
- `ImportStrategy`;
- pravilima za provjeru drift-a u odnosu na Deklarant Pro.

Ovaj sloj je granica kompatibilnosti. Parser Studio mora znati kakav izlaz Deklarant Pro očekuje, ali ne smije zavisiti od instalacije Deklarant Pro aplikacije u runtimeu.

Preporuka je da contract sloj ima:

- verziju ugovora;
- automatski `drift_check`;
- skup obaveznih i opcionih polja;
- test koji učitava generisani parser protiv trenutne verzije ugovora.

### 6.2. Document ingestion sloj

Jedinstveni ulazni model treba biti `DocumentBundle`, ne samo jedan fajl.

Primjer paketa:

- PDF faktura;
- Excel sa stavkama;
- packing-list sa težinama;
- dodatna stranica ili specifikacija.

`DocumentBundle` treba znati:

- koji fajlovi pripadaju istom poslu;
- koji tip dokumenta predstavlja svaki fajl;
- koji izvor je autoritativan za određeno polje;
- koji fajlovi su potrošeni;
- gdje postoje konflikti.

Ovaj model direktno podržava ispravno generisanje `consumed_paths`.

### 6.3. Unificirani dokumenti

Postojeći `ExcelDocument` treba zadržati i proširiti.

Predloženi osnovni objekti:

- `PdfDocument` — stranice, tekst, riječi, koordinate, linije, slike;
- `ExcelDocument` — sheetovi, redovi, ćelije, formule i prikazane vrijednosti;
- `TextDocument` — normalizovan tekstualni prikaz;
- `DocumentBundle` — veza više izvora.

PDF sloj treba sačuvati i tekst i geometriju. Sam tekst nije dovoljan za pouzdano prepoznavanje kolona.

### 6.4. Candidate extraction engine

Prepoznavač ne treba odmah proizvesti samo jednu vrijednost. Više ekstraktora treba paralelno predlagati kandidate.

Primjeri ekstraktora:

- labela + tekst desno;
- labela + blok ispod;
- Excel header;
- PDF geometrija kolone;
- regex oblika vrijednosti;
- analiza sadržaja kolone;
- tabela pronađena linijama;
- tabela pronađena grupisanjem riječi;
- prepoznavanje prema odnosu susjednih kolona.

Svaki kandidat mora nositi dokaz kako je nastao.

### 6.5. Provenance i radni model

`ImportResult` ne treba koristiti kao glavni interni model tokom analize. On ne može dovoljno dobro predstaviti alternative, konflikte, koordinate i razloge izbora.

Predloženi modeli:

```python
ExtractedValue:
    field_name
    raw_value
    normalized_value
    source_path
    page_or_sheet
    row_or_bounding_box
    extractor_id
    evidence
    confidence_level
    validation_issues
    alternatives
```

```python
ExtractionDraft:
    parties
    invoice_metadata
    line_items
    totals
    weights
    origin_statements
    conflicts
    unresolved_fields
```

Tek nakon pregleda, validacije i potvrde `ExtractionDraft` se pretvara u očekivani `ImportResult`.

### 6.6. Resolver i validacioni engine

Resolver bira između kandidata koristeći više dokaza, ne samo jedan regex.

Primjeri kombinovanih dokaza:

- header liči na `Quantity`;
- vrijednosti su pozitivni brojevi;
- susjedna kolona sadrži poznate jedinice mjere;
- količina × cijena približno odgovara ukupnom iznosu reda;
- suma stavki odgovara totalu fakture;
- tarifni broj ima validan oblik;
- ISO zemlja odgovara poznatoj šifri.

Validacije treba podijeliti na:

- sintaksne;
- strukturne;
- aritmetičke;
- domenske;
- međudokumentne.

Sistem ne treba prikazivati lažne precizne procente pouzdanosti dok za njih nema izmjeren kalibracioni model. Bolje su kategorije:

- **visoka pouzdanost**;
- **potrebna provjera**;
- **neriješeno**.

Uz svaku kategoriju treba prikazati razloge.

### 6.7. Structure inference

Na osnovu najmanje nekoliko uzoraka istog dobavljača Parser Studio treba zaključiti:

- stabilna obilježja dokumenta;
- pravila `detect_*` funkcije;
- početak i kraj tabele;
- identitet kolona;
- višeredne opise;
- nastavak tabele na novoj stranici;
- subtotal i total redove;
- alternativne verzije rasporeda;
- prioritete PDF/Excel izvora;
- fallback ponašanje.

Jedan uzorak je često nedovoljan. Za ozbiljan parser preporučljivo je najmanje:

- 3 različita dokumenta za osnovnu strukturu;
- barem jedan višestranični dokument ako postoji;
- barem jedan primjer sa nedostajućim opcionim poljem;
- primjeri različitih brojeva stavki;
- po mogućnosti jedan noviji i jedan stariji raspored.

### 6.8. VendorParserModel

Interni model može sadržavati:

```text
VendorParserModel
├── metadata
├── detection_rules
├── document_bundle_rules
├── party_rules
├── table_rules
├── column_rules
├── line_continuation_rules
├── totals_rules
├── weight_rules
├── origin_rules
├── incoterm_rules
├── normalization_rules
├── supported_variants
└── fallback_rules
```

Korisnik ga ne uređuje kao konfiguraciju. On je interni rezultat analize i ulaz u generator.

---

## 7. Generisanje Python parsera

### 7.1. Osnovni zahtjev

Generisani parser mora biti:

- samostalan u okviru postojećeg Deklarant Pro API-ja;
- čitljiv programeru;
- deterministički;
- testabilan;
- bez runtime zavisnosti od Parser Studija;
- bez `eval`, dinamičkog učitavanja proizvoljnog koda i skrivenog DSL-a;
- dovoljno robustan na manje promjene rasporeda.

### 7.2. Dozvoljene zavisnosti

Parser može uvoziti samo:

- Python standardnu biblioteku;
- biblioteke koje Deklarant Pro već garantovano distribuira;
- postojeće ugovore i pomoćne funkcije Deklarant Pro koje koriste i ručno pisani parseri.

Ne smije sadržavati:

```python
from parser_studio import ...
```

niti bilo koju sličnu zavisnost.

### 7.3. Način generisanja

Ne preporučuje se slobodno spajanje velikih stringova Python koda. Bolje je koristiti:

1. provjerene šablone funkcija;
2. parametrizovane blokove pravila;
3. Python AST provjeru;
4. automatsko formatiranje;
5. statičku provjeru prije izvršavanja.

Generator može koristiti Jinja2 ili sličan template sistem, ali izlaz mora proći:

- `ast.parse()`;
- `compile()`;
- formatter;
- lint provjere;
- provjeru zabranjenih importa;
- testove ugovora.

### 7.4. Preporučena struktura generisanog fajla

```text
- metadata konstante
- detect_* funkcija
- glavna parse_* funkcija
- čitanje dokumenta
- ekstrakcija stranaka
- ekstrakcija stavki
- ekstrakcija ukupnih težina i totalnih vrijednosti
- normalizacija
- fallback funkcije
- finalno kreiranje ImportResult
```

Dodatne metadata konstante mogu biti korisne:

```python
PARSER_ID = "imamoglu_invoice"
PARSER_VERSION = "1.2.0"
GENERATOR_VERSION = "0.4.0"
CONTRACT_VERSION = "1"
SUPPORTED_VARIANTS = ("layout_2024", "layout_2026")
```

Te konstante ne smiju remetiti postojeći API, ali olakšavaju praćenje verzija i dijagnostiku.

### 7.5. Čitljivost je važnija od minimalne dužine

Parser od 300–500 jasnih linija nije neuspjeh. Ne treba težiti vještački kratkom kodu ako bi on postao neproziran.

Generisani kod treba:

- imati stabilna imena funkcija;
- imati kratke komentare gdje pravilo nije očigledno;
- jasno odvojiti detekciju, ekstrakciju i normalizaciju;
- biti moguće ručno popraviti ako se ikada pojavi hitan slučaj.

---

## 8. Obavezna verifikacija generisanog parsera

Najvažniji princip je:

> **Ne testira se samo interni engine Parser Studija. Mora se testirati upravo generisani `.py` fajl.**

Tok:

```text
Uzorci
  ↓
Interna analiza
  ↓
Potvrđeni ExtractionDraft / očekivani rezultat
  ↓
VendorParserModel
  ↓
Generisani .py parser
  ↓
Učitavanje parsera u izolovanom procesu
  ↓
Pokretanje nad svim uzorcima
  ↓
Poređenje sa očekivanim rezultatima
  ↓
Izvoz samo ako je rezultat prihvatljiv
```

### 8.1. Sandbox izvršavanje

Generisani Python kod treba testirati u odvojenom procesu sa:

- vremenskim ograničenjem;
- ograničenim radnim direktorijumom;
- kontrolisanim ulaznim fajlovima;
- zabranom mrežnog pristupa;
- zapisom stdout/stderr izlaza;
- jasnim hvatanjem izuzetaka.

Iako generator proizvodi kod iz poznatih šablona, izolovano izvršavanje je dobra sigurnosna i stabilnosna mjera.

### 8.2. Pozitivni testovi

Parser mora ispravno obraditi sve potvrđene uzorke tog dobavljača.

Provjeravati najmanje:

- broj stavki;
- nazive robe;
- količine;
- cijene i valutu;
- tarifne brojeve kada postoje;
- zemlje porijekla;
- exporter/importer;
- bruto/neto težine;
- Incoterm;
- izjavu o porijeklu;
- `consumed_paths`;
- ponašanje kada opciono polje ne postoji.

### 8.3. Negativni testovi za `detect_*`

Ovo je posebno važno: `detect_*` ne smije samo prepoznati svog dobavljača, nego mora odbiti dokumente drugih dobavljača.

Za svaki novi parser treba pokrenuti:

- pozitivne uzorke svog dobavljača;
- uzorke svih postojećih dobavljača;
- generičke PDF/Excel dokumente koji nisu fakture;
- dokumente sa sličnim nazivom ili kolonama.

Time se sprečava da novi parser postane previše širok i presretne fajlove namijenjene drugom parseru.

### 8.4. Aritmetičke i domenske kontrole

Primjeri:

- suma stavki približno odgovara ukupnom iznosu;
- količina × jedinična cijena odgovara vrijednosti reda gdje je primjenjivo;
- neto masa nije veća od bruto mase bez upozorenja;
- tarifni broj je normalizovan na očekivani oblik;
- mase se ne zaokružuju na dvije decimale;
- isti red nije dupliran nakon spajanja PDF-a i Excela;
- valuta je konzistentna ili je konflikt eksplicitno prikazan.

---

## 9. Korišćenje postojećih 13 parsera kao oracle-a

Postojeći ručno pisani parseri predstavljaju najvredniji početni skup znanja.

Preporučeni postupak:

1. prikupiti reprezentativne uzorke za svaki postojeći parser;
2. pokrenuti ručno pisani parser i sačuvati njegov izlaz;
3. isti uzorak dati Parser Studiju;
4. pokušati generisati novi parser bez ručnog kodiranja;
5. uporediti izlaze polje po polje;
6. evidentirati šta univerzalni engine još ne razumije;
7. proširiti zajedničku logiku samo tamo gdje je problem zaista opšti.

Ovaj proces ima dvije koristi:

- mjeri koliko je Parser Studio stvarno sposoban;
- omogućava razvoj bez čekanja novih dobavljača.

Postojeći parser nije uvijek nepogrešiv. Zato njegov izlaz treba tretirati kao početni oracle koji korisnik može potvrditi ili korigovati, a ne kao apsolutnu istinu.

---

## 10. Pravila korekcije i učenja

Svaka korekcija korisnika ne smije automatski postati globalno pravilo.

Treba razlikovati tri nivoa:

### 10.1. Korekcija dokumenta

Primjer: OCR je pročitao `O` umjesto `0`.

- mijenja samo očekivani rezultat tog uzorka;
- ne mijenja vendor model;
- ne mijenja zajednički engine.

### 10.2. Korekcija vendor modela

Primjer: kolona `Menşei` na dokumentima ovog dobavljača znači zemlja porijekla.

- dopunjava model konkretnog parsera;
- utiče na buduće dokumente tog dobavljača;
- može kasnije postati globalno pravilo ako se potvrdi na drugim dobavljačima.

### 10.3. Globalno unapređenje Parser Studija

Primjer: turski izraz `Menşei` je opšti sinonim za porijeklo i pojavljuje se kod više dobavljača.

- dodaje se zajedničkoj biblioteci koncepata;
- pokreću se svi regresioni testovi;
- promjena se prihvata samo ako ne izazove nove konflikte.

Ovo sprečava da zajednički engine postane skup izuzetaka za pojedinačne dobavljače.

---

## 11. Prikaz originala i rezultata

Desktop GUI ima smisla jer je vizuelno poređenje centralna funkcija i korisnik nije programer.

Preporučeni glavni ekran nije wizard, nego radni prostor sa tri dijela:

1. **Originalni dokument**  
   PDF stranica ili Excel sheet.

2. **Izvučeni rezultat**  
   Stranke, zaglavlje fakture, tabela stavki, težine, porijeklo i upozorenja.

3. **Dokazi i problemi**  
   Izvor označene vrijednosti, pravilo koje ju je pronašlo, alternative i validacioni problemi.

Interakcija treba biti kružna:

```text
analiziraj → pregledaj → ispravi → ponovo generiši → testiraj
```

Ne treba koristiti deset ekrana i dugme „Dalje“.

### 11.1. Vizuelno povezivanje

Klik na vrijednost u rezultatu treba:

- označiti odgovarajuću ćeliju u Excelu;
- označiti bounding box u PDF-u;
- prikazati sirovi tekst;
- prikazati extractor i razlog izbora.

Klik na dio originala treba prikazati koje je vrijednosti Parser Studio iz njega izveo.

### 11.2. Ispravke

Korisnik treba moći:

- promijeniti vrijednost;
- označiti pogrešnu kolonu;
- povezati nedostajuće polje sa dijelom dokumenta;
- reći da podatak ne postoji;
- označiti konflikt za kasniju odluku.

To nije ručno programiranje parsera. To je davanje tačnog očekivanog rezultata iz kojeg Studio zaključuje pravilo.

---

## 12. Drift i verzije faktura

Isti dobavljač može promijeniti dizajn fakture. Parser ne treba odmah ručno zakrpiti niti tiho nastaviti sa slabim rezultatom.

Preporučeni model:

- jedan parser može podržavati više prepoznatih varijanti rasporeda;
- svaka varijanta ima svoj fingerprint i pravila;
- semantička sidra imaju prednost nad apsolutnim koordinatama;
- koordinate se koriste kao dodatni dokaz, ne kao jedina osnova;
- generički fallback pokušava oporavak;
- kada pouzdanost padne, parser vraća kontrolisan problem ili zahtjev za pregled;
- nova potvrđena varijanta proizvodi novu verziju parsera.

Verzionisanje parsera treba biti semantičko gdje je praktično:

- patch — ispravka bez promjene podržanog formata;
- minor — nova varijanta dokumenta ili proširenje;
- major — promjena ugovora ili ponašanja koja zahtijeva novu verziju Deklarant Pro.

---

## 13. AI eskalacija bez obavezne integracije

Prva verzija ne treba imati živu LLM integraciju.

Dugme **„Pripremi dijagnostički paket“** može izvesti ZIP/folder sa:

- uzorkom ili anonimizovanom kopijom;
- izvučenim tekstom;
- riječima i koordinatama;
- kandidatskim vrijednostima;
- izabranim i odbačenim kandidatima;
- rezultatima validacija;
- korisnički potvrđenim očekivanim rezultatom;
- internim vendor modelom;
- generisanim parserom;
- logom neuspjelog testa;
- verzijama Parser Studija i contract-a;
- automatski generisanim Markdown opisom problema.

Takav paket se može predati Codexu, Claude Codeu ili drugom agentu bez ručnog prepričavanja.

Kasnija direktna integracija ima smisla tek kada je format dijagnostičkog paketa stabilan. U suprotnom bi se rano vezali za određenog provajdera ili API.

---

## 14. Privatnost i regresiona biblioteka

Stvarni poslovni dokumenti ne smiju automatski ići u Git niti u dijeljene sisteme.

Preporučena podjela:

### Lokalno, van Git-a

- originalne fakture;
- PDF/Excel uzorci;
- osjetljivi podaci;
- puna dijagnostika;
- lokalni indeks uzoraka.

### Dozvoljeno u Git-u

- sintetički fixture-i;
- anonimizovani tekstualni uzorci;
- očekivani rezultati bez poslovnih podataka;
- testovi;
- globalne liste sinonima;
- šabloni generatora;
- kod Parser Studija.

Svaki lokalni uzorak može imati:

- interni ID;
- SHA-256 hash;
- dobavljača;
- datum dodavanja;
- varijantu rasporeda;
- status odobrenja;
- verziju parsera koja ga podržava.

Anonimizacija mora biti eksplicitna i provjerena. Jednostavna zamjena naziva firme nije uvijek dovoljna jer dokument može sadržavati adrese, poreske brojeve, telefone, brojeve računa i komercijalne cijene.

---

## 15. Plugin i distribucija u Deklarant Pro

### Faza razvoja

Za prototip je prihvatljivo:

- ručno kopiranje parsera u `importers/vendors/<dobavljač>/`;
- ručna registracija u postojećem toku;
- direktno pokretanje ugovornih testova.

### Proizvodna distribucija

Prije šire distribucije preporučljivo je oživjeti postojeći plugin/potpisivanje sistem u Deklarant Pro kako bi se dobilo:

- instaliranje parsera bez izmjene core koda;
- identitet i verzija parsera;
- provjera potpisa;
- minimalna podržana verzija Deklarant Pro;
- rollback;
- sprečavanje neovlaštenog ili izmijenjenog koda.

Parser Studio može već u ranoj fazi generisati parser spreman za budući plugin format, ali to ne treba blokirati MVP.

---

## 16. Jezici i sinonimi

Ne treba odmah praviti ogroman rječnik svih mogućih jezika.

Prioritet treba izvesti iz stvarnih dokumenata:

1. engleski;
2. srpski/hrvatski/bosanski;
3. njemački izrazi koji se već pojavljuju;
4. turski izrazi iz stvarnih Imamoglu uzoraka;
5. drugi jezici tek kada postoji konkretan slučaj.

Svaka oznaka treba biti vezana za koncept, kontekst i moguće konflikte. Na primjer, riječ `Origin` sama po sebi nije dovoljno jaka jer može označavati više stvari.

Biblioteka sinonima zato ne treba biti samo:

```text
origin = [Origin, Country of origin, Menşei]
```

nego treba podržavati:

- jezik;
- očekivani tip vrijednosti;
- prostorni odnos;
- prioritet;
- negativni kontekst;
- polje dokumenta u kojem se očekuje.

---

## 17. Podaci koje sistem ne smije nagađati

Za carinske podatke kontrolisani neuspjeh je bolji od uvjerljivo pogrešnog rezultata.

Pravila:

- ako tarifa ne postoji u dokumentu, rezultat je `nije pronađena`;
- Parser Studio ne određuje tarifni broj na osnovu opisa robe;
- ne poistovjećuje zemlju izvoza i zemlju porijekla;
- ne smatra automatski `Buyer`, `Bill to`, `Ship to` i `Consignee` istom stranom;
- čuva originalni tekst izjave o porijeklu i njegovu lokaciju;
- ne skriva konflikt između PDF-a i Excela;
- ne zaokružuje mase na dvije decimale;
- ne popunjava prazna pravno značajna polja pretpostavkom.

---

## 18. Predloženi redoslijed razvoja

### Faza 0 — inventar i ugovor

- pregledati svih 13 postojećih parsera;
- klasifikovati tipove dokumenata i ponavljajuće obrasce;
- definisati obavezni parser API;
- stabilizovati `contract/` i drift test;
- napraviti katalog stvarnih funkcija koje generator smije koristiti.

**Rezultat:** precizan ugovor i mapa problema.

### Faza 1 — headless analiza

- završiti `ExcelDocument`;
- napraviti `PdfDocument`;
- uvesti `DocumentBundle`;
- napraviti provenance model;
- implementirati prve ekstraktore kandidata;
- dodati postojeće brojčane i tarifne utility funkcije.

**Rezultat:** JSON/Markdown izvještaj analize bez GUI-ja.

### Faza 2 — resolver i validacije

- razviti resolver kandidata;
- dodati aritmetičke i domenske provjere;
- uvesti konflikte i neriješena polja;
- napraviti konverziju u `ExtractionDraft`.

**Rezultat:** pouzdana analiza nekoliko postojećih dobavljača.

### Faza 3 — vendor model i generator

- definisati `VendorParserModel`;
- napraviti generator iz provjerenih šablona;
- uvesti AST, compile, formatter i import provjere;
- generisati prvi samostalni `.py` parser.

**Rezultat:** parser koji ne zavisi od Parser Studija.

### Faza 4 — generated-parser verifier

- izvršavati parser u izolovanom procesu;
- porediti sa potvrđenim očekivanim rezultatima;
- dodati pozitivne i negativne `detect_*` testove;
- napraviti izvještaj razlika polje po polje.

**Rezultat:** kontrolisan quality gate prije izvoza.

### Faza 5 — HTML pregled

- prikaz PDF/Excel izvora;
- prikaz ekstrakcije i dokaza;
- isticanje razlika i konflikata.

**Rezultat:** brzo provjeravanje arhitekture interakcije prije punog GUI-ja.

### Faza 6 — PySide6 radni prostor

- original naspram rezultata;
- povezano označavanje izvora;
- uređivanje očekivanih vrijednosti;
- ponovna analiza i generisanje;
- izvoz parsera i dijagnostičkog paketa.

**Rezultat:** funkcionalni Parser Studio MVP.

### Faza 7 — proširenje i distribucija

- podrška za više varijanti fakture;
- OCR samo ako stvarni uzorci pokažu potrebu;
- povezivanje plugin sistema Deklarant Pro;
- potpisivanje, verzionisanje i rollback;
- opcionalna AI integracija.

---

## 19. MVP obim

MVP ne treba pokušati riješiti svaki PDF i svaki jezik.

Preporučeni MVP:

- Excel sa prepoznatljivim header redom;
- tekstualni PDF sa tabelom ili stabilnim kolonama;
- jedan ili dva dokumenta u `DocumentBundle` paketu;
- engleske i BHS labele;
- stranke, stavke, tarifa, porijeklo, količina, cijena, valuta, težine i Incoterm;
- generisanje parsera za 2–3 postojeća dobavljača;
- izvršavanje i testiranje generisanog parsera;
- HTML ili jednostavan PySide6 pregled;
- lokalna regresiona biblioteka.

Namjerno odložiti:

- složen OCR;
- fotografije faktura;
- direktan LLM API;
- automatsko određivanje tarifnog broja;
- potpuni plugin marketplace;
- desetine jezika;
- korisničko ručno crtanje pravila.

---

## 20. Kriterijumi uspjeha

Parser Studio MVP je uspješan ako može:

1. iz uzoraka najmanje 2–3 postojeća dobavljača generisati samostalne parsere;
2. proizvesti isti ili korisnički potvrđen izlaz kao postojeći ručni parseri;
3. proći sve pozitivne testove uzoraka;
4. ne presretati fakture drugih dobavljača kroz `detect_*`;
5. dati tačan izvor svake ključne vrijednosti;
6. pokazati neriješene i konfliktne podatke bez nagađanja;
7. generisati čitljiv kod koji programer može pregledati;
8. ponoviti isti izlaz iz istih uzoraka i iste verzije engine-a;
9. skratiti vrijeme izrade parsera bez povećanja rizika u svakodnevnom radu.

Ne treba mjeriti samo procenat automatski popunjenih polja. Važnije metrike su:

- tačnost stavki;
- broj lažno prihvaćenih dokumenata;
- broj ručnih intervencija;
- vrijeme do gotovog parsera;
- broj regresija na prethodnim parserima;
- stabilnost nakon promjene rasporeda.

---

## 21. Najveći rizici

### 21.1. Preširoka globalna pravila

Popravka za jednog dobavljača može pokvariti druge.

**Odbrana:** tri nivoa korekcije, regresioni testovi i vendor model.

### 21.2. Previše oslanjanja na koordinate

Mala promjena layouta ruši parser.

**Odbrana:** semantička sidra + geometrija + sadržaj + fallback.

### 21.3. Lažno uspješan `detect_*`

Parser presretne dokument drugog dobavljača.

**Odbrana:** obavezni negativni corpus testovi.

### 21.4. Razlika internog engine-a i generisanog koda

Studio prikazuje tačan rezultat, ali `.py` parser radi drugačije.

**Odbrana:** obavezno izvršavanje generisanog fajla nad svim uzorcima.

### 21.5. Preuranjen GUI

Mnogo vremena ode na interfejs prije nego što engine radi.

**Odbrana:** headless engine i HTML pregled prije punog PySide6 UI-ja.

### 21.6. Preuranjena AI integracija

Sistem postane vezan za provajdera prije stabilnog procesa.

**Odbrana:** prvo standardizovan dijagnostički paket.

### 21.7. Povjerljivi podaci u testovima

Fakture završe u Git-u ili eksternom servisu.

**Odbrana:** lokalni storage, hash indeks, eksplicitna anonimizacija i jasna pravila izvoza.

---

## 22. Konačna arhitektonska preporuka

Parser Studio ne treba graditi kao:

- univerzalni runtime parser za Deklarant Pro;
- wizard za ručno konfigurisanje;
- alat koji generiše proizvoljni LLM kod;
- skup sve većih globalnih regex pravila;
- sistem koji nagađa pravno značajne podatke.

Treba ga graditi kao:

> **samostalni deterministički razvojni alat koji iz više uzoraka fakture izvodi objašnjiv vendor model, omogućava čovjeku da potvrdi očekivani rezultat, kompajlira taj model u čitljiv i samostalan `.py` parser kompatibilan sa postojećim Deklarant Pro ugovorom, a zatim testira upravo taj generisani parser nad pozitivnim i negativnim corpusom prije izvoza.**

Najvažniji praktični princip cijelog projekta je:

> **Parser Studio treba da automatizuje nastanak vendor-specifičnog koda, a ne da pokušava ukinuti potrebu da konačni parser bude vendor-specifičan.**

Takva arhitektura čuva jednostavnost za korisnika, odvojenost aplikacija, kompatibilnost sa postojećim Deklarant Pro sistemom i mogućnost dugoročnog unapređivanja bez stvaranja krhkog univerzalnog parsera.

---

## 23. Kratka lista odluka za dalji rad

- [x] Parser Studio je potpuno odvojena aplikacija.
- [x] Krajnji izlaz je samostalan `.py` parser.
- [x] Nema runtime zavisnosti od Parser Studija.
- [x] Korisnik ne gradi ručni profil ni wizard pravila.
- [x] Interni vendor model je dozvoljen i automatski se izvodi.
- [x] `ImportResult` je završni contract, ne radni model analize.
- [x] Svaka vrijednost mora imati provenance.
- [x] Generisani parser se mora stvarno izvršiti i testirati.
- [x] `detect_*` se testira i protiv drugih dobavljača.
- [x] Postojećih 13 parsera koristi se kao početni oracle i corpus.
- [x] Globalna, vendor i dokument korekcija moraju biti razdvojene.
- [x] AI integracija nije uslov za MVP.
- [x] Prvo engine i verifier, zatim puni GUI.
- [ ] Precizno zaključati contract generisanog parsera.
- [ ] Napraviti inventar svih 13 parsera i uzoraka.
- [ ] Izabrati prva 2–3 parsera za pilot regeneraciju.
- [ ] Odlučiti kada oživjeti plugin/potpisivanje sistem.

