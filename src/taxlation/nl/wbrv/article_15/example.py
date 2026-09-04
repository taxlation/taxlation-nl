# import package
import json
from datetime import date
from taxlation.nl import wbrv

art_15_1_p_voorbeeld= wbrv.Artikel15(datum_toepassing= date(2026,1,1)).Lid1.OnderdeelP(
    woning = True,
    
    verkrijger_natuurlijk_persoon= True,
    verkrijger_leeftijd= 34,

    verkrijger_vrijstelling_niet_eerder_toegepast= True,
    verkrijger_niet_eerder_toegepast_verklaring= True,

    verkrijger_woning_hoofdverblijf= True,
    verkrijger_hoofdverblijf_verklaring= True,
    
    woning_waarde= 550000,
    aanhorigheden_waarde= 5000 
)

print("Startersvrijstelling in 2026", art_15_1_p_voorbeeld.startersvrijstelling)

art_15_lid1_voorbeeld= wbrv.Artikel15(datum_toepassing= date(2026,1,1)).Lid1(art_15_1_p_voorbeeld)

print("Vrijstelling in 2025", art_15_lid1_voorbeeld.vrijstelling)