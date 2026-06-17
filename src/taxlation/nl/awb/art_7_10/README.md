# awb - artikel 7:10

## Classes

### Art_7_10
**Properties**
- _einddatum_bezwaartermijn_: Datum waarop de termijn voor het indienen van een bezwaarschrift is verstreken (date).
- _commissie_ingesteld_: Indien een commissie als bedoeld in artikel 7:13 is ingesteld (bool).
- _beslistermijn_: Beslistermijn voor de beslissing op bezwaar (timedelta).
- _einddatum_beslistermijn_: Nieuw te berekenen einddatum voor de beslissing op bezwaar (date).

**Methods**
- _lid_1_: Bepaalt dat de beslistermijn 12 weken bedraagt indien een commissie is ingesteld. Indien geen commissie is ingesteld, wordt een beslistermijn van 6 weken gehanteerd.
