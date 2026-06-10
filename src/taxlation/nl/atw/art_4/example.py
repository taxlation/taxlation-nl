from datetime import date, timedelta

from taxlation.nl import atw

# Voorbeeld los gebruik van Art4: 2025-12-24 startdatum en 4 dagen
art_4_voorbeeld= atw.Art_4(einddatum_wettelijke_termijn= date(2025,12,24), wettelijke_termijn= timedelta(days=4), wettelijke_termijn_eenheid = 'dag', verlenging_termijn= timedelta(days=4))
print("Atw is niet van toepassing dan Art4:", art_4_voorbeeld.wet_geldt_niet)
print("Einddatum na eventuele verlenging:", art_4_voorbeeld.einddatum_verlengde_termijn)