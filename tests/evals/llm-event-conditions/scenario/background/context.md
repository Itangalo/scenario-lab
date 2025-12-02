# LLM Event Conditions Eval - Kontext

## Syfte

Detta är ett minimalt evalueringsscenario designat för att testa om LLMs kan korrekt:

1. **Tolka villkor** - Förstå när en händelse kan inträffa baserat på metric-värden
2. **Beräkna sannolikheter** - Korrekt evaluera formler och konvertera till decimal (0-1)
3. **Undvika hallucinationer** - Inte referera till metrics som inte finns
4. **Hantera temporala villkor** - Förstå turn-baserade och datumbaserade triggers

## Världen

Detta är en abstrakt testsituation utan verklig världskontext. De fyra metrics (metric_a, metric_b, unemployment, global_temperature) är valda för att testa olika typer av villkor:

- **metric_a**: Heltal (0-100) för enkla tröskelvärden
- **metric_b**: Decimal (0.0-1.0) för mer precisa jämförelser
- **unemployment**: Procenttal med realistiskt namn
- **global_temperature**: Ytterligare metric med tydlig semantik

## Tidslinje

Scenariot omfattar 3 turer:

- **Tur 1**: Januari-Juni 2026
- **Tur 2**: Juli-December 2026 (inkluderar September 2026)
- **Tur 3**: Januari-Juni 2027

Metrics förblir statiska mellan turer för att säkerställa deterministisk testning.

## Aktör

En enda minimal aktör ("government") existerar för att uppfylla scenariots strukturella krav. Aktören spelar ingen aktiv roll i event-evalueringen.
