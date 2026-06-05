# atw - artikel 1

## Classes
### Art_1
**Properties**
- _startDatum_: start datum van een termijn (date).
- _wettelijkeTermijn_: In een wet gestelde termijn (timedelta).
- _verlengingTermijn_: Nieuw te berekenen verlenging van de termijn (timedelta).
- _eindDatum_: Nieuw te berekenen einddatum (date).

**Methods**
- _Art1Par1()_: Verlengt de termijn, als deze op een zaterdag, zondag of algemeen erkende feestdag eindigt, tot en met de eerstvolgende dag die niet een zaterdag, zondag of feestdag is.
- _Art1Par2()_: Maakt de verlenging ongedaan wanneer de termijn is bepaald door terugrekening vanaf de start van een termijn.