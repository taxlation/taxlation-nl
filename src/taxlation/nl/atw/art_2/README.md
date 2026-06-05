# atw - artikel 2

## Classes
### Art_2
**Properties**
- _startDatum_: start datum van een termijn (date).
- _wettelijkeTermijn_: In een wet gestelde termijn (timedelta).
- _verlengingTermijn_: Nieuw te berekenen verlenging van de termijn (timedelta).
- _eindDatum_: Nieuw te berekenen einddatum (date).

**Methods**
- _Art2()_: Verlengt een in de wet gestelde termijn van tenminste drie dagen zo nodig dat in de termijn ten minste twee dagen voorkomen die niet een zaterdag, zondag of een algemeen erkende feestdag zijn.
