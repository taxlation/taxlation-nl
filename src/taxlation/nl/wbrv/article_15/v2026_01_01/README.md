# wbrv - artikel 15

## Classes

### Artikel15
- _lid_1_: Stelt vast of artikel 15, lid 1, WBRV van toepassing is (bool).

### Artikel15.Lid1
- _onderdeel_p_: Stelt vast of artikel 15, lid 1, onderdeel p, WBRV van toepassing is (bool).

### Artikel15.Lid1.OnderdeelP
- _startersvrijstelling_: Stelt vast of de startersvrijstelling van toepassing is (bool).

**Feiten** (gelezen uit de casus)
- _zaak.woning_: Of een woning wordt verkregen (bool).
- _zaak.rechten_woning_onderworpen_: Of rechten waaraan een woning is onderworpen worden verkregen (bool).
- _zaak.rechten_lidmaatschap_woning_: Of lidmaatschapsrechten met betrekking tot een woning worden verkregen (bool).
- _zaak.aanhorigheid_: Of gelijktijdig een tot de woning behorende aanhorigheid wordt verkregen (bool).
- _verkrijger.natuurlijk_persoon_: Of de verkrijger een natuurlijk persoon is (bool).
- _verkrijger.leeftijd_: Leeftijd van de verkrijger (int).
- _verkrijger.vrijstelling_eerder_toegepast_: Of de verkrijger de vrijstelling eerder heeft toegepast (bool).
- _verkrijger.verklaring_vrijstelling_: Of de verkrijger heeft verklaard de vrijstelling niet eerder te hebben toegepast (bool).
- _hoofdverblijf.woning_tijdelijk_hoofdverblijf_: Of de woning slechts tijdelijk als hoofdverblijf wordt gebruikt (bool).
- _hoofdverblijf.verklaring_hoofdverblijf_: Of de verkrijger heeft verklaard de woning anders dan tijdelijk als hoofdverblijf te gaan gebruiken (bool).
- _zaak.waarde_woning_: De waarde van de woning (int).
- _zaak.waarde_aanhorigheden_: De waarde van de aanhorigheden (int, standaard 0; verplicht zodra er een aanhorigheid is).
