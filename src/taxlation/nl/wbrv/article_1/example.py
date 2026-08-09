from taxlation.nl import wbrv
from taxlation.nl.feiten import Belastingmiddel, Casus

casus = Casus(
    belastingmiddel=Belastingmiddel(overdrachtsbelasting=True, assurantiebelasting=False),
)

print("Belasting van rechtsverkeer:", wbrv.Artikel1(casus=casus).belasting_van_rechtsverkeer)
