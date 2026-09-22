# Konfiguracja sekretów systemu gk-sm — krok po kroku

Jak uzyskać każdą zmienną z każdego portalu i gdzie ją wpiąć. Sekrety żyją
w dwóch miejscach:

- **GitHub Secrets** (repo → Settings → Secrets and variables → Actions) —
  używa ich cron `.github/workflows/social-publish.yaml`;
- **lokalny `.env`** (gitignored; szablon: `.env.example`) — używa go sesja
  planowania (`uv run pyldz social dry-run`, testy ręczne).

| Zmienna | Portal | Używana przez |
|---|---|---|
| `META_PAGE_ID` | Meta (strona FB Python Łódź) | publisher FB |
| `META_ACCESS_TOKEN` | Meta (token System User) | publisher FB + IG |
| `IG_USER_ID` | Meta (konto IG `pythonlodz`) | publisher IG |
| `DISCORD_WEBHOOK_URL` | Discord (serwer Python Łódź) | publisher Discord |
| `SITE_BASE_URL` | — (stała, domyślnie https://pythonlodz.org) | URL-e grafik |
| YouTube OAuth | Google Cloud (istniejący projekt pyldz) | `yt-create-live` (lokalnie) |

## 1. Meta — `META_PAGE_ID`, `META_ACCESS_TOKEN`, `IG_USER_ID`

Strona „Python Łódź" + IG `pythonlodz` to **inne portfolio firmowe niż DumTek**
→ osobna aplikacja + osobny System User + osobny token (nie mieszaj portfolio;
pełne uzasadnienie: `dumtek/fb-ads-system/notes/meta-api-setup.md`).

Wymagania wstępne: konto IG `pythonlodz` musi być typu **Business/Creator**
i być **połączone ze stroną FB** (Ustawienia strony → Połączone konta →
Instagram), a strona i IG muszą wisieć w portfolio firmowym (Business
Manager) Python Łódź.

1. **Business Manager** — business.facebook.com → Ustawienia firmy.
   Upewnij się, że w portfolio są: Strona FB „Python Łódź" (Konta → Strony)
   i konto IG `pythonlodz` (Konta → Konta na Instagramie).
2. **Aplikacja Meta** — developers.facebook.com → Utwórz aplikację → typ
   **Business**. Powiąż z portfolio (Business Settings → Konta → Aplikacje →
   Dodaj). Zanotuj App ID (przyda się przy debugowaniu tokena).
3. **System User** — Business Settings → Użytkownicy → Użytkownicy systemowi →
   Dodaj, typ **Admin**. Przypisz zasoby (Assign assets): **Strona FB**
   (pełna kontrola), **konto IG**, **aplikacja** z pkt. 2.
4. **Token System User** — przy użytkowniku „Generuj token": wybierz aplikację,
   zakresy (scopes): `pages_manage_posts`, `pages_read_engagement`,
   `instagram_basic`, `instagram_content_publish`, `business_management`;
   wygaśnięcie: **„Nigdy"**. Skopiuj token (pokazywany raz) → to jest
   `META_ACCESS_TOKEN`.

   Uwaga na pułapkę z 22.09.2026: przypisanie zasobów (pkt. 3) i zakresy tokena
   to **dwie niezależne rzeczy**. System User może mieć na stronie pełne zadania
   (`MANAGE`, `CREATE_CONTENT`) i nadal nie móc nic opublikować, jeśli token
   powstał bez `pages_manage_posts`. Bez `instagram_basic` pole
   `instagram_business_account` na stronie wraca puste, więc krok 6 nie zadziała.
5. **`META_PAGE_ID`** — Business Settings → Konta → Strony → ID strony
   (albo: strona FB → Informacje → ID strony).
6. **`IG_USER_ID`** — mając token i Page ID:
   ```bash
   curl "https://graph.facebook.com/v23.0/<META_PAGE_ID>?fields=instagram_business_account&access_token=<META_ACCESS_TOKEN>"
   ```
   Pole `instagram_business_account.id` → to jest `IG_USER_ID`.

**Weryfikacja tokena:**

```bash
uv run pyldz social check-meta
```

Komenda robi same odczyty (nic nie publikuje, nie pokazuje tokena) i mówi, czy
token widzi stronę oraz czy `IG_USER_ID` zgadza się z kontem podpiętym do strony.
Ten sam sprawdzian z sekretami z CI odpala workflow **Social check**
(`.github/workflows/social-check.yaml`, ręczny `workflow_dispatch`) — przydatne,
gdy lokalny `.env` może mieć inny token niż GitHub Secrets.

Gdy publikacja zwraca błąd, a `check-meta` świeci na zielono, sprawdź nadane
zakresy tokena:

```bash
curl "https://graph.facebook.com/v23.0/me/permissions?access_token=<META_ACCESS_TOKEN>"
```

Objawy i przyczyny:

| objaw | przyczyna |
|---|---|
| `403` na `POST /<page>/photos`, odczyty działają | token bez `pages_manage_posts` |
| `instagram_business_account` puste na stronie | token bez `instagram_basic` |
| `code 190`, `subcode 463` | token wygasł lub został unieważniony |
| `code 100`, `subcode 33` na `IG_USER_ID` | złe ID albo brak dostępu do konta IG |
| `(#200) The permission(s) publish_actions are not available` | publikacja tokenem System Usera zamiast tokenem strony |

**Token System Usera nie publikuje.** Nawet z kompletem zakresów Graph odmawia
publikacji na stronie i zwraca błąd o `publish_actions` — uprawnieniu skasowanym
w 2018 roku, które z realną przyczyną nie ma nic wspólnego. Pisać wolno tokenem
**strony**, który Graph oddaje w polu `access_token` samej strony:

```bash
curl "https://graph.facebook.com/v23.0/<META_PAGE_ID>?fields=access_token&access_token=<META_ACCESS_TOKEN>"
```

Publisher robi tę wymianę sam przy budowaniu adapterów (`page_access_token`
w `src/pyldz/social/adapters/facebook.py`), więc w sekretach trzymamy dalej token
System Usera — nie podmieniaj go na token strony, bo ten drugi jest związany
z konkretną stroną i trudniej go odtworzyć.

**Znane ryzyko (spec §8, ryzyko #1):** appka w trybie Development może
ograniczać publikację/widoczność postów — możliwy App Review / weryfikacja
firmy. Wyjdzie w pilocie pierwszym realnym postem. Plan B na przejściówkę:
FB+IG czasowo w pakiecie wklejki (Meta Business Suite planuje oba naraz);
architektura systemu bez zmian.

## 2. Discord — `DISCORD_WEBHOOK_URL`

1. Discord → serwer Python Łódź → kanał ogłoszeń → ⚙️ Edytuj kanał →
   **Integracje** → **Webhooki** → **Nowy webhook**.
2. Nazwij (np. „Python Łódź bot"), ustaw kanał docelowy, **Kopiuj adres URL
   webhooka** → to jest `DISCORD_WEBHOOK_URL`.

**Weryfikacja** (wyśle testową wiadomość na kanał — użyj kanału testowego
albo skasuj post po chwili):

```bash
curl -H "Content-Type: application/json" -d '{"content":"test webhooka gk-sm"}' "<DISCORD_WEBHOOK_URL>"
```

## 3. YouTube — OAuth (lokalnie, bez GitHub Secrets w v1)

Live jest zakładany **w sesji planowania na Twojej maszynie** (gk-sm-4),
nie w CI — więc cron nie potrzebuje żadnych sekretów YT. Wystarczy istniejący
projekt Google Cloud pyldz (ten od Sheets):

1. console.cloud.google.com → projekt pyldz → **APIs & Services → Library →
   YouTube Data API v3 → Enable**.
2. Istniejący klient OAuth (`.client_secret.json` w katalogu repo) wystarczy —
   to ten sam plik, którego używa `pyldz generate`.
3. Konto Google, którym się zalogujesz, musi mieć dostęp do kanału YouTube
   Python Łódź (właściciel/menedżer kanału), a kanał musi mieć **włączone
   transmisje na żywo** (YouTube Studio → Ustawienia → Kanał → Funkcje).
4. Pierwsze uruchomienie otwiera przeglądarkę (OAuth), scope
   `youtube.force-ssl`; token trafia do `.yt_token.json` (gitignored):
   ```bash
   uv run pyldz social yt-create-live --title "Test gk-sm (usuń)" --start "2026-12-31 18:00"
   # oczekiwane: URL https://www.youtube.com/watch?v=... ; usuń testowy live w YouTube Studio
   ```

(Gdy kiedyś przeniesiemy zakładanie live do CI: refresh token z
`.yt_token.json` → GitHub Secrets `YT_*` — na dziś świadomie poza zakresem.)

## 4. Wpięcie sekretów

**GitHub Secrets** (repo pythonlodz.org → Settings → Secrets and variables →
Actions → New repository secret): `META_PAGE_ID`, `META_ACCESS_TOKEN`,
`IG_USER_ID`, `DISCORD_WEBHOOK_URL`. (`SITE_BASE_URL` ma dobry default —
nie trzeba go ustawiać.)

**Lokalny `.env`**: skopiuj sekcję „Social publisher" z `.env.example`
i uzupełnij te same wartości.

**Weryfikacja end-to-end:**

```bash
uv run pyldz social dry-run          # lokalnie: waliduje schedule + pokazuje payloady
gh workflow run "Social publish"     # ręczny run crona; sprawdź logi w Actions
```

Run bez postów due wypisze `nic nie jest due` — to poprawny wynik weryfikacji.
