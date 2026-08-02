#import datackasses module
from dataclasses import dataclass

@dataclass (kw_only= True)
class Artikel15Lid1OnderdeelP:  
  """
  Dataclass voor artikel 15, lid 1, onderdeel p, WBRV
  """
  woning: bool = None # True indien sprake is van een verkrijging.
  rechten_woning_onderworpen: bool = None # True indien sprake is van een in Nederland gelegen onroerende zaak.
  rechten_lidmaatschap_woning: bool = None # True indien sprake is van een onroerende zaken.
  aanhorigheid: bool  = None # True indien gelijktijdig een aanhorigheid wordt verkregen.
  natuurlijk_persoon: bool # True indien sprake is van een natuurlijk persoon
  leeftijd: int # Leeftijd
  vrijstelling_eerder_toegepast: bool # True indien vrijstelling eerder is toegepast.
  verklaring_vrijstelling: bool # True indien verklaring van verkrijger niet eerder startersvrijstelling heeft toegepast.
  woning_tijdelijk_hoofdverblijf: bool # True indien de verkrijger de woning anders dan tijdelijk als hoofdverblijf gaat gebruiken.
  verklaring_hoofdverblijf: bool # True indien verklaring van verkrijger de woning anders dan tijdelijk als hoofdverblijf gaat gebruiken.
  waarde_woning: int # Waarde woning
  waarde_aanhorigheden: int = 0 # Waarde aanhorigheid

  def startersvrijstelling(self) -> bool:
    if(((self.woning or self.rechten_woning_onderworpen or self.rechten_lidmaatschap_woning) or ((self.woning or self.rechten_woning_onderworpen or self.rechten_lidmaatschap_woning) and self.aanhorigheid)) and
       (self.natuurlijk_persoon == True and self.leeftijd >= 18 and self.leeftijd < 35) and
       (self.vrijstelling_eerder_toegepast == False and self.verklaring_vrijstelling == True) and # 
        (self.woning_tijdelijk_hoofdverblijf == False and self.verklaring_hoofdverblijf == True) and 
       ((self.waarde_woning + self.waarde_aanhorigheden) <= 525000) 
       ):
      return True
    else:
      return False
