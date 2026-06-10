from datetime import date, timedelta

from taxlation.nl import atw

# voorbeeld gebruik van Art_2
# 2025-12-24 startdatum en 72 uur
art2_voorbeeld= atw.Art_2(einddatum_wettelijke_termijn= date(2025,12,27), wettelijke_termijn= timedelta(hours=72))
print("Verlenging van termijn met Art2", art2_voorbeeld.verlenging_termijn) # 3 dagen
print("Einddatum na verlenging:", art2_voorbeeld.einddatum_verlengde_termijn) # 2025-12-30  