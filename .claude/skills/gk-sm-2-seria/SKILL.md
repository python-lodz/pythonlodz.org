---
name: gk-sm-2-seria
description: >
  Faza 2 promocji meetupu Python Łódź — seria postów: jeden kanoniczny tekst
  per post, iteracyjnie z userem. Użyj po zaakceptowanym briefie lub gdy
  trzeba poprawić teksty: "napisz posty", "seria postów", "teksty do promocji",
  "popraw posty do #NN". Czyta social/brief.md, pisze social/posts.md
  w formacie parsowalnym przez publisher. Drugi skill sekwencji gk-sm-*.
---

# gk-sm-2-seria — kanoniczne teksty postów (faza 2)

Zamienia brief w gotowe teksty. **Jeden kanoniczny tekst per post** — NIE
warianty per platforma. Różnice platformowe są mechaniczne i stosuje je
publisher (`src/pyldz/social/transforms.py`): na IG linki zamieniają się w
„🔗 Link w bio → pythonlodz.org" + stałe hashtagi; FB/Discord/LinkedIn dostają
tekst bez zmian. Wyjątek: rzadki `override` per platforma (np. `@everyone`
dla Discorda).

**Kontrakt z procesem:** faza 2. Wejście: `social/brief.md`. Wyjście:
`social/posts.md`. Następny: **gk-sm-3-grafiki**.

## Format social/posts.md (kontrakt z publisherem — nie zmieniaj!)

```markdown
# Posty — Python Łódź #<nr>

## post: <id-kebab-case>

<pełny kanoniczny tekst — linki pełnymi URL-ami, @handle prelegentów IG w treści>

### override: discord

<opcjonalny pełny tekst zastępczy, np. z @everyone>
```

Id posta: `[a-z0-9][a-z0-9-]*` (np. `save-the-date`, `lightning-talk`,
`last-call`). Override tylko gdy transformacja mechaniczna nie wystarcza.

## Zasady tekstów

- Ton Python Łódź: przyjazny, luźny, otwarty, „zero spiny". Emoji z umiarem.
  Myślnik: „-". Wzorzec jakości: `page/content/spotkania/65/descriptions/social-series.md`.
- Każdy post ma jeden cel (z etapów briefu) i jedno CTA.
- Linki pełnymi URL-ami w treści (IG-transform zajmie się resztą).
- Prelegenci: w treści `@handle` (IG) — publisher zostawia; na FB to plain text
  (zgodnie ze specem, ograniczenie Mety); LinkedIn dostanie instrukcję tagów
  w gk-sm-4.
- Placeholder na link do YT live: wpisz `[LINK DO LIVE]` w postach dnia
  spotkania — gk-sm-4 podmieni po założeniu transmisji.

## Model współpracy (obowiązuje)

- **Nigdy jednostrzałowo.** Dla kluczowych postów pokaż 3–4 kontrastowe
  warianty → zbierz reakcję per wariant → syntezuj.
- Pokazuj pełne brzmienie (nie skróty) — to dokładny tekst, który pójdzie
  w świat. **Jawna akceptacja pełnego brzmienia każdego posta.**
- Po akceptacji sprawdź parsowalność:
  `uv run python -c "from pathlib import Path; from pyldz.social.posts_md import parse_posts_md; print(list(parse_posts_md(Path('page/content/spotkania/<nr>/social/posts.md').read_text())))"`

## Definition of Done

- `social/posts.md` w poprawnym formacie (parser zwraca wszystkie posty).
- Każdy etap briefu ma post; każdy post zaakceptowany w pełnym brzmieniu.
- → Następny skill: **gk-sm-3-grafiki**.
