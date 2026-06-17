# import date module 
from datetime import date, timedelta

# import atw package
from taxlation.nl import awb

# Voorbeeld los gebruik van Art_7_10: einddatum bezwaartermijn 2021-08-13 met verzoek herstel 2021-09-01
art_7_10_voorbeeld= awb.Art_7_10(
  datum_einde_bezwaartermijn= date(2021,8,13),
  commissie_ingesteld= False,
  datum_verzoek_verzuim = date(2021,9,1),
  termijn_verzoek_verzuim = timedelta(days=2),
  # datum_herstel_verzuim = date(2021,9,2)
  termijn_verdagen=timedelta(days=2),
  termijn_verder_uitstel= timedelta(days=1),
  instemming_alle_belanghebbenden= False
)

print("Einddatum beslistermijn:", art_7_10_voorbeeld.datum_einde_beslistermijn)
