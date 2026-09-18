# Brief promocji — Python Łódź #65 (29.07.2026, śr 18:00 · IndieBI, Piotrkowska 157A, Hi Piotrkowska)

Preset: P2 (Lightning Talks + Open Spaces, edycja letnia) · Kanały: FB, IG, Discord (automat, cron 9:00/17:00) + LinkedIn (wklejka) · YT live: tak

**Model godzin per kanał (decyzja GK 10.07):** każdy etap = dwie publikacje tego
samego dnia. Rano **9:00 → Facebook** (+ LinkedIn jako wklejka z rekomendacją 9:00),
wieczorem **17:00 → Discord + Instagram**. W `schedule.yaml` realizowane jako dwa
`ScheduleItem` na post (rozłączne kanały), idempotencja kluczuje per `post:channel`.

## Etapy (robocze)

Okno: 10.07 → 29.07.2026. Każdy dzień: 9:00 FB (+LI wklejka) / 17:00 Discord+IG.

| # | dzień | post | cel |
|---|-------|------|-----|
| 1 | pon 13.07 | save-the-date | Save the date — ogłoszenie wakacyjnej edycji |
| 2 | śr 15.07 | lightning-talk | Czym jest Lightning Talk + otwarcie zgłoszeń (formularz) |
| 3 | pt 17.07 | zero-spiny | Zasady LT / „zero spiny" — obalenie strachu przed sceną |
| 4 | wt 21.07 | open-spaces | Open Spaces explainer — druga część wieczoru |
| 5 | czw 23.07 | lt-zgloszenia-update | Social proof — „mamy już 3 zgłoszenia, czekamy na Twoje" |
| 6 | pt 24.07 | reminder-agenda | Reminder + agenda wieczoru |
| 7 | pon 27.07 | last-call | Last call na zgłoszenia Lightning Talków |
| 8 | śr 29.07 | dzien-spotkania | Dzień spotkania — mobilizacja „widzimy się dziś" (+ link YT live) |

## Prelegenci i oznaczenia

Format LT + Open Spaces — brak zapowiedzianych prelegentów, brak postów per prelekcja i oznaczeń. Bohaterem serii jest społeczność („to Wy tworzycie program").

| kto | IG handle | LinkedIn |
|-----|-----------|----------|
| — (n/d dla P2) | — | — |

Sponsor/gospodarz: **IndieBI** (miejsce: Piotrkowska 157A, Hi Piotrkowska) — wspominać w postach z lokalizacją.

## Linki

- strona: https://pythonlodz.org/spotkania/65/
- zapisy: https://www.meetup.com/python-lodz/events/315445931
- formularz LT: https://forms.gle/wJMToqP34B7FyJEv5
- Discord: https://discord.gg/e4XpHMnPfJ (potwierdzony przez GK 10.07.2026)
- YT live: założy gk-sm-4 (opis gotowy w `descriptions/youtube-live.md`)

## Braki / do uzupełnienia

- Link do strony spotkania w bio na IG — do podmiany ręcznie przy pierwszym poście.
- **Liczba zgłoszeń w poście `lt-zgloszenia-update` (23.07):** obecnie „3" — GK musi
  potwierdzić/zaktualizować realną liczbę zgłoszeń przed 23.07 (edycja w `posts.md`).

Rozstrzygnięte 10.07.2026: Discord kanoniczny to `discord.gg/e4XpHMnPfJ` (w serii
podmienić `jbvWBMufEf`); „Save the date" NIE został opublikowany — seria startuje
od etapu 1 dnia 13.07 o 9:00.

## Decyzje i odchyłki

- **P2 wg lessons.md** — edycja letnia, wzorzec #59; bez generatora prelegentowego.
- **Reuse ręcznej serii:** `descriptions/social-series.md` (7 etapów, teksty per kanał) to punkt wyjścia dla gk-sm-2-seria — teksty do przeniesienia/odświeżenia do formatu parsowalnego `social/posts.md`, z podmianą placeholdera `[LINK DO ZAPISÓW]` na realny link meetup.com (już jest w index.md).
- **Grafiki już istnieją** (PIL, `scripts/generate_summer_graphic.py`): featured 4:5/1:1 + posty lightning-talk / zero-spiny / open-spaces / last-call (4:5). gk-sm-3 głównie mapuje istniejące pliki na etapy zamiast tworzyć od zera; ewentualnie dorobi brakujące (reminder/agenda, dzień spotkania).
- Harmonogram zagęszczony na końcu (24 → 27 → 29.07) — szczyt zgłoszeń LT tuż przed spotkaniem.
