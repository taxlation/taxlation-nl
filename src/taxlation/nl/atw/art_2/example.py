from datetime import date, timedelta

from taxlation.nl import atw

# Voorbeeld los gebruik van Art2: 2025-12-24 startdatum en 72 uur
art2_voorbeeld= atw.Art_2(startDatum= date(2025,12,24), wettelijkeTermijn= timedelta(hours=72))
print("Verlenging van termijn met Art2", art2_voorbeeld.verlengingTermijn)
print("Einddatum na verlenging:", art2_voorbeeld.einddatum)