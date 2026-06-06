from datetime import date, timedelta

from taxlation.nl.atw.art_1 import Art_1

# Voorbeeld los gebruik van Art1: 2025-12-24 startdatum en 72 uur
art_1_voorbeeld= Art_1(startDatum= date(2025,12,24), wettelijkeTermijn= timedelta(hours=72))

print("Verlenging van termijn met Art_1", art_1_voorbeeld.verlengingTermijn)
print("Einddatum na verlenging:", art_1_voorbeeld.einddatum)