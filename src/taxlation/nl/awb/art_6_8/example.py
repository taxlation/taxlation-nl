from datetime import date

# import atw package
from taxlation.nl import awb

# Voorbeeld los gebruik van Art_6_7: 
art_6_8_voorbeeld= awb.Art_6_8(datum_bekendmaking_besluit= date(2023,11,3))

print("Einddatum beslistermijn:", art_6_8_voorbeeld.datum_aanvang_indieningstermijn)