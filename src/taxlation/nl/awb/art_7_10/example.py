# import date module 
from datetime import date

# import atw package
from taxlation.nl import awb

# Voorbeeld los gebruik van Art_7_10: einddatum bezwaartermijn 2021-08-13
art_7_10_voorbeeld= awb.Art_7_10(einddatum_bezwaartermijn= date(2021,8,13), commissie_ingesteld= False)

print("Einddatum beslistermijn:", art_7_10_voorbeeld.einddatum_beslistermijn)
