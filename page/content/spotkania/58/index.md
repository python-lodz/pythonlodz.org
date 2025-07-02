---
title: "Meetup #58"
date: 2025-05-28T18:00:00+02:00
time: "18:00"
place: "indiebi"
---
<img src="featured.png" alt="Infographic" />

## Informacje

**📅 data:** 2025-05-28</br>
**🕕 godzina:** 18:00</br>
**📍 miejsce:** indiebi</br>
 ➡️ [**LINK DO ZAPISÓW**](https://www.meetup.com/python-lodz/events/306971418/) ⬅️

## Prelekcje

### Pythonowa konfiguracja, która przyprawi Cię o dreszcze (w dobry sposób, obiecuję!)
{{< speaker speaker_id="grzegorz-kocjan" >}}
Konfiguracja — wszyscy jej potrzebujemy, wszyscy jej nienawidzimy. A mimo to, w każdym projekcie przynajmniej raz udaje nam się ją zepsuć.  
  
Przez lata widziałem już wszystko: ręczne pliki konfiguracyjne tworzone dla każdego możliwego środowiska, upychanie setek parametrów w jednym pliku JSON, ręczne odczytywanie zmiennych środowiskowych bez żadnej kontroli typów, czy pipeline’y wywracające się przez brakujący przecinek. Ale po dekadzie męki w końcu trafiłem na rozwiązanie: pydantic-settings.  
  
Dzięki Pydantic mamy konfigurację, która jest:  
✅ Dokładnie typowana (koniec z zastanawianiem się, czy "timeout" to rzeczywiście integer!)  
✅ Elastyczna (działa płynnie na lokalnych maszynach, w Dockerze, Kubernetesie i chmurze)  
✅ Łatwa do walidacji (unikniesz awarii w runtime z powodu wpisania „True” zamiast True)  
✅ Świetna do testów (tak, zahaczymy też o sztuczki z pytest)  
  
ALE nie zamierzam tu omawiać podstaw pydantic-settings. Zamiast tego zanurzymy się w zaawansowane typowanie, żeby stworzyć superrestrykcyjną konfigurację, w której nie da się popełnić błędu — taką, która przetrwa dłużej niż jakikolwiek framework JavaScript. Dodatkowo pokażę, jak używać jej w projekcie bez polegania na stanie globalnym, opierając się na sprawdzonych w boju zasadach, które zebrałem przez lata.  
  
Z tego wystąpienia dowiesz się:  
🎯 Dlaczego większość tradycyjnych metod konfiguracji to strzał w kolano  
🎯 Jak zbudować konfigurację tak solidną, że nic jej nie wytrąci z rytmu  
🎯 Jak porządnie przetestować konfigurację i jej użycie (żeby nie rozpadła się na produkcji)  
🎯 Jakie sekrety Pydantic może jeszcze przed Tobą skrywać   
  
Jeśli uważasz, że konfiguracja jest nudna, spróbuj przesiedzieć tę prezentację i nie poczuć przy tym chociaż odrobiny ekscytacji. Najgorszy scenariusz? Wychodzisz z mniejszą liczbą koszmarów związanych z configiem. Najlepszy? Masz wreszcie konfigurację, która po prostu działa.  
  
P.S. Te techniki wykraczają poza samą konfigurację — prawdopodobnie wykorzystasz je także w innych częściach swojego projektu! 🚀

### Programista zoptymalizował aplikację, ale nikt mu nie pogratulował bo była w Pythonie 😔
{{< speaker speaker_id="sebastian-buczynski" >}}
  
Wokół tematu wydajności w Pythonie narosło wiele mitów. Rozwiejmy te fałszywe przekonania opierając się na twardych danych.  
  
Porozmawiajmy jak być lepszym inżynierem oprogramowania w ciągle zmieniającym się świecie, wymagającym podejmowania decyzji i balansowania między różnymi wymaganiami.

## Sponsorzy
{{< article link="/sponsorzy/indiebi/" >}}

{{< article link="/sponsorzy/sunscrapers/" >}}
