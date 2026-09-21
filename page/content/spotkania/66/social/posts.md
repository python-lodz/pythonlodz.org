# Posty — Python Łódź #66

## post: ogloszenie

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

### override: discord

@everyone 🐍 **Agenda Python Łódź #66 jest gotowa!**

🤔 "Jak wiadomość trafi do kolejki, to na pewno zostanie obsłużona."

🤔 "Testy przechodzą, więc system działa."

Dwa zdania, które brzmią rozsądnie - dopóki nie spotkają produkcji. O obu będziemy rozmawiać w środę.

📅 Środa 30 września, 18:00
📍 IndieBI, Piotrkowska 157A (Hi Piotrkowska)

⚡ **Sebastian Buczyński - Największe mity w pracy z kolejkami**

Ponowienia, kolejność, transakcje, Kafka vs RabbitMQ. Sebastian przechodzi przez najpopularniejsze przekonania o kolejkach i szuka kompromisu między niezawodnością a prędkością.

🧪 **Grzegorz Kocjan - Najtrudniejszy test suite, jaki kiedykolwiek zbudowałem**

Analiza wideo w czasie rzeczywistym, detekcje na poziomie 80-90% i testy, które muszą mierzyć jakość, a nie zgodność. Case study z pytest: podwójna parametryzacja, statystyki zbierane w trakcie, raport na końcu.

➡️ Szczegóły i zapisy: https://pythonlodz.org/spotkania/66/

## post: prelekcja-kolejki

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

## post: prelekcja-pytest

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

## post: reminder-agenda

📅 Python Łódź #66 już w środę - oto plan wieczoru.

Środa 30 września, 18:00 @ IndieBI, Piotrkowska 157A (Hi Piotrkowska).

⚡ Największe mity w pracy z kolejkami - Sebastian Buczyński

🧪 Najtrudniejszy test suite, jaki kiedykolwiek zbudowałem - Grzegorz Kocjan

Między prelekcjami robimy przerwę, a po wszystkim zostajemy na rozmowy - dla wielu z nas to najlepsza część wieczoru.

Gospodarzem spotkania jest IndieBI. Jeśli jeszcze się nie zapisałeś, teraz jest dobry moment: zapisy pomagają nam ogarnąć miejsce.

➡️ Szczegóły i zapisy: https://pythonlodz.org/spotkania/66/

## post: last-call

⏰ Ostatni dzień przed Python Łódź #66.

Jutro, środa 30 września, 18:00 @ IndieBI, Piotrkowska 157A.

⚡ Kolejki: ile z tego, co "wiadomo", zostaje po zderzeniu z produkcją - Sebastian Buczyński

🧪 Test suite dla systemu, który z natury jest niedeterministyczny - Grzegorz Kocjan

Nie dasz rady dojechać? Będzie transmisja na YouTube. Ale jeśli możesz wpaść - wpadnij, rozmowy po prelekcjach dzieją się tylko na miejscu.

➡️ Zapisy: https://pythonlodz.org/spotkania/66/

## post: dzien-spotkania

🐍 Dziś Python Łódź #66!

18:00 @ IndieBI, Piotrkowska 157A (Hi Piotrkowska). Wpadajcie spokojnie - zaczynamy od spraw organizacyjnych, więc kilka minut różnicy nikomu nie zrobi krzywdy.

⚡ Największe mity w pracy z kolejkami - Sebastian Buczyński

🧪 Najtrudniejszy test suite, jaki kiedykolwiek zbudowałem - Grzegorz Kocjan

Nie dojedziesz? Transmisja leci tutaj: [LINK DO LIVE]

➡️ Szczegóły: https://pythonlodz.org/spotkania/66/

### override: discord

@everyone 🐍 **Dziś Python Łódź #66!**

18:00 @ IndieBI, Piotrkowska 157A (Hi Piotrkowska). Wpadajcie spokojnie - zaczynamy od spraw organizacyjnych.

⚡ **Największe mity w pracy z kolejkami** - Sebastian Buczyński

🧪 **Najtrudniejszy test suite, jaki kiedykolwiek zbudowałem** - Grzegorz Kocjan

Nie dojedziesz? Transmisja leci tutaj: [LINK DO LIVE]
