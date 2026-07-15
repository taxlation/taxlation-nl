# import atw package
from taxlation.nl import wbrv

art_15_1_p_voorbeeld= wbrv.Artikel15(
    woning= True, 
    rechten_woning_onderworpen= False, 
    rechten_lidmaatschap_woning= False,
    
    natuurlijk_persoon= True,
    leeftijd= 34,

    vrijstelling_niet_toegepast= True,
    verklaring_vrijstelling= True,

    woning_hoofdverblijf= True,
    verklaring_hoofdverblijf= True,
    
    waarde_woning= 510000,
    waarde_aanhorigheden= 5000 
)

print("Startersvrijstelling:", art_15_1_p_voorbeeld.lid_1)