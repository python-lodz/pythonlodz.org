---
name: gk-sm-4-harmonogram
description: >
  Faza 4 promocji meetupu Python Łódź — harmonogram publikacji, YT live,
  pakiet LinkedIn, dry-run i uzbrojenie crona. Użyj po zaakceptowanych
  grafikach: "harmonogram postów", "zaplanuj publikacje", "odpal promocję",
  "załóż live na YouTube", "pakiet LinkedIn". Pisze social/schedule.yaml
  + social/linkedin-paste.md, zakłada YT live, robi dry-run, commituje do main.
  Czwarty skill sekwencji gk-sm-*.
---

# gk-sm-4-harmonogram — kalendarz, YT live, wklejka, uzbrojenie (faza 4)

Ostatnia faza przed automatem: układa kalendarz, zakłada transmisję,
generuje pakiet ręcznej wklejki i uzbraja cron przez commit do `main`.

**Kontrakt z procesem:** faza 4. Wejście: `social/posts.md` +
`social/images/final/`. Wyjście: `social/schedule.yaml` +
`social/linkedin-paste.md` (+ link YT w postach). Następny: gk-sm-retro
(po meetupie).

## Proces

1. **Kalendarz**: przypisz każdemu postowi datę + slot (tylko **9:00** lub
   **17:00** Europe/Warsaw), kanały, grafikę i tagi IG. Format
   `schedule.yaml` (kontrakt z publisherem — patrz niżej).
2. **YT live** (jeśli brief mówi „tak"):
   ```bash
   uv run pyldz social yt-create-live --title "Python Łódź #<nr> — <tytuł>" \
     --start "<YYYY-MM-DD HH:MM>" --description-file page/content/spotkania/<nr>/descriptions/youtube-live.md
   ```
   Zwrócony link wstaw w `posts.md` w miejsce `[LINK DO LIVE]`.
   (Pierwsze użycie: otworzy się OAuth w przeglądarce; token → `.yt_token.json`.)
3. **Pakiet LinkedIn**: `social/linkedin-paste.md` — dla każdego posta
   z kanałem `linkedin`: data+slot, pełny tekst (kanoniczny lub override),
   którą grafikę załączyć, kogo oznaczyć (profile LinkedIn prelegentów
   z briefu — tagowanie ręcznie w UI natywnego schedulera, do 3 mies. w przód).
   Opcjonalnie sekcja YT Community (brak API — też wklejka).
4. **Dry-run** — pokaż userowi DOKŁADNE payloady:
   ```bash
   uv run pyldz social dry-run --meetup <nr>
   ```
   Uwaga: dry-run pokazuje tylko posty due „teraz"; harmonogram przyszły
   zweryfikuj czytając schedule.yaml na głos (post × kanał × slot × grafika).
5. **Akceptacja → uzbrojenie**: po jawnej akceptacji całości commit + push
   do `main` (posts.md, schedule.yaml, images/final/, linkedin-paste.md).
   Publikacja = merge do main; cron (`.github/workflows/social-publish.yaml`,
   sloty 9:00/17:00 PL) przejmuje resztę i nadrabia zaległe sloty.
   Deploy strony (GitHub Pages) musi zajść przed pierwszym slotem —
   grafiki muszą być publicznie dostępne pod
   `https://pythonlodz.org/spotkania/<nr>/social/…` (FB/IG ciągną URL).

## Format social/schedule.yaml (kontrakt z publisherem — nie zmieniaj!)

```yaml
meetup: "<nr>"
timezone: Europe/Warsaw
posts:
  - post: <id z posts.md>
    channels: [facebook, instagram, discord, linkedin]
    scheduled: 2026-07-08 09:00:00      # czas lokalny Europe/Warsaw
    image: images/final/<post-id>-4x5.png   # względem social/
    ig_tagged: [<ig-handle-bez-@>]           # opcjonalne
```

Zasady: IG wymaga `image`; `linkedin` w `channels` = tylko do pakietu wklejki
(publisher pomija); posty przeszłe bez wpisu w `status.json` publikują się
w najbliższym runie (świadomie — tak działa nadrabianie).

## Feedback loop (obowiązuje)

- **Na starcie fazy**: przeczytaj `tasks/feedback.md` i zastosuj wpisy ze statusem
  `nowy` dotyczące tej fazy, zanim cokolwiek wyprodukujesz.
- **Po każdej korekcie usera** (zrobiłeś coś nie tak, jak chciał): dopisz wpis
  `[data] | gk-sm-4-harmonogram | co poszło nie tak | jak ma być | nowy`.
- Wpisy do skilli promuje wyłącznie gk-sm-retro — nie edytuj SKILL.md w trakcie fazy.

## Definition of Done

- `schedule.yaml` waliduje się (`uv run pyldz social dry-run --meetup <nr>`
  działa bez błędu), każdy post ma slot 9:00/17:00 i grafikę tam, gdzie trzeba.
- YT live założony, link wstawiony w posty (jeśli dotyczy).
- `linkedin-paste.md` kompletny (teksty + daty + grafiki + kogo oznaczyć).
- User zaakceptował harmonogram; całość scommitowana i wypchnięta na `main`.
- Po meetupie: **gk-sm-retro**.
