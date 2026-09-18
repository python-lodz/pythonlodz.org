---
name: gk-sm-retro
description: >
  Retro promocji meetupu Python Łódź po spotkaniu — co zadziałało, ekstrakcja
  klocków wielokrotnego użytku, lekcje. Użyj po meetupie: "retro promocji",
  "podsumuj promocję #NN", "co zadziałało w postach". Czyta social/ meetupu,
  pisze blocks/social/ + tasks/lessons.md. Zamyka sekwencję gk-sm-*.
---

# gk-sm-retro — retro promocji (po meetupie)

Zamyka cykl: wyciąga z kampanii to, co warto zużyć ponownie, i lekcje na
kolejne edycje. Bez analityki zasięgów (poza zakresem systemu) — retro
opiera się na obserwacjach usera i przebiegu procesu.

**Kontrakt z procesem:** wejście: `page/content/spotkania/<nr>/social/`
(+ `status.json` — co i kiedy faktycznie poszło). Wyjście: `blocks/social/`
+ wpisy w `tasks/lessons.md` (+ ew. poprawki skilli gk-sm-*).

## Proces

1. Przejrzyj `status.json`: czy wszystkie posty poszły? Które sloty padły /
   były nadrabiane? Błędy z runów crona (GitHub Actions → „Social publish").
2. Zapytaj usera: które posty/grafiki zadziałały (komentarze, zapisy,
   zgłoszenia LT), co było za dużo/za mało, co ręczne bolało.
3. **Ekstrakcja klocków** → `blocks/social/<nazwa>.md`: sprawdzone fragmenty
   tekstów (call-to-action, explainery LT/OS, struktury postów), szablony
   grafik warte powtórzenia (wskaż plik w `tools/social/templates/`),
   działające sekwencje etapów. Klocek = plik z treścią + notka kiedy używać.
4. **Przegląd feedbacku** → `tasks/feedback.md`: przejdź wszystkie wpisy `nowy`.
   Powtarzające się lub potwierdzone przez usera → wpisz na stałe do odpowiedniego
   `gk-sm-*/SKILL.md`, podbij wersję w `.claude/skills/gk-sm-manifest.md`
   (semver + wpis w CHANGELOG) i zmień status wpisu na `wdrożone`.
   Jednorazowe/nieaktualne → status `odrzucone`. Każdą promocję pokaż userowi
   do akceptacji przed edycją skilla.
5. **Lekcje** → `tasks/lessons.md` w formacie repo:
   `[data] | co poszło nie tak | reguła na przyszłość` (rzeczy spoza procesu gk-sm).

## Definition of Done

- Klocki wielokrotnego użytku w `blocks/social/` (min. te wskazane przez usera).
- `tasks/feedback.md` przejrzany: zero wpisów `nowy` (wszystkie `wdrożone` albo
  `odrzucone`); wdrożone mają odzwierciedlenie w SKILL.md + manifeście.
- Lekcje dopisane do `tasks/lessons.md`.
