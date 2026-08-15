# import package
from datetime import date
from taxlation.nl import wbrv

art_15_1_p_voorbeeld= wbrv.Artikel15(datum_toepassing= date(2025,1,1)).Lid1.OnderdeelP(
    rechten_lidmaatschap_woning= True,
    aanhorigheid = True,
    
    natuurlijk_persoon= True,
    leeftijd= 34,

    vrijstelling_eerder_toegepast= False,
    verklaring_vrijstelling= True,

    woning_tijdelijk_hoofdverblijf= False,
    verklaring_hoofdverblijf= True,
    
    waarde_woning= 520000,
    waarde_aanhorigheden= 5000 
)

print("Startersvrijstelling artikel 15, lid 1, onderdeel p:", art_15_1_p_voorbeeld.startersvrijstelling())

art_15_lid1_voorbeeld= wbrv.Artikel15(datum_toepassing= date(2025,1,1)).Lid1(art_15_1_p_voorbeeld)
print("Vrijstelling artikel 15, lid 1:", art_15_lid1_voorbeeld.vrijstelling())


# Article_15_1_p_voorbeeld= wbrv.Artikel15Lid1OnderdeelP(
#     woning= True, 
    
#     natuurlijk_persoon= True,
#     leeftijd= 34,

#     vrijstelling_eerder_toegepast= False,
#     verklaring_vrijstelling= True,

#     woning_tijdelijk_hoofdverblijf= False,
#     verklaring_hoofdverblijf= True,
    
#     waarde_woning= 510000,
#     waarde_aanhorigheden= 5000 
# )

# print("Startersvrijstelling artikel 15, lid 1, onderdeel p:", Article_15_1_p_voorbeeld.startersvrijstelling())