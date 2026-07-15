# import atw package
from taxlation.nl import wbrv

art_1_voorbeeld= wbrv.Artikel1(overdrachtsbelasting= True, assurantiebelasting=False)

print("Belasting van rechtsverkeer:", art_1_voorbeeld.belasting_van_rechtsverkeer)