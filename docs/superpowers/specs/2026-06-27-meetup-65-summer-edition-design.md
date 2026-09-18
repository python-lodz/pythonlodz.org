# Spec — Python Łódź #65 · Summer Edition

**Data:** 2026-06-27
**Cel:** Komplet materiałów dla spotkania #65 (29.07.2026): strona, opisy, grafiki, seria postów social, reklama — w formacie sprawdzonej edycji letniej #59 (Lightning Talks + Open Spaces).

## Założenia
- Numer: **#65**, środa **29.07.2026, 18:00**
- Miejsce: **IndieBI, Piotrkowska 157A, Hi Piotrkowska**
- Format: **Lightning Talks + Open Spaces** (bez prelegentów w danych)
- **Bez nagrody** za LT (w #59 były wejściówki na PyConPL)
- Formularz LT: reuse z #59
- Link meetup.com: placeholder (do uzupełnienia)
- Sponsor: **IndieBI**
- Platformy serii postów: Facebook, Discord, LinkedIn, Instagram
- Język: polski

## Deliverables
1. `page/content/spotkania/65/index.md` — standalone strona wg wzoru #59, bez sekcji nagrody, framing summer edition.
2. `page/content/spotkania/65/descriptions/meetup-com.md` — opis na meetup.com.
3. `page/content/spotkania/65/descriptions/youtube-live.md` — opis transmisji live.
4. `page/content/spotkania/65/descriptions/social-series.md` — 7-etapowa seria postów w wariantach per platforma + briefy grafik 4:5.
5. `page/content/spotkania/65/descriptions/reklama.md` — tekst reklamowy + brief kreacji.
6. Grafiki:
   - branded `featured.png` (16:9) + `images/` warianty 4:5, 1:1 — generowane PIL ze skryptu reużywającego assetów pyldz (logo, tło, fonty, paleta), dedykowany layout "Lightning Talks + Open Spaces" (bez avatarów).
   - kreacje AI / briefy do postów i reklamy.

## Architektura grafik
Standalone skrypt `scripts/generate_summer_graphic.py` (PIL), reużywa:
- `page/assets/images/bacground.png`, `python_lodz_logo_transparent_border.png`
- `page/assets/fonts/OpenSans-*.ttf`
- paleta: YA #FFD700, CG #001F3F, JS #F5F5F5, CT #333333
Layout: nagłówek "PYTHON ŁÓDŹ #65" + "SUMMER EDITION", data/godzina (żółty akcent), centralny blok "⚡ LIGHTNING TALKS + 💬 OPEN SPACES", stopka (lokalizacja + pythonlodz.org). Warianty 16:9 / 4:5 / 1:1.

## Decyzje
- Edycja letnia = standalone index.md (jak #59), nie pipeline danych.
- Nie modyfikujemy `MeetupImageGenerator` (zbudowany wokół prelegentów) — osobny skrypt dla summer layoutu, by nie ryzykować regresji.
