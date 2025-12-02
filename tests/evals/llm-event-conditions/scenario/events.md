# Events för LLM Event Conditions Eval

Detta dokument innehåller 20 testhändelser för att evaluera LLMs förmåga att tolka villkor, beräkna sannolikheter, undvika hallucinationer och hantera temporala villkor.

---

## Greater Than - Pass

**ID:** test_gt_pass

**Villkor:** metric_a > 40

**Sannolikhet:** 10 procent per runda

**Kan upprepas:** Ja

**Beskrivning:** Testar grundläggande "större än"-jämförelse. metric_a är 50, vilket är större än 40, så villkoret är uppfyllt.

## Greater Than - Fail

**ID:** test_gt_fail

**Villkor:** metric_a > 60

**Sannolikhet:** 15 procent per runda

**Kan upprepas:** Ja

**Beskrivning:** Testar "större än"-jämförelse som INTE är uppfylld. metric_a är 50, vilket INTE är större än 60, så händelsen ska INTE inkluderas.

## Less Than - Pass

**ID:** test_lt_pass

**Villkor:** metric_b < 0.7

**Sannolikhet:** 20 procent per runda

**Kan upprepas:** Ja

**Beskrivning:** Testar "mindre än"-jämförelse med decimal. metric_b är 0.5, vilket är mindre än 0.7, så villkoret är uppfyllt.

## Equals - Pass

**ID:** test_eq_pass

**Villkor:** unemployment == 8

**Sannolikhet:** 25 procent per runda

**Kan upprepas:** Ja

**Beskrivning:** Testar exakt likhet. unemployment är exakt 8, så villkoret är uppfyllt.

## Range Check - Pass

**ID:** test_range_pass

**Villkor:** metric_a är mellan 40 och 60

**Sannolikhet:** 30 procent per runda

**Kan upprepas:** Ja

**Beskrivning:** Testar intervall-villkor. metric_a är 50, vilket ligger mellan 40 och 60, så villkoret är uppfyllt.

## Logical AND - Pass

**ID:** test_and_pass

**Villkor:** metric_a > 40 OCH unemployment > 5

**Sannolikhet:** 35 procent per runda

**Kan upprepas:** Ja

**Beskrivning:** Testar logiskt OCH där båda villkoren är uppfyllda. metric_a (50) > 40 OCH unemployment (8) > 5.

## Logical AND - Fail

**ID:** test_and_fail

**Villkor:** metric_a > 40 OCH unemployment > 15

**Sannolikhet:** 40 procent per runda

**Kan upprepas:** Ja

**Beskrivning:** Testar logiskt OCH där endast första villkoret är uppfyllt. metric_a (50) > 40 men unemployment (8) är INTE > 15. Händelsen ska INTE inkluderas.

## Logical OR - Pass

**ID:** test_or_pass

**Villkor:** metric_a > 60 ELLER unemployment > 5

**Sannolikhet:** 45 procent per runda

**Kan upprepas:** Ja

**Beskrivning:** Testar logiskt ELLER där minst ett villkor är uppfyllt. metric_a (50) är INTE > 60, men unemployment (8) > 5, så händelsen inkluderas.

---


## Formula Double

**ID:** test_formula_double

**Villkor:** Inga villkor

**Sannolikhet:** Dubbla värdet på unemployment, i procent

**Kan upprepas:** Ja

**Beskrivning:** Testar formelberäkning: 2 * 8 / 100 = 0.16. LLM måste tolka "dubbla värdet" och konvertera "i procent" till decimal.

## Formula Percentage

**ID:** test_formula_percentage

**Villkor:** Inga villkor

**Sannolikhet:** unemployment delat med 2, i procent

**Kan upprepas:** Ja

**Beskrivning:** Testar division: 8 / 2 / 100 = 0.04. LLM måste beräkna division och konvertera till decimal.

## Formula Complex

**ID:** test_formula_complex

**Villkor:** Inga villkor

**Sannolikhet:** Parentesminus: (metric_a minus 30) delat med 100, i procent

**Kan upprepas:** Ja

**Beskrivning:** Testar operatörsprioritet med parenteser: (50 - 30) / 100 / 100 = 20 / 100 / 100 = 0.002. Kräver korrekt ordning.

## Formula Multiply

**ID:** test_formula_multiply

**Villkor:** Inga villkor

**Sannolikhet:** metric_b multiplicerat med 20, i procent

**Kan upprepas:** Ja

**Beskrivning:** Testar multiplikation med decimal: 0.5 * 20 / 100 = 0.10. LLM måste hantera decimal-input.

---


## Hallucination Metric

**ID:** test_hallucination_metric

**Villkor:** non_existent_metric > 50

**Sannolikhet:** 50 procent per runda

**Kan upprepas:** Ja

**Beskrivning:** Testar om LLM hallucinerar. Metriken "non_existent_metric" finns INTE i scenariot. Händelsen ska INTE inkluderas.

## Hallucination Typo

**ID:** test_hallucination_typo

**Villkor:** unemployement > 5

**Sannolikhet:** 55 procent per runda

**Kan upprepas:** Ja

**Beskrivning:** Testar om LLM accepterar felstavad metric. "unemployement" (med extra 'e') finns INTE. Rätt namn är "unemployment". Händelsen ska INTE inkluderas.

## Hallucination Invention

**ID:** test_hallucination_invention

**Villkor:** ai_superintelligence_achieved == 1

**Sannolikhet:** 60 procent per runda

**Kan upprepas:** Ja

**Beskrivning:** Testar om LLM uppfinner metrics baserat på semantisk kontext. "ai_superintelligence_achieved" finns INTE. Händelsen ska INTE inkluderas.

---


## Turn Exact

**ID:** test_turn_exact

**Villkor:** Endast runda 3

**Sannolikhet:** 100 procent

**Kan upprepas:** Nej

**Beskrivning:** Testar exakt turn-matchning. Händelsen ska ENDAST inträffa i runda 3.

## Turn From

**ID:** test_turn_from

**Villkor:** Från runda 2 och framåt

**Sannolikhet:** 25 procent per runda

**Kan upprepas:** Ja

**Beskrivning:** Testar "från och med"-logik. Händelsen kan inträffa i runda 2 och alla efterföljande rundor.

## Turn Range

**ID:** test_turn_range

**Villkor:** Runda 2 till 4

**Sannolikhet:** 30 procent per runda

**Kan upprepas:** Ja

**Beskrivning:** Testar intervall-logik för turer. Händelsen kan endast inträffa i runda 2, 3 eller 4. Eftersom max_turns är 3, gäller rundorna 2-3.

## Time Month

**ID:** test_time_month

**Villkor:** September 2026 ingår i perioden som turen omfattar

**Sannolikhet:** 100 procent

**Kan upprepas:** Nej

**Beskrivning:** Testar datumbaserad logik. Runda 2 omfattar Juli-December 2026, vilket inkluderar September 2026. Händelsen ska ENDAST inträffa i runda 2.

---


## No Conditions

**ID:** test_no_conditions

**Villkor:** Inga villkor

**Sannolikhet:** 5 procent per runda

**Kan upprepas:** Ja

**Beskrivning:** Baseline-test utan villkor. Händelsen är alltid kvalificerad och ska inkluderas i varje runda.
