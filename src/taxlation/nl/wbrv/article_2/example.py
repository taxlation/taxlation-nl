# import atw package
from taxlation.nl import wbrv

art_2_voorbeeld= wbrv.Artikel2(verkrijging= True, in_nederland_gelegen=True, onroerende_zaken= True, rechten_onroerende_zaken_onderworpen= True )

print("Belastbaar feit:", art_2_voorbeeld.overdrachtsbelasting)