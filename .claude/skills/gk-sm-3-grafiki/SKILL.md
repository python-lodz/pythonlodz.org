---
name: gk-sm-3-grafiki
description: >
  Faza 3 promocji meetupu Python Łódź — grafiki do postów przez
  HTML+CSS → puppeteer → PNG. Użyj po zaakceptowanych tekstach lub do poprawy
  grafik: "grafiki do postów", "zrób grafiki", "popraw grafikę do #NN",
  "kreacje social media". Czyta social/posts.md, pisze social/images/final/.
  Trzeci skill sekwencji gk-sm-*.
---

# gk-sm-3-grafiki — grafiki postów (faza 3)

Produkuje grafiki brandowe przez `tools/social/render.mjs` (HTML+CSS →
puppeteer → PNG). **Tekst zawsze warstwą HTML** (nigdy wypalony w tle) —
łatwa iteracja i pełna kontrola typografii.

**Kontrakt z procesem:** faza 3. Wejście: `social/posts.md` (+ brief).
Wyjście: `social/images/final/*.png`. Następny: **gk-sm-4-harmonogram**.

## Produkcja

1. Szablony: `tools/social/templates/*.html` (start: `announcement.html`).
   Nowy typ posta ⇒ nowy szablon w tym katalogu (commitowany — rośnie biblioteka).
2. Job JSON + render:
   ```bash
   node tools/social/render.mjs job.json
   # job: template, name, outDir, formats ["4x5","1x1","16x9"], fields, background?
   ```
   Formaty z jednego szablonu; podstawowy format postów to **4:5**.
   (Pierwsze użycie na maszynie: `npm install --prefix tools/social`.)
3. Tła: stock (Pexels/Unsplash) → zapisz źródłowy plik w `social/images/stock/`
   z notką pochodzenia (`social/images/stock/README.md`: plik → URL źródła,
   licencja) — albo własne zdjęcia/assety z repo.
4. Brand (wymusza szablon): granat `#001F3F`, żółty `#FFD700`,
   logo `page/assets/images/logo.png`, fonty OpenSans z `page/assets/fonts/`.

## Reguły czytelności (z dumtek — odrzucaj, co ich nie spełnia)

- **Data i miejsce NA grafice** — nie licz, że ktoś doczyta w tekście.
- Wysoki kontrast napis/tło; czcionka czytelna na telefonie (podgląd w 25%).
- Mało tekstu: kicker + hasło + data/miejsce. Ściana tekstu = antywzorzec.
- Zbyt „ładne"/artystyczne kosztem czytelności = antywzorzec.

## Model współpracy (obowiązuje)

- Pokazuj obrazy, nie opisy hexów. Do akceptacji renderuj **mockup w feedzie**:
  ```bash
  node tools/social/mockup.mjs <grafika.png> <plik-z-tekstem-posta> <mockup.png>
  ```
- 2–3 kontrastowe warianty dla grafik kluczowych → reakcja per wariant →
  synteza → **jawna akceptacja zestawu**.
- Zaakceptowane → `social/images/final/<post-id>-<format>.png` (nazwa pliku
  = id posta z posts.md + format). Odrzucone + źródłowe job JSON →
  `social/images/archive/`.

## Feedback loop (obowiązuje)

- **Na starcie fazy**: przeczytaj `tasks/feedback.md` i zastosuj wpisy ze statusem
  `nowy` dotyczące tej fazy, zanim cokolwiek wyprodukujesz.
- **Po każdej korekcie usera** (zrobiłeś coś nie tak, jak chciał): dopisz wpis
  `[data] | gk-sm-3-grafiki | co poszło nie tak | jak ma być | nowy`.
- Wpisy do skilli promuje wyłącznie gk-sm-retro — nie edytuj SKILL.md w trakcie fazy.

## Definition of Done

- Każdy post z serii ma grafikę w `social/images/final/` (min. 4:5),
  nazwaną `<post-id>-4x5.png`.
- Data i miejsce na grafikach eventowych; mockupy pokazane; zestaw
  zaakceptowany przez usera.
- → Następny skill: **gk-sm-4-harmonogram**.
