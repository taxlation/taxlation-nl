from datetime import date, timedelta

from taxlation.nl.atw.art_4 import Art_4

# Voorbeeld los gebruik van Art4: 2025-12-24 startdatum en 72 uur
art_4_voorbeeld= Art_4(startDatum= date(2025,12,24), wettelijkeTermijn= timedelta(hours=72), wettelijkeTermijnEenheid = 'uur', verlengingTermijn= timedelta(days=2))
print("Verlenging van termijn met Art4:", art_4_voorbeeld.verlengingTermijn)
print("Einddatum na verlenging:", art_4_voorbeeld.einddatum)