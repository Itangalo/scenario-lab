# External Events – Cold War Endgame

## Chernobyl Disaster

**ID:** chernobyl

**Condition:** Turn is 5 or earlier

**Probability:** 25 percent per round

**Can repeat:** No

**Description:** A catastrophic nuclear reactor explosion at a Soviet nuclear plant. The disaster exposes the dangers of Soviet secrecy and institutional incompetence. Gorbachev uses it to strengthen the case for glasnost. soviet_stability should decrease, reform_momentum should increase, and public trust in Soviet institutions should erode. If the event does not occur by turn 5, the USSR avoids this particular crisis and the simulation diverges from actual history.

## US Presidential Election 1988

**ID:** us_election_1988

**Condition:** November 1988 is included in the turn being covered

**Probability:** 100 percent

**Can repeat:** No

**Description:** George H.W. Bush wins the US presidential election. The new administration initially adopts a cautious "pause" in US-Soviet relations to reassess Gorbachev's intentions, before eventually continuing engagement. us_soviet_tension may increase slightly in the short term as the new administration finds its footing.

## Arms Control Breakthrough

**ID:** arms_treaty

**Condition:** Requires us_soviet_tension <= 55

**Probability:** 20 percent per round when us_soviet_tension is 40–55, 35 percent when below 40.

**Can repeat:** Yes

**Description:** The superpowers reach a significant arms reduction agreement (INF Treaty, START negotiations, or similar). us_soviet_tension should drop notably. soviet_economic_output may benefit marginally as military spending pressure eases. Both sides gain political capital domestically.

## Satellite State Reform Initiative

**ID:** satellite_reform

**Condition:** Requires reform_momentum >= 35 and east_bloc_cohesion <= 60

**Probability:** 15 percent per round when reform_momentum is 35–49, 25 percent when 50–64, and 40 percent when 65 or higher.

**Can repeat:** Yes

**Description:** An Eastern European state (Hungary, Czechoslovakia, or East Germany) launches its own reform program or opens its borders. Each occurrence escalates the pressure on remaining hardline regimes. east_bloc_cohesion should drop, and reform_momentum should increase.

## Soviet Economic Crisis Deepens

**ID:** economic_crisis

**Condition:** Requires soviet_economic_output <= 80

**Probability:** 10 percent per round when soviet_economic_output is 70–80, 20 percent when 55–69, and 35 percent when below 55.

**Can repeat:** Yes

**Description:** A severe supply disruption, failed harvest, or industrial breakdown worsens Soviet economic conditions beyond the gradual decline. soviet_economic_output should take an additional sharp drop. soviet_stability should decrease. Public discontent rises visibly.

## Hardliner Coup Attempt

**ID:** hardliner_coup

**Condition:** Requires reform_momentum >= 55 and soviet_stability <= 45

**Probability:** 12 percent per round when conditions are met, increasing to 25 percent when soviet_stability is below 30.

**Can repeat:** No

**Description:** Conservative forces in the military, KGB, and party apparatus attempt to seize power and reverse reforms. The outcome depends on the current state: if reform_momentum is very high and the military is divided, the coup is likely to fail — which would accelerate the collapse of the old order. If the hardliners retain strong institutional support, the coup could succeed and set back reform dramatically.

## Popular Uprising in Eastern Europe

**ID:** popular_uprising

**Condition:** Requires east_bloc_cohesion <= 35 and reform_momentum >= 50

**Probability:** 20 percent per round when conditions are first met, 35 percent in subsequent rounds.

**Can repeat:** Yes

**Description:** Mass protests erupt in one or more Eastern European countries demanding democratic change. If the Soviet Union does not intervene, the regime in question may fall. east_bloc_cohesion should drop sharply. reform_momentum should surge. The event is inspired by and in turn inspires further movements.

## Soviet Republic Declares Sovereignty

**ID:** republic_sovereignty

**Condition:** Requires soviet_stability <= 40 and reform_momentum >= 50

**Probability:** 10 percent per round when soviet_stability is 30–40, 25 percent when below 30.

**Can repeat:** Yes

**Description:** A Soviet republic (Baltic states, Ukraine, or Georgia) declares sovereignty or independence. This directly undermines the territorial integrity of the USSR. soviet_stability should drop. The event may trigger similar declarations from other republics.

## Superpower Summit

**ID:** superpower_summit

**Condition:** Requires us_soviet_tension <= 65

**Probability:** 25 percent per round

**Can repeat:** Yes

**Description:** A high-profile summit between the US and Soviet leaders generates diplomatic momentum. Both sides make concessions or announce joint initiatives. us_soviet_tension should decrease. reform_momentum may benefit if the summit strengthens Gorbachev's domestic position.

## Western Economic Aid Package

**ID:** western_aid

**Condition:** Requires us_soviet_tension <= 40 and soviet_economic_output <= 75

**Probability:** 15 percent per round

**Can repeat:** Yes

**Description:** Western nations offer economic assistance, trade agreements, or technical cooperation to support Soviet reform. soviet_economic_output decline may slow or partially reverse. us_soviet_tension decreases further. Hardliners view this as humiliating dependence on the West.
