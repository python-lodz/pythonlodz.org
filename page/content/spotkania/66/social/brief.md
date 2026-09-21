# Brief promocji — Python Łódź #66 (30.09.2026, śr 18:00 · IndieBI, Piotrkowska 157A, Hi Piotrkowska)

Preset: P1 (klasyczny meetup, dwie prelekcje) · Kanały: FB, IG, Discord (automat, cron 9:00/17:00) + LinkedIn (wklejka) · YT live: tak

**Model godzin per kanał (decyzja GK 10.07, potwierdzona 21.09):** każdy etap = dwie
publikacje tego samego dnia. Rano **9:00 → Facebook** (+ LinkedIn jako wklejka
z rekomendacją 9:00), wieczorem **17:00 → Discord + Instagram**. W `schedule.yaml`
realizowane jako dwa `ScheduleItem` na post (rozłączne kanały), idempotencja kluczuje
per `post:channel`.

## Etapy (robocze)

Okno: 22.09 → 30.09.2026 (9 dni, 6 etapów). Każdy dzień: 9:00 FB (+LI wklejka) / 17:00 Discord+IG.

| # | dzień | post | cel |
|---|-------|------|-----|
| 1 | wt 22.09 | ogloszenie | Ogłoszenie agendy — dwie prelekcje, data, miejsce, CTA na zapisy |
| 2 | czw 24.09 | prelekcja-kolejki | Sebastian Buczyński, „Największe mity w pracy z kolejkami" — hak na obalaniu mitów, oznaczenie prelegenta |
| 3 | pt 25.09 | prelekcja-pytest | Grzegorz Kocjan, „Najtrudniejszy test suite…" — case study z pytest na niedeterministycznym systemie wideo |
| 4 | pon 28.09 | reminder-agenda | Reminder + agenda wieczoru (18:00, kolejność prelekcji, gospodarz) |
| 5 | wt 29.09 | last-call | Last call — ostatni dzień na zapisy |
| 6 | śr 30.09 | dzien-spotkania | Dzień spotkania — „widzimy się dziś 18:00" + link do transmisji YT |

## Prelegenci i oznaczenia

| kto | IG handle | LinkedIn |
|-----|-----------|----------|
| Sebastian Buczyński | — (GK nie podaje; post na IG bez oznaczenia) | https://www.linkedin.com/in/sebastianbuczynski/ |
| Grzegorz Kocjan | `grzegorz.kocjan` | https://www.linkedin.com/in/grzegorzkocjan/ |

Kolejność prelekcji (z arkusza, `order` puste ⇒ kolejność wierszy): 1. Sebastian, 2. Grzegorz.

Dodatkowe kanały prelegentów — do ewentualnego wplecenia w posty per prelekcja:
Sebastian (YT `@pythoneerguru`, blog breadcrumbscollector.tech, autor książki o czystej
architekturze w Pythonie, Software Engineer w Revolut), Grzegorz (YT `@grzegorz.kocjan`,
belazy.dev).

Sponsor i gospodarz: **IndieBI** (Piotrkowska 157A, Hi Piotrkowska) — wspominać w postach,
które podają lokalizację.

## Linki

- strona: https://pythonlodz.org/spotkania/66/ ← **główne CTA w treści postów** (feedback 10.07: nie linkujemy wprost do meetup.com)
- zapisy: `[LINK DO ZAPISÓW]` — wydarzenie na meetup.com istnieje, link do wpisania w arkusz (kolumna `meetup_url`)
- Discord: https://discord.gg/e4XpHMnPfJ
- YT live: zakłada gk-sm-4; opis gotowy w `descriptions/youtube-live.md`

## Braki / do uzupełnienia

- **`meetup_url` w arkuszu — blocker etapu 1.** Bez niego strona #66 nie ma przycisku
  zapisów, więc główne CTA prowadzi w pustkę. Po wpisaniu: `uv run pyldz generate -m 66`.
- ~~Handle IG prelegentów~~ — rozstrzygnięte 21.09: Grzegorz `grzegorz.kocjan`
  (wpisany do `page/data/speakers/grzegorz-kocjan.yaml`), Sebastian bez handle'a
  — jego post na IG idzie bez oznaczenia, reszta treści bez zmian.
- `feedback_url` — uzupełniany po spotkaniu, nie dotyczy tej serii.
- Link do strony spotkania w bio na IG — podmiana ręczna przy pierwszym poście.

## Decyzje i odchyłki

- **P1, nie P2** — klasyczny meetup z dwiema zapowiedzianymi prelekcjami (P2 to edycje
  letnie LT + Open Spaces, patrz `tasks/lessons.md`).
- **Start 22.09, 6 etapów** (decyzja GK 21.09) — wymaga domknięcia gk-sm-2 (teksty)
  i gk-sm-3 (grafiki) jeszcze dziś, bo pierwsza publikacja leci wtorek 9:00.
- **YT live: tak**, jak przy #65 (decyzja GK 21.09).
- **Dwa posty merytoryczne, nie jeden zbiorczy** — każda prelekcja dostaje własny etap
  z oznaczeniem prelegenta; to rdzeń presetu P1.
- **Opis prelekcji Grzegorza ma 2044 znaki** (w arkuszu) — w postach idzie tylko hak
  (niedeterministyczny system wideo, skuteczność detekcji 80–90%, podwójna
  parametryzacja), nie streszczenie całości.
- **Grafiki: każdy post ma własne tło** (feedback 10.07), bez wakacyjnego klimatu #65 —
  P1 celuje w techniczny, spójny z brandem look. Featured 4:5 i 1:1 z generatora PIL
  (`images/featured-pl-4x5.png`, `-1x1`) oraz kadry per prelegent
  (`images/speaker_0-PL-4x5.png`, `speaker_1-PL-4x5.png`) są gotowe — kandydaci na
  etapy 1, 2, 3 i 4 zamiast renderowania od zera.
- **Posty z CTA mają CTA na grafice**, nie tylko w tekście (feedback 10.07).
- Weekend 26–27.09 pominięty świadomie: etapy merytoryczne w dni robocze, zagęszczenie
  na 28–30.09 (reminder → last call → dzień spotkania).
