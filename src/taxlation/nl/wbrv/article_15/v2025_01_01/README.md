# WBRV - Artikel 15

## Classes

### Artikel15
Slechts container en omvat dus geen properties of methods.

### Lid1
**Properties**
- _onderdeel_p_: dataclass van onderdeel_p (dataclass).
**Methods**
- _vrijstelling_: Stelt vast of een vrijstelling van toepassing is (bool).


### OnderdeelP
**Properties**
- _woning_: Of een woning wordt verkregen of rechten waaraan deze is onderworpen of van rechten van lidmaatschap als bedoeld in artikel 4, eerste lid, onderdeel b, voor zover deze laatste rechten betrekking hebben op een woning wordt verkregen (bool).
- _verkrijger_natuurlijk_persoon_: Of de verkrijger een natuurlijk persoon is (bool).
- _verkrijger_leeftijd_: Leeftijd van de verkrijger (int).
- _verkrijger_vrijstelling_niet_eerder_toegepast_: Of de verkrijger de vrijstelling eerder heeft toegepast (bool).
- _verkrijger_niet_eerder_toegepast_verklaring_: Of de verkrijger voorafgaand aan de verkrijging heeft verklaard de vrijstelling niet eerder te hebben toegepast (bool).
- _verkrijger_woning_hoofdverblijf_: Of de verkrijger de woning anders dan tijdelijk als hoofdverblijf gaat gebruiken (bool).
- _verkrijger_hoofdverblijf_verklaring_: Of de verkrijger voorafgaand aan de verkrijging heeft verklaard de woning anders dan tijdelijk als hoofdverblijf te gaan gebruiken (bool).
- _woning_waarde_: De waarde van de woning (int).
- _aanhorigheden_waarde_: De waarde van de bij de woning behorende aanhorigheden (int)

**Methods**
- _startersvrijstelling_: Stelt vast of de startersvrijstelling van toepassing is (bool).