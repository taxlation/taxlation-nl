# awb - artikel 7:10

## Classes

### Art_7_10
**Properties**
- _datum_einde_bezwaartermijn_: Datum waarop de termijn voor het indienen van een bezwaarschrift is verstreken (date).
- _commissie_ingesteld_: Indien een commissie als bedoeld in artikel 7:13 is ingesteld (bool).
- _termijn_beslissing_bezwaar_: Termijn voor de beslissing op bezwaar (timedelta).
- _datum_einde_beslistermijn_: Nieuw te berekenen einddatum voor de beslissing op bezwaar (date).
- _datum_verzoek_verzuim_: Datum waarop de indiender is verzocht een verzuim als bedoeld in artikel 6:6 Awb te herstellen (date).
- _termijn_verzoek_verzuim_: Termijn voor het herstel van het verzuim (timedelta)
- _datum_herstel_verzuim_: Datum waarop het verzuim is hersteld (date).
- _termijn_opschorten: Nieuw te berekenen termijn van het opschorten van de beslistermijn (timedelta).
- _termijn_verdagen_: Termijn van het verdagen van de beslistermijn (timedelta).
- _termijn_verder_uitstel_: Termijn van het verder uitstel van de beslistermijn (timedelta).
- _instemming_alle_belanghebbenden_: Of alle belanghebbende met verder uitstel instemmen (bool).
- _instemming_indiender_: Of de indiener met verder uitstel instemt (bool).
- _andere_belanghebbende_niet_geschaad_: Of andere belanghebbende dan de indiender door verder uitstel niet in hun belangen kunnen worden geschaad.
- _naleving_wettelijke_procedurevoorschriften_: Of verder uitstel nodig is in verband met de naleving van wettelijke procedurevoorschriften.


**Methods**
- _lid_1_: Bepaalt dat de beslistermijn 12 weken bedraagt indien een commissie is ingesteld. Indien geen commissie is ingesteld, wordt een beslistermijn van 6 weken gehanteerd.
- _lid_2_: Schort de beslistermijn op indien sprake is van een herstelverzuim.
- _lid_3_: Verdaagt de beslistermijn met ten hoogste 6 weken.
- _lid_4_: Stelt de beslistermijn uit zodra aan de voorwaarden van onderdeel a, b of c wordt voldaan.