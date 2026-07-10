---
name: gk-sm-1-brief
description: >
  Faza 1 promocji meetupu Python Łódź w social media — brief: preset, zakres,
  kanały, decyzje. Użyj gdy startujemy promocję spotkania: "promocja meetupu",
  "wystartujmy social media do #NN", "zaplanuj posty do spotkania #NN",
  "brief promocji", "kampania meetupu". Czyta page/content/spotkania/<nr>/index.md
  + dane prelegentów, pisze social/brief.md. Pierwszy skill sekwencji gk-sm-*.
---

# gk-sm-1-brief — brief promocji (faza 1)

Ustala CO promujemy, JAKIM presetem i na JAKICH kanałach — zanim powstanie
jakikolwiek tekst. Wyjście to krótki dokument decyzji, nie treści.

**Kontrakt z procesem:** faza 1. Wejście: `page/content/spotkania/<nr>/index.md`
(+ `page/data/speakers/*.yaml`, dane sponsora). Wyjście:
`page/content/spotkania/<nr>/social/brief.md`. Następny: **gk-sm-2-seria**.

## Presety

- **P1 — klasyczny meetup** (prelekcje z prelegentami):
  ogłoszenie → post per prelekcja (z oznaczeniem prelegenta) → reminder →
  last call → dzień spotkania.
- **P2 — Lightning Talks + Open Spaces** (edycje letnie; wzorzec: ręczna seria
  #65 `page/content/spotkania/65/descriptions/social-series.md`):
  ogłoszenie → posty edukacyjne „czym jest LT/OS" → call for speakers →
  reminder → last call → dzień spotkania.
- **P3 — pojedynczy post** (ad-hoc: ankieta, nagranie, ogłoszenie).

## Proces

1. Przeczytaj `index.md` spotkania: format, data, godzina, miejsce,
   prelekcje/LT, sponsor. Edycja letnia ⇒ P2 (patrz `tasks/lessons.md`).
2. Zbierz prelegentów: `page/data/speakers/<id>.yaml` — w tym pole
   `instagram:` (handle bez @) do oznaczeń na IG oraz profil LinkedIn z sekcji
   `social:`. Braki wypisz w briefie jako „do uzupełnienia / pominięcia".
3. Kanały standardowe: FB + IG + Discord (automat, cron 9:00/17:00 PL)
   oraz LinkedIn (pakiet wklejki z gk-sm-4). YT live zakłada gk-sm-4.
   Odchyłki zapisz jawnie w sekcji Decyzje.
4. Ustal etapy (liczba i cele postów) oraz okno czasowe: od dziś do dnia
   spotkania, sloty tylko 9:00 lub 17:00.
5. Zbierz linki: strona spotkania, zapisy (meetup.com), formularz LT (dla P2),
   Discord. Brak linku = placeholder `[LINK]` + pozycja na liście braków.
6. Pokaż brief userowi, zbierz uwagi, popraw. **Jawna akceptacja** kończy fazę.

## Format social/brief.md

```markdown
# Brief promocji — Python Łódź #<nr> (<data> · <miejsce>)

Preset: P1|P2|P3 · Kanały: FB, IG, Discord (automat) + LinkedIn (wklejka) · YT live: tak/nie

## Etapy (robocze)
| # | ~data | slot | cel |
|---|-------|------|-----|

## Prelegenci i oznaczenia
| kto | IG handle | LinkedIn |
|-----|-----------|----------|

## Linki
- strona: … · zapisy: … · formularz LT: … · Discord: …

## Braki / do uzupełnienia
## Decyzje i odchyłki
```

## Feedback loop (obowiązuje)

- **Na starcie fazy**: przeczytaj `tasks/feedback.md` i zastosuj wpisy ze statusem
  `nowy` dotyczące tej fazy, zanim cokolwiek wyprodukujesz.
- **Po każdej korekcie usera** (zrobiłeś coś nie tak, jak chciał): dopisz wpis
  `[data] | gk-sm-1-brief | co poszło nie tak | jak ma być | nowy`.
- Wpisy do skilli promuje wyłącznie gk-sm-retro — nie edytuj SKILL.md w trakcie fazy.

## Definition of Done

- `social/brief.md` istnieje: preset, etapy z celami, kanały, linki.
- Braki danych jawnie wylistowane.
- User zaakceptował brief.
- → Następny skill: **gk-sm-2-seria**.
