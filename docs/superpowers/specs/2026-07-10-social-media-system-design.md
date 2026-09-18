# System promocji meetupów w social media (gk-sm-*) — design

Data: 2026-07-10 · Status: zaakceptowany przez GK · Repo docelowe: pythonlodz.org (wszystko tutaj)

## 1. Cel

Jedna sesja robocza z Claude w repo pythonlodz.org planuje całą promocję meetupu:

- seria postów na **Facebook / Instagram / Discord** publikowana automatycznie wg harmonogramu
  (GitHub Actions cron, stałe sloty),
- **pakiet do wklejenia** dla LinkedIn (natywny scheduler LinkedIn, do 3 mies. w przód)
  — plus opcjonalnie YT Community posts (brak API),
- **zaplanowany live na YouTube** przez API (link do transmisji dostępny od razu w sesji
  i wklejany do postów).

Automatyzacja ~80%. Ręczne zostaje: akceptacje treści/grafik/harmonogramu, wklejka LinkedIn
(z oznaczeniem prelegentów w UI), opcjonalny tag prelegenta na FB po publikacji.

Zastępuje dotychczasowy `descriptions/chatgpt-prompt.md` (ręcznie kopiowany meta-prompt:
brak parametryzacji, brak obsługi LT/Open Spaces, brak IG/LinkedIn) oraz półręczną pracę
w stylu #65 (`social-series.md` dla #65 to prototyp tego, co system generuje automatycznie).

## 2. Ustalenia o wykonalności API (researched 2026-07-10)

| Platforma | Publikacja przez API | Planowanie przez API | Oznaczanie osób |
|---|---|---|---|
| Facebook (Page) | tak, Graph API | **tak** — `scheduled_publish_time` (natywny kalendarz Mety) | **nie** (profili prywatnych; ograniczenie Mety) |
| Instagram (Business) | tak — container → `media_publish` | **nie** — tylko natychmiast; scheduling budujemy sami | **tak** — `@handle` w caption (≤3) + `user_tags` na zdjęciu/Reels |
| LinkedIn (Page) | wymaga Community Management API (wniosek od podmiotu prawnego, 1–4 tyg.) | **nie** — `lifecycleState=PUBLISHED` to jedyna opcja; natywny scheduler tylko w UI | tak (mentions w commentary), ale dostęp zablokowany j.w. |
| Discord | webhook | przez nasz cron | n/d |
| YouTube live | tak — `liveBroadcasts.insert` z `scheduledStartTime` | **tak natywnie** | n/d |
| YouTube Community | **brak API** | — | — |

Cross-posting FB+IG z Meta Business Suite to funkcja wyłącznie UI — nie ma odpowiednika w API;
publisher publikuje ten sam content na FB i IG niezależnie (efekt identyczny).

Decyzje: **LinkedIn = wklejka** (wniosek o CM API świadomie odłożony — bez podmiotu teraz);
**IG/Discord = własny cron**; **FB** — publikacja przez cron razem z IG (spójnie, jeden mechanizm);
**YT live** zakładany od razu w sesji planowania.

## 3. Proces — skille `gk-sm-*`

Wzorzec przeniesiony z `dumtek/fb-ads-system` (gk-fb-*): sekwencja numerowanych,
samowystarczalnych skilli; każdy czyta artefakty poprzedniej fazy, pisze jeden własny,
kończy się Definition of Done wskazującym następny. Frontmatter z polskimi frazami
wyzwalającymi. Manifest wersji (semver) + CHANGELOG + routing w CLAUDE.md repo.

- **gk-sm-1-brief** — czyta `page/content/spotkania/<nr>/index.md` + dane prelegentów/sponsorów;
  ustala preset i zakres. Presety:
  - **P1 klasyczny meetup** (prelekcje): ogłoszenie → post per prelekcja (z tagiem prelegenta) →
    reminder → last call → dzień spotkania;
  - **P2 Lightning Talks + Open Spaces**: ogłoszenie → posty edukacyjne "czym jest LT/OS" →
    call for speakers → reminder → last call (wzorzec: ręczna seria #65);
  - **P3 pojedynczy post** (ad-hoc).
  → `social/brief.md`
- **gk-sm-2-seria** — **jeden kanoniczny tekst per post** (nie warianty per platforma);
  różnice platformowe są mechaniczne i stosuje je publisher (patrz §6). Iteracyjnie:
  3–4 kontrastowe warianty → reakcja per wariant → synteza → jawna akceptacja pełnego brzmienia.
  → `social/posts.md`
- **gk-sm-3-grafiki** — **HTML+CSS → puppeteer → PNG** (wzorzec `render_ad_mockups.mjs` z dumtek):
  szablony w `tools/social/templates/*.html` z brandem (granat `#001F3F`, żółty `#FFD700`,
  logo + fonty OpenSans z `page/assets/`); tła stockowe (Pexels/Unsplash → `social/images/stock/`
  z notką źródła) lub własne zdjęcia/assety; tekst zawsze warstwą HTML; formaty 4:5 / 1:1 / 16:9
  z jednego szablonu. Reguły czytelności z dumtek: data i miejsce NA grafice, wysoki kontrast,
  czcionka czytelna na telefonie. Mockup posta w feedzie do akceptacji. Zaakceptowane →
  `social/images/final/`, odrzucone + źródła HTML → `social/images/archive/`.
- **gk-sm-4-harmonogram** — układa kalendarz (sloty), zakłada YT live przez API (link wraca
  do treści), generuje pakiet LinkedIn (`linkedin-paste.md`: posty + daty + kogo oznaczyć +
  które grafiki), dry-run publishera (dokładne payloady), po akceptacji commit do `main`.
  → `social/schedule.yaml` + `social/linkedin-paste.md`
- **gk-sm-retro** — po meetupie: co zadziałało, ekstrakcja klocków do `blocks/social/`, lekcje,
  przegląd `tasks/feedback.md` i promocja sprawdzonych wpisów do skilli (podbicie wersji w manifeście).

**Feedback loop** (każda faza): na starcie skill czyta `tasks/feedback.md` i stosuje wpisy `nowy`;
po każdej korekcie usera dopisuje wpis `[data] | skill | co poszło nie tak | jak ma być | nowy`.
Docelowo wpisy są usprawniane i przenoszone do skilli wyłącznie w gk-sm-retro (za akceptacją GK).

## 4. Artefakty

`page/content/spotkania/<nr>/social/` (obok istniejących `descriptions/`, `images/`):

```
social/
  brief.md            # preset, zakres, decyzje
  posts.md            # kanoniczne teksty postów (+ rzadkie override'y per platforma)
  schedule.yaml       # harmonogram: post × kanały × data/slot × grafika × tagi
  linkedin-paste.md   # pakiet do ręcznej wklejki (LinkedIn, ew. YT Community)
  status.json         # zapisywany przez publisher: co poszło, ID postów (idempotencja)
  images/
    final/  archive/  stock/
```

## 5. Silnik publikacji

- CLI w istniejącym pakiecie: **`src/pyldz/social/`** (`uv run pyldz social publish --due`,
  `... dry-run`, `... yt-create-live`). Adaptery: FB (Graph API, feed + photo), IG (container →
  publish, `user_tags` + mentions), Discord (webhook). Architektura otwarta na adapter LinkedIn
  (gdy kiedyś będzie CM API).
- **GitHub Actions** `social-publish.yaml`: cron w stałych slotach **9:00 i 17:00 Europe/Warsaw**;
  wpisy cron w UTC pokrywają czas letni i zimowy, a skrypt decyduje w strefie `Europe/Warsaw`,
  co jest due (`scheduled <= now` i brak wpisu w `status.json`) — run nadrabia zaległe sloty
  (odporność na opóźnienia cronów GitHuba). Dodatkowo `workflow_dispatch`.
- **Bezpieczniki**: publikacja wyłącznie z `main` (akceptacja = commit/merge); dry-run w sesji
  planowania; `status.json` commitowany po publikacji (brak podwójnych publikacji);
  sekrety w GitHub Secrets: `META_*`, `DISCORD_WEBHOOK_URL`, `YT_*`.

## 6. Uniwersalny format treści

Jeden tekst kanoniczny per post; transformacje mechaniczne w publisherze:

- **IG**: link nieklikalny → zamiana sekcji linku na "🔗 link w bio / pythonlodz.org" +
  stały zestaw hashtagów; `@handle` prelegentów zostaje.
- **Discord**: markdown + pełny link.
- **FB**: bez zmian. **LinkedIn**: bez zmian (w pakiecie wklejki + instrukcja tagów).
- Wyjątki: opcjonalne pole `override` per platforma w `posts.md` (rzadko).

## 7. Prelegenci i oznaczanie

`page/data/speakers/*.yaml` + nowe opcjonalne pole `instagram:` (handle bez @).
Mapa: **IG** automatycznie (caption + tag na zdjęciu) · **LinkedIn** ręcznie przy wklejce
(instrukcja w pakiecie) · **FB** plain text (opcjonalny ręczny tag po publikacji).

## 8. Tokeny i znane ryzyka

- **Meta**: strona Python Łódź (Page `pythonlodz` + IG `pythonlodz`) to inne portfolio niż
  dumtek → **osobna appka + System User token** (checklista: `dumtek/fb-ads-system/notes/meta-api-setup.md`).
  Scope'y: `pages_manage_posts`, `pages_read_engagement`, `instagram_content_publish`,
  `business_management`.
- **Ryzyko #1** (znane z dumtek): appka w trybie Development może ograniczać publikację/widoczność —
  możliwy App Review / Business verification. Wyjdzie w pilocie. Plan B na przejściówkę:
  FB+IG czasowo w pakiecie wklejki (Business Suite planuje oba naraz jednym postem);
  architektura bez zmian.
- **YouTube**: OAuth w istniejącym projekcie Google Cloud (od Sheets/pyldz), scope
  `youtube.force-ssl`; refresh token w GitHub Secrets.
- **Higiena sekretów**: w repo leżą `.env`, `.client_secret.json`, `.client_secret.token.json` —
  zweryfikować, że nie są śledzone przez git; nowe sekrety nigdy w repo.
- **Dokumentacja konfiguracji (deliverable)**: `docs/social/setup.md` — krok po kroku, jak
  uzyskać każdą zmienną z każdego portalu (Meta: appka + System User token + Page ID + IG user ID;
  Discord: webhook; YouTube: OAuth w istniejącym projekcie GCP) i gdzie ją wpiąć
  (GitHub Secrets dla crona, lokalny `.env` dla sesji planowania), z komendami weryfikacyjnymi.

## 9. Poza zakresem (świadomie, na teraz)

Wniosek LinkedIn Community Management API · YT Community posts przez API (brak) ·
IG Stories/Reels (adapter przewiduje rozszerzenie) · analityka zasięgów ·
meetup.com (opis jak dotąd w `descriptions/`, publikacja ręczna) ·
automatyzacja przeglądarki (łamie ToS — odrzucone).

## 10. Log decyzji

- 2026-07-10 · LinkedIn = wklejka do natywnego schedulera; wniosek o CM API odłożony (GK).
- 2026-07-10 · Jeden cron GitHub Actions dla FB/IG/Discord; stałe sloty 9:00/17:00 PL (GK).
- 2026-07-10 · YT live zakładany w sesji przez API; link wchodzi do postów (GK).
- 2026-07-10 · System w całości w repo pythonlodz.org (GK).
- 2026-07-10 · Grafiki: HTML→puppeteer→PNG + stock backgrounds, wzorzec dumtek (GK).
- 2026-07-10 · Jeden uniwersalny tekst per post, różnice platformowe mechaniczne (GK).
- 2026-07-10 · Wymagana dokumentacja `docs/social/setup.md`: jak uzyskać i wpiąć wszystkie
  zmienne/sekrety per portal SM (GK).
- 2026-07-10 · Feedback loop: korekty usera → `tasks/feedback.md`, czytany na starcie każdej
  fazy; promocja wpisów do skilli w gk-sm-retro (GK).
