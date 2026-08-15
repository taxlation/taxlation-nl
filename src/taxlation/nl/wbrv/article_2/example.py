from datetime import date

from taxlation.nl import wbrv
from taxlation.nl.feiten import Casus, OnroerendeZaak, Verkrijging

casus = Casus(
    datum_toepassing=date(2025, 1, 1),
    verkrijging=Verkrijging(verkrijging=True),
    zaak=OnroerendeZaak(
        in_nederland_gelegen=True,
        onroerende_zaken=True,
        rechten_onroerende_zaken_onderworpen=True,
    ),
)

print("Belastbaar feit:", wbrv.Artikel2(casus=casus).overdrachtsbelasting)
