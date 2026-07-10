from taxlation.nl import atw

# voorbeeld gebruik van Art_3
# 2026-5-25 startdatum en 72 uur
art3_voorbeeld= atw.Artikel3(jaar=2026)
print("Algemeen erkende feestdagen", art3_voorbeeld.algemeen_erkende_feestdagen)