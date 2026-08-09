from datetime import date

from taxlation.nl import wbrv
from taxlation.nl.feiten import Casus, Hoofdverblijf, OnroerendeZaak, Verkrijger

casus = Casus(
    datum_toepassing=date(2025, 1, 1),
    verkrijger=Verkrijger(
        natuurlijk_persoon=True,
        leeftijd=34,
        vrijstelling_eerder_toegepast=False,
        verklaring_vrijstelling=True,
    ),
    zaak=OnroerendeZaak(woning=True, waarde_woning=510000, waarde_aanhorigheden=5000),
    hoofdverblijf=Hoofdverblijf(
        woning_tijdelijk_hoofdverblijf=False,
        verklaring_hoofdverblijf=True,
    ),
)

print("Startersvrijstelling artikel 15:", wbrv.Artikel15(casus=casus).lid_1)
print("Artikel 15, lid 1:", wbrv.Artikel15.Lid1(casus=casus).onderdeel_p)
print(
    "Artikel 15, lid 1, onderdeel p:",
    wbrv.Artikel15.Lid1.OnderdeelP(casus=casus).startersvrijstelling,
)
