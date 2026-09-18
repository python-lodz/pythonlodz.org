# pythonlodz.org — instrukcje projektu

## Social media — promocja meetupów (gk-sm-*)

Frazy typu „promocja meetupu", „posty na social media", „seria postów",
„grafiki do postów", „harmonogram publikacji", „załóż live na YouTube",
„pakiet LinkedIn", „retro promocji" → użyj sekwencji skilli gk-sm-*
(`.claude/skills/gk-sm-*`), wchodząc w fazę odpowiednią do stanu artefaktów
w `page/content/spotkania/<nr>/social/`:

1. `gk-sm-1-brief` → `social/brief.md`
2. `gk-sm-2-seria` → `social/posts.md`
3. `gk-sm-3-grafiki` → `social/images/final/`
4. `gk-sm-4-harmonogram` → `social/schedule.yaml` + `social/linkedin-paste.md` + YT live
5. po meetupie: `gk-sm-retro` → `blocks/social/` + lekcje

Publikacją steruje `.github/workflows/social-publish.yaml`
(cron 9:00/17:00 Europe/Warsaw) przez `uv run pyldz social publish`.
Silnik: `src/pyldz/social/`. Wersje skilli: `.claude/skills/gk-sm-manifest.md`.
Konfiguracja sekretów: `docs/social/setup.md`.

**Feedback loop (obowiązuje w każdej fazie gk-sm):** na starcie fazy przeczytaj
`tasks/feedback.md` i zastosuj wpisy `nowy`; po każdej korekcie usera dopisz tam
wpis `[data] | skill | co poszło nie tak | jak ma być | nowy`. Promocja wpisów
do SKILL.md odbywa się wyłącznie w gk-sm-retro (za akceptacją usera, z podbiciem
wersji w manifeście).
