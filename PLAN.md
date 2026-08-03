# Parser Studio — plan (v2, nakon razgovora o domenu)

> Ovaj dokument zamjenjuje raniju verziju plana koja je pogrešno pošla u pravcu
> wizard-a sa ručnim mapiranjem kolona po dobavljaču. Ovdje je zapisano ono što
> je proizašlo iz razgovora sa vlasnikom projekta — cilj je da se ovaj dokument
> pokaže drugom modelu (ChatGPT) za drugo mišljenje, pa da se iz oba pogleda
> izvuče najbolje rješenje.

## 1. Kontekst — zašto ovo uopšte postoji

**Deklarant Pro** je desktop aplikacija (PySide6) za carinsko posredovanje —
uvozi fakture (PDF/Excel) od raznih dobavljača, izvlači stavke robe, popunjava
carinsku deklaraciju (ASYCUDA XML). Trenutno ima **~13 ručno pisanih parsera**
po dobavljaču (`importers/vendors/blagic/`, `importers/vendors/medicopharm/`,
`importers/vendors/imamoglu/`, itd.), prosjek ~500 linija koda po parseru.

**Problem:** svaki NOVI dobavljač trenutno zahtijeva da programer sjedne i
ručno napiše novi parser — pročita PDF/Excel strukturu, napiše regex-e ili
koordinate kolona, testira. To je usko grlo.

**Vlasnik projekta** (carinski deklarant, ne programer) želi alat koji taj
posao radi umjesto njega — ili bar najveći dio njega — **bez LLM API-ja**
(eksplicitan zahtjev: ne želi zavisnost od eksternog modela, i trenutno ne
može pokretati lokalni LLM). Kad alat sam ne uspije, uskače programer/AI
asistent — ali kao POMOĆ generičkoj logici, ne kao zamjena za nju.

## 2. Ključni uvid iz razgovora (ovo je srž plana)

Sve fakture, bez obzira na dobavljača, sadrže **skoro identičan skup
podataka** — samo drugačije raspoređen na stranici:

- ko šalje (izvoznik/pošiljalac)
- ko prima (uvoznik/primalac)
- nazivi robe
- tarifni brojevi (ako ih faktura uopšte sadrži)
- da li postoji izjava o porijeklu robe
- zemlja porijekla
- količine, cijene, valuta, težine (bruto/neto)

**Zato ne treba da postoji poseban "profil" koji korisnik ručno gradi za
svakog dobavljača.** Umjesto toga: **jedan zajednički, generički
"prepoznavač"** koji zna šta uobičajeno traži u bilo kom PDF-u ili Excel-u, i
sam to pokuša da nađe — bez ijednog koraka gdje korisnik ručno mapira kolonu
ili povlači granicu mišem.

Kad taj prepoznavač na novom dobavljaču nešto ne nađe ili pogrešno prepozna,
**to nije razlog da se piše poseban parser za tog dobavljača** — to je signal
da se **dopuni ZAJEDNIČKA logika** (dodaj još jedan način da prepozna npr.
"Shipper:" kao izvoznika), tako da profitiraju svi budući dobavljači, ne samo
ovaj jedan.

**Ipak, krajnji isporučeni artefakt PO DOBAVLJAČU ostaje poseban `.py` fajl**
— u istom stilu kao postojeći `blagic_loren_pdf_parser.py` (funkcije
`detect_*`/`parse_*`, vraća `ImportResult`) — jer se TAJ fajl šalje klijentskoj
firmi i oni ga uvoze u svoj `deklarant_pro` da mogu raditi sa tim dobavljačem.

## 3. Radni tok (5 koraka, NE wizard)

```
1. UBACI       korisnik prevuče uzorak(e) fakture (PDF i/ili Excel) novog dobavljača
2. PREPOZNAJ   zajednički generički prepoznavač sam izvuče sve što obično traži
3. UPOREDI     alat prikaže original naspram izvučenog, jedan-na-jedan (helper za poređenje)
4. ISPRAVI     korisnik ručno ispravi sitne greške (npr. loše prepoznato slovo)
               ILI, ako je promašaj veći — eskalira se AI asistentu koji
               popravlja ZAJEDNIČKI prepoznavač (ne piše poseban kod za ovog dobavljača)
5. IZVEZI      kad je zadovoljavajuće, alat ispeče gotov `.py` parser fajl
               u stilu postojećih vendor parsera — spreman da se pošalje firmi
```

Ovo NIJE sekvenca u smislu "korak po korak čarobnjak sa dugmetom Dalje" —
koraci 3 i 4 se prirodno ponavljaju (ispravi, pogledaj ponovo, ispravi) dok
rezultat ne zadovolji.

## 4. Šta je OVIM razgovorom eksplicitno ODBAČENO

Prva verzija plana (prije ovog razgovora) je predlagala:

- ❌ Wizard sa 10 odvojenih ekrana/koraka
- ❌ Korak gdje korisnik BIRA "engine" (pdf_lineregex / pdf_words / excel_headers)
- ❌ Ručno povlačenje granica kolona mišem preko rasterizovane PDF stranice
- ❌ JSON "profil" koji korisnik ručno sastavlja polje-po-polje za svakog dobavljača
- ❌ Korak "detekcija formata" gdje korisnik gradi boolean stablo pravila

Sve ovo je pogrešno pretpostavljalo da je posao alata "pomoći korisniku da SAM
konfiguriše parser po dobavljaču" — a stvarni cilj je suprotan: **korisnik
skoro ništa ne konfiguriše, generički prepoznavač radi posao, korisnik samo
provjerava i ispravlja rezultat.**

## 5. Generički prepoznavač — šta treba da zna da traži

Ciljni podaci (isti oblik koji `deklarant_pro` već koristi —
`InvoiceLine`/`Party` iz `core/draft/draft.py`, `ImportResult` iz
`importers/import_result.py`):

| Polje | Kako se generički prepoznaje (ideja, ne konačno rješenje) |
|---|---|
| Izvoznik (exporter) | traži labele "Exporter"/"Shipper"/"Seller"/"Pošiljalac"/"Izvoznik" + tekst bloka koji slijedi (naziv firme, adresa, zemlja) |
| Uvoznik (importer) | isto, labele "Consignee"/"Buyer"/"Primalac"/"Uvoznik" |
| Naziv robe | kolona u tabeli (Excel: naziv zaglavlja; PDF: pozicija teksta) ili opis u redu stavke |
| Tarifni broj | prepoznatljiv OBLIK (6-10 cifara, često grupisano) + labele "HS Code"/"Tariff"/"Tarifna oznaka"/"CN" — **napomena: mnoge fakture NEMAJU tarifni broj uopšte, to je normalno** |
| Zemlja porijekla | ISO kod zemlje (2 slova) ili puno ime zemlje, blizu labele "Country of origin"/"Zemlja porijekla"/"Origin" |
| Izjava o porijeklu | prepoznatljive fraze ("The exporter of the products... declares that...", "Izjavljujem da...") — `deklarant_pro` VEĆ ima `OriginStatementDetector` (`services/tariff/origin_statement_detector.py`) koji ovo radi za postojeće parsere — trebalo bi ga ponovo iskoristiti, ne izmišljati iznova |
| Količina / cijena / valuta | brojevi uz jedinice mjere i valutne kodove (EUR, USD...), EU vs US format decimalnog zareza |
| Bruto/neto težina | brojevi uz "kg"/"gross"/"net"/"bruto"/"neto" |
| Paritet isporuke (Incoterm) | `deklarant_pro` VEĆ ima `detect_incoterm()` (`importers/incoterm_utils.py`) — ponovo iskoristiti |

**Bitna činjenica:** `deklarant_pro` već ima nekoliko "generičkih" komponenti
na kojima se ovo može graditi, ne kreće se od nule:

- `importers/generic_pdf_importer.py` — fallback PDF parser koji već pokušava
  da prepozna kolone po nazivu zaglavlja (`_detect_columns`) i po poziciji
  riječi na stranici kad nema prave tabele (`_parse_words_based` — uči
  pozicije kolona iz header reda umjesto da su zakucane).
- `importers/faktura_xml_parser.py` — ima čistu mapu "koncept → lista mogućih
  naziva" (`_ITEM_TAGS`), tačno onaj oblik koji generički prepoznavač treba.
- `importers/excel_column_utils.py` — `infer_origin_column()` prepoznaje
  kolonu porijekla PO SADRŽAJU ćelija kad header ne postoji.
- `importers/invoice_line_utils.py` — `parse_eu_number`, `normalize_tariff_number`,
  `KNOWN_JM` (poznate jedinice mjere) — gotovi graditeljski blokovi.

Ovaj alat (Parser Studio) bi trebalo da ove ideje **objedini i proširi** u
jedan robustan, samostalan modul — ne da ih duplira, i ne da ih zamijeni
nečim potpuno novim.

## 6. Poređenje / provjera (korak 3)

Alat mora prikazati **original naspram izvučenog, jedan-na-jedan**, da
korisnik (koji nije programer) vizuelno provjeri tačnost bez čitanja koda:

- Za PDF: prikaz stranice (ili izvučenog teksta) sa istaknutim mjestom odakle
  je svaka vrijednost pokupljena, pored tabele izvučenih stavki.
- Za Excel: originalni list pored tabele izvučenih stavki.
- Svaka izvučena vrijednost treba da "zna" odakle je došla (broj stranice/reda/
  kolone) — to je preduslov da se pregled uopšte može napraviti.

## 7. Ispravka i eskalacija (korak 4)

- **Sitna greška** (npr. loše prepoznato slovo, OCR artefakt) → korisnik
  direktno ispravi vrijednost u izlazu.
- **Veći promašaj** (polje uopšte nije prepoznato, pogrešna kolona, nova
  varijanta izjave o porijeklu koju prepoznavač ne zna) → eskalacija AI
  asistentu, koji popravlja/dopunjuje ZAJEDNIČKI prepoznavač (rječnik
  labela, novi regex obrazac, itd.), ne piše poseban kod samo za ovog
  dobavljača.

**Otvorena ideja (nije odlučeno):** mogućnost da se AI asistent pozove
DIREKTNO iz aplikacije (npr. dugme "Zatraži pomoć" koje spakuje uzorak +
šta je pokušano + gdje je zapelo u oblik koji je lako predati asistentu), da
se izbjegne ručno prepričavanje problema u posebnom razgovoru.

## 8. Izlazni artefakt — `.py` parser fajl

Fajl mora zadovoljiti postojeća pravila `deklarant_pro` aplikacije (iz
AGENTS.md i postojećeg koda):

- Vraća `ImportResult` sa `items`, `bruto_kg`, `neto_kg`
- `exporter` i `importer` popunjeni (XML lookup u aplikaciji ide po paru
  `(exporter, tariff_code)`, ne samo po tarifi)
- Ima `detect_*` funkciju za auto-detekciju formata
- `consumed_paths` popunjen ako se kombinuju dva fajla (PDF+Excel), da se
  izbjegnu duplikati stavki
- `incoterm_code` popunjen kad god se ekstraktuje pun tekst fakture
- Tarifni broj normalizovan (8 cifara bez tačaka)
- Težine NIKAD zaokružene na 2 decimale

**Otvoreno pitanje:** `deklarant_pro` ima infrastrukturu za "plugin" parsere
(`importers/plugin_loader.py`, potpisivanje preko
`services/security/parser_trust_service.py`) — ali ta infrastruktura
TRENUTNO NIJE povezana sa stvarnim tokom uvoza fajlova (provjereno u kodu:
`_register_default_strategies()` je ne registruje). Treba odlučiti: da li
generisani fajl ide kroz taj (trenutno mrtav, treba ga oživjeti) plugin/
potpisivanje sistem, ili je za sada dovoljno jednostavnije rješenje — fajl
se ručno doda u `importers/vendors/<dobavljač>/` uz malu izmjenu u
`deklarant_pro` da ga registruje.

## 9. Tehnički pristup — bez LLM-a

Cijela logika prepoznavanja treba biti **deterministička i objašnjiva**, ne
model:

- Biblioteka poznatih labela/sinonima po polju (proširenje `_ITEM_TAGS`/
  `COLUMN_MAP` obrasca iz postojećeg koda), po potrebi na više jezika
  (srpski/hrvatski/bosanski/engleski/njemački... zavisno od dobavljača).
- Prepoznavanje po OBLIKU vrijednosti (regex za tarifne brojeve, ISO kodove
  zemalja, valute, formate brojeva) kao dopuna prepoznavanju po labeli.
- Za PDF bez prave tabele (linija): pozicija riječi na stranici
  (`pdfplumber.extract_words()`), grupisanje u redove/kolone — port i
  proširenje postojećeg `_parse_words_based` pristupa.
- **Regresiona biblioteka uzoraka**: kako AI asistent dopunjava zajednički
  prepoznavač za nove slučajeve, svaki uzorak (anonimizovan/lokalno čuvan,
  NIKAD u git-u zbog poslovnih podataka) postaje trajni test — dokaz da
  popravka za jednog dobavljača nije pokvarila prepoznavanje kod prethodnih.

## 10. Šta je već urađeno (prije ovog razgovora, dijelom iskoristivo)

U dosadašnjem radu na alatu (prije nego je ovaj razgovor razjasnio pravac)
napravljeno je:

- `contract/` — vjerna kopija ciljnog oblika podataka iz `deklarant_pro`
  (`InvoiceLine`, `Party`, `ImportResult`, `ImportStrategy`) + provjera da
  kopija nije zastarjela (`drift_check.py`). **Ovo ostaje potrebno** — to je
  isti ciljni oblik i u novom pravcu.
- `ExcelDocument` — keširan, unificiran čitač `.xlsx`/`.xls`. **Ostaje
  koristan** kao osnovni sloj za čitanje Excel fajlova.
- `excel_headers` engine — rječnik sinonima naziva kolona + prepoznavanje
  header reda BEZ ručnog mapiranja. **Sama logika prepoznavanja je
  ispravnog oblika** (generička, radi sama) — ono što otpada je ideja da se
  ovo poziva kroz "wizard korak", umjesto kao dio jednog zajedničkog
  prepoznavača koji se pokreće automatski.

Ono što treba **odbaciti/preraditi**: čitav plan wizard ekrana (10 koraka),
"profil" kao JSON koji korisnik ručno gradi, "izbor engine-a" kao korisnička
odluka.

## 11. Otvorena pitanja (za drugo mišljenje / dalju diskusiju)

1. Da li generisani `.py` fajl mora proći kroz postojeći plugin/potpisivanje
   sistem u `deklarant_pro` (zahtijeva da neko oživi tu infrastrukturu), ili
   je za početak dovoljno jednostavnije: ručno kopiranje u
   `importers/vendors/`?
2. Kako konkretno treba da izgleda "pozovi AI asistenta direktno iz
   aplikacije" — izvoz konteksta u fajl/paket koji se lako preda, ili nešto
   ambicioznije (npr. živa integracija)?
3. Da li je alatu uopšte potreban desktop GUI (PySide6), ili bi jednostavniji
   CLI/skripta + HTML izvještaj za pregled bili dovoljni s obzirom da je
   glavna interakcija "ubaci fajl → pregledaj tabelu → ispravi"? (Ranija
   verzija plana je pretpostavila GUI kao samorazumljivo — vrijedi preispitati.)
4. Šta se dešava kad ISTI dobavljač kasnije malo promijeni raspored fakture
   (drift) — da li se `.py` fajl ponovo generiše iz prepoznavača, ili se
   ručno zakrpi? Da li generisani fajl treba da ima "meki" fallback (npr.
   sidra iz naziva kolone umjesto fiksne pozicije) da preživi sitan drift?
5. Koliko jezika/varijanti labela realno treba pokriti u prvoj verziji
   (srpski/hrvatski/bosanski, engleski, njemački, turski — Imamoglu je
   turski dobavljač) — da li krenuti uže pa širiti, ili odmah široko?
6. Da li se biblioteka uzoraka (za regresiono testiranje prepoznavača) čuva
   lokalno kod deklaranta, ili treba neki dijeljeni mehanizam (a da se pritom
   NIKAD ne prekrši pravilo da stvarni poslovni podaci ne idu u git/dijeljene
   sisteme bez izričite dozvole)?

## 12. Sažetak za brzo čitanje

**Nije:** wizard gdje korisnik ručno konfiguriše parser po dobavljaču.

**Jeste:** jedan zajednički, sve pametniji "prepoznavač" koji sam nalazi
uobičajene podatke fakture (ko šalje, ko prima, roba, tarifa, porijeklo) u
bilo kom PDF-u ili Excel-u; korisnik pregleda rezultat naspram originala i
sitno ga ispravi; kad prepoznavač promaši nešto veće, AI asistent ga
dopunjuje (za sve buduće dobavljače, ne samo ovog); na kraju se za tog
KONKRETNOG dobavljača ispeče gotov `.py` parser fajl u postojećem stilu
`deklarant_pro` aplikacije, spreman da se pošalje firmi.
