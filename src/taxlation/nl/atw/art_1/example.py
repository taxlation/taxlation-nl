from datetime import date, timedelta

# from taxlation.nl import atw
from taxlation.nl import atw

# voorbeeld gebruik van Art_1
art_1_voorbeeld= atw.Art_1(einddatum_wettelijke_termijn= date(2021,9,25, 23,59), wettelijke_termijn= timedelta(weeks=6))

print("Verlenging van termijn met Art_1", art_1_voorbeeld.verlenging_termijn) # verlenging termijn met 2 dagen
print("Einddatum na verlenging:", art_1_voorbeeld.einddatum_verlengde_termijn) # 2021-08-16 