# atw - artikel 2

## Classes
### Art_2
**Properties**
- _datum_einde_wettelijke_termijn_: Einddatum van een in de wet gestelde termijn (date).
- _wettelijke_termijn_: In een wet gestelde termijn (timedelta).
- _verlenging_termijn_: Nieuw te berekenen verlenging van de termijn (timedelta).
- _datum_einde_verlengde_termijn_: Nieuw te berekenen einddatum van een in de wet gestelde termijn met inachtneming van eventuele verlenging (date).

**Methods**
- _Art2()_: Verlengt een in de wet gestelde termijn van tenminste drie dagen zo nodig dat in de termijn ten minste twee dagen voorkomen die niet een zaterdag, zondag of een algemeen erkende feestdag zijn.