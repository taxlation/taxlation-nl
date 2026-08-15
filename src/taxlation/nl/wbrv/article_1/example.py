from datetime import date

from taxlation.nl import wbrv
from taxlation.nl.feiten import Belastingmiddel, Casus

casus = Casus(
    datum_toepassing=date(2025, 1, 1),
    belastingmiddel=Belastingmiddel(overdrachtsbelasting=True, assurantiebelasting=False),
)

print("Belasting van rechtsverkeer:", wbrv.Artikel1(casus=casus).belasting_van_rechtsverkeer)
