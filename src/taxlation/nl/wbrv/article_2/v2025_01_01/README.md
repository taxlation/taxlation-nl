# wbrv - artikel 2

## Classes

### Artikel2
- _overdrachtsbelasting_: Stelt vast of overdrachtsbelasting wordt geheven (bool).
- _lid_1_: Stelt vast of artikel 2, lid 1, WBRV van toepassing is (bool).

### Artikel2.Lid1
- _belastbaar_feit_: Stelt vast dat overdrachtsbelasting dient te worden geheven bij een verkrijging van in Nederland gelegen onroerende zaken of van rechten waaraan deze zijn onderworpen (bool).

**Feiten** (gelezen uit de casus)
- _verkrijging.verkrijging_: Of goederen onder algemene titel of onder bijzondere titel worden verkregen (bool).
- _zaak.in_nederland_gelegen_: Of zaken in het Europese deel van het Koninkrijk der Nederlanden zijn gelegen (bool).
- _zaak.onroerende_zaken_: Of het eigendom wordt verkregen van zaken die onroerend zijn volgens Burgerlijk Wetboek Boek 3 (bool).
- _zaak.rechten_onroerende_zaken_onderworpen_: Of rechten worden verkregen waaraan zaken die onroerend zijn volgens Burgerlijk Wetboek Boek 3 zijn onderworpen (bool).

De laatste twee feiten vormen samen een disjunctie: zodra één van beide bekend en waar is, staat
dat deel van de voorwaarde vast en hoeft het andere niet te worden opgegeven.
