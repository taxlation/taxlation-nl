# atw - artikel 1

## Classes
### Art_1
**Properties**
- _einddatum_wettelijke_termijn_: Einddatum van een in de wet gestelde termijn (date).
- _wettelijke_termijn_: In een wet gestelde termijn (timedelta).
- _verlenging_termijn_: Nieuw te berekenen verlenging van de termijn (timedelta).
- _einddatum_verlengde_termijn_: Nieuw te berekenen einddatum van een in de wet gestelde termijn met inachtneming van eventuele verlenging (date).

**Methods**
- _lid_1()_: Verlengt de termijn, als deze op een zaterdag, zondag of algemeen erkende feestdag eindigt, tot en met de eerstvolgende dag die niet een zaterdag, zondag of feestdag is.
- _lid_2()_: Maakt de verlenging ongedaan wanneer de termijn is bepaald door terugrekening vanaf de start van een termijn.