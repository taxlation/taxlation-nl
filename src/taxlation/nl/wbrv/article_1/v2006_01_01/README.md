# wbrv - artikel 1

## Classes

### Artikel1
- _belasting_van_rechtsverkeer_: Stelt vast of sprake is van een belasting van rechtsverkeer (bool).

**Feiten** (gelezen uit de casus)
- _belastingmiddel.overdrachtsbelasting_: Of de overdrachtsbelasting van toepassing is (bool).
- _belastingmiddel.assurantiebelasting_: Of de assurantiebelasting van toepassing is (bool).

De twee feiten vormen samen een disjunctie: zodra één van beide bekend en waar is, staat de
uitkomst vast en hoeft het andere niet te worden opgegeven.
