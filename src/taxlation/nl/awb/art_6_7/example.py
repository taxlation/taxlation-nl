# import date module 
from datetime import date

# import atw package
from taxlation.nl import awb

# Voorbeeld los gebruik van Art_6_7: 
art_6_7_voorbeeld= awb.Art_6_7(datum_aanvang_indieningstermijn= date(2012,3,3))

print("Einddatum beslistermijn:", art_6_7_voorbeeld.datum_einde_indieningstermijn)