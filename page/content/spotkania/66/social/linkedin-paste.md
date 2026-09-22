# Pakiet LinkedIn — Python Łódź #66

LinkedIn nie jest publikowany automatem (brak API w systemie) — to wklejka do
natywnego schedulera LinkedIna. Wszystkie posty planuj na **9:00**, zgodnie
z modelem godzin: rano LinkedIn i Facebook, wieczorem Discord i Instagram.

Oznaczenia robisz ręcznie w UI (wpisując @ i wybierając profil) — scheduler
LinkedIna przyjmuje wpisy do 3 miesięcy w przód.

Tekst poniżej jest kanoniczny, identyczny z tym, co idzie na Facebooka.

---

## 1. `ogloszenie` — wt 22.09.2026, 09:00

**Grafika do załączenia:** `social/images/final/ogloszenie-4x5.png`

**Do oznaczenia:**
- Sebastian Buczyński — https://www.linkedin.com/in/sebastianbuczynski/
- Grzegorz Kocjan — https://www.linkedin.com/in/grzegorzkocjan/

**Tekst:**

```
🤔 "Jak wiadomość trafi do kolejki, to na pewno zostanie obsłużona."

🤔 "Testy przechodzą, więc system działa."

Dwa zdania, które brzmią rozsądnie - dopóki nie spotkają produkcji. O obu będziemy rozmawiać na Python Łódź #66.

📅 Środa 30 września, 18:00
📍 IndieBI, Piotrkowska 157A (Hi Piotrkowska)

⚡ Sebastian Buczyński - Największe mity w pracy z kolejkami

Ponowienia, kolejność, transakcje, Kafka vs RabbitMQ. Sebastian przechodzi przez najpopularniejsze przekonania o kolejkach i szuka kompromisu między niezawodnością a prędkością.

🧪 Grzegorz Kocjan - Najtrudniejszy test suite, jaki kiedykolwiek zbudowałem

Analiza wideo w czasie rzeczywistym, detekcje na poziomie 80-90% i testy, które muszą mierzyć jakość, a nie zgodność. Case study z pytest: podwójna parametryzacja, statystyki zbierane w trakcie, raport na końcu.

➡️ Szczegóły i zapisy: https://pythonlodz.org/spotkania/66/

💬 Discord: https://discord.gg/e4XpHMnPfJ
```

---

## 2. `live-stream` — śr 23.09.2026, 09:00

**Grafika do załączenia:** `social/images/final/live-stream-4x5.png`

**Do oznaczenia:**
- Sebastian Buczyński — https://www.linkedin.com/in/sebastianbuczynski/
- Grzegorz Kocjan — https://www.linkedin.com/in/grzegorzkocjan/

**Tekst:**

```
🔴 Nie dojedziesz do Łodzi? Python Łódź #66 puszczamy na żywo.

Obie prelekcje lecą na naszym kanale YouTube - kolejki bez mitów u Sebastiana Buczyńskiego i case study z pytest u Grzegorza Kocjana. Włącz przypomnienie na YouTube, żeby nie przegapić startu.

📅 Środa 30 września, 18:00

🔴 Transmisja: https://youtube.com/live/dDS8l_D9oIk

Na miejscu jest jednak inaczej: po prelekcjach zostajemy na rozmowy, a tego żaden stream nie odda. Jeśli możesz wpaść na Piotrkowską - wpadnij.

➡️ Szczegóły i zapisy: https://pythonlodz.org/spotkania/66/
```

---

## 3. `prelekcja-kolejki` — czw 24.09.2026, 09:00

**Grafika do załączenia:** `social/images/final/prelekcja-kolejki-4x5.png`

**Do oznaczenia:**
- Sebastian Buczyński — https://www.linkedin.com/in/sebastianbuczynski/

**Tekst:**

```
⚡ "Ponowienia wystarczą, w końcu się przetworzy."

Brzmi znajomo? To jedno z przekonań, które Sebastian Buczyński rozbiera na Python Łódź #66.

W "Największych mitach w pracy z kolejkami" przechodzimy przez rzeczy wyglądające na oczywiste - dopóki nie zobaczysz ich na produkcji:

🔹 wysłanie wiadomości po zatwierdzeniu transakcji: czy to naprawdę jest bezpieczne

🔹 czy wiadomość, która trafiła do kolejki, zawsze zostanie obsłużona

🔹 co ponowienia załatwiają, a czego nie załatwią nigdy

🔹 czym Kafka i RabbitMQ różnią się mniej, niż się o nich mówi

Wszystko z jednym pytaniem w tle: gdzie postawić granicę między niezawodnością a prędkością.

Sebastian jest Software Engineerem w Revolut, wcześniej trenerem, architektem i tech leadem. Napisał książkę o implementowaniu czystej architektury w Pythonie i prowadzi bloga breadcrumbscollector.tech.

📅 Środa 30 września, 18:00 @ IndieBI, Piotrkowska 157A

➡️ Szczegóły i zapisy: https://pythonlodz.org/spotkania/66/
```

---

## 4. `prelekcja-pytest` — pt 25.09.2026, 09:00

**Grafika do załączenia:** `social/images/final/prelekcja-pytest-4x5.png`

**Do oznaczenia:**
- Grzegorz Kocjan — https://www.linkedin.com/in/grzegorzkocjan/

**Tekst:**

```
🧪 Co robić, kiedy "test przechodzi albo nie" przestaje mieć sens?

Na Python Łódź #66 @grzegorz.kocjan opowie o najtrudniejszym test suicie, jaki zbudował: dla systemu analizy wideo w czasie rzeczywistym, rozwijanego latami praktycznie bez testów.

Problem był nietypowy. Pojedyncze detekcje są skuteczne w 80-90%, więc jeden zły wynik nie znaczy jeszcze, że system działa źle. Trzeba było mierzyć jakość całości i wyłapywać moment, w którym zmiana faktycznie powoduje regresję.

Co z tego wyszło:

🔹 podwójna parametryzacja - na poziomie nagrania i pojedynczych zdarzeń

🔹 orkiestracja schowana we fixture'ach, a same testy małe i skupione na jednej rzeczy

🔹 statystyki zbierane w trakcie uruchomienia

🔹 agregacja na końcu, pokazująca jakość całego systemu

🔹 raporty HTML i powtarzalne dane do porównań między wersjami modeli

Case study z pytest, które wychodzi daleko poza klasyczne unit testy.

📅 Środa 30 września, 18:00 @ IndieBI, Piotrkowska 157A

➡️ Szczegóły i zapisy: https://pythonlodz.org/spotkania/66/
```

---

## 5. `reminder-agenda` — pon 28.09.2026, 09:00

**Grafika do załączenia:** `social/images/final/reminder-agenda-4x5.png`

**Do oznaczenia:**
- Sebastian Buczyński — https://www.linkedin.com/in/sebastianbuczynski/
- Grzegorz Kocjan — https://www.linkedin.com/in/grzegorzkocjan/

**Tekst:**

```
📅 Python Łódź #66 już w środę - oto plan wieczoru.

Środa 30 września, 18:00 @ IndieBI, Piotrkowska 157A (Hi Piotrkowska).

⚡ Największe mity w pracy z kolejkami - Sebastian Buczyński

🧪 Najtrudniejszy test suite, jaki kiedykolwiek zbudowałem - Grzegorz Kocjan

Między prelekcjami robimy przerwę, a po wszystkim zostajemy na rozmowy - dla wielu z nas to najlepsza część wieczoru.

Gospodarzem spotkania jest IndieBI. Jeśli jeszcze się nie zapisałeś, teraz jest dobry moment: zapisy pomagają nam ogarnąć miejsce.

➡️ Szczegóły i zapisy: https://pythonlodz.org/spotkania/66/
```

---

## 6. `last-call` — wt 29.09.2026, 09:00

**Grafika do załączenia:** `social/images/final/last-call-4x5.png`

**Do oznaczenia:**
- Sebastian Buczyński — https://www.linkedin.com/in/sebastianbuczynski/
- Grzegorz Kocjan — https://www.linkedin.com/in/grzegorzkocjan/

**Tekst:**

```
⏰ Ostatni dzień przed Python Łódź #66.

Jutro, środa 30 września, 18:00 @ IndieBI, Piotrkowska 157A.

⚡ Kolejki: ile z tego, co "wiadomo", zostaje po zderzeniu z produkcją - Sebastian Buczyński

🧪 Test suite dla systemu, który z natury jest niedeterministyczny - Grzegorz Kocjan

Nie dasz rady dojechać? Będzie transmisja na YouTube. Ale jeśli możesz wpaść - wpadnij, rozmowy po prelekcjach dzieją się tylko na miejscu.

➡️ Zapisy: https://pythonlodz.org/spotkania/66/
```

---

## 7. `dzien-spotkania` — śr 30.09.2026, 09:00

**Grafika do załączenia:** `social/images/final/dzien-spotkania-4x5.png`

**Do oznaczenia:**
- Sebastian Buczyński — https://www.linkedin.com/in/sebastianbuczynski/
- Grzegorz Kocjan — https://www.linkedin.com/in/grzegorzkocjan/

**Tekst:**

```
🐍 Dziś Python Łódź #66!

18:00 @ IndieBI, Piotrkowska 157A (Hi Piotrkowska). Wpadajcie spokojnie - zaczynamy od spraw organizacyjnych, więc kilka minut różnicy nikomu nie zrobi krzywdy.

⚡ Największe mity w pracy z kolejkami - Sebastian Buczyński

🧪 Najtrudniejszy test suite, jaki kiedykolwiek zbudowałem - Grzegorz Kocjan

Nie dojedziesz? Transmisja leci tutaj: https://youtube.com/live/dDS8l_D9oIk

➡️ Szczegóły: https://pythonlodz.org/spotkania/66/
```

---

## Uwagi

- Gospodarz spotkania to **IndieBI** — jeśli mają stronę firmową na LinkedInie,
  warto ich oznaczyć w postach podających lokalizację (w danych sponsora jest
  tylko `https://indiebi.com`).
- Sekcji YT Community nie generuję: przy #66 transmisja powstała ręcznie
  w Studio, a posty społecznościowe na YT nie są częścią tej kampanii.
