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
  natuurlijk_persoon: bool = None
  leeftijd: int = None
  vrijstelling_niet_toegepast: bool = None
  verklaring_vrijstelling: bool = None
  woning_hoofdverblijf: bool = None
  verklaring_hoofdverblijf: bool = None
  waarde_woning: int = None
  waarde_aanhorigheden: int = None

  def startersvrijstelling(self) -> bool:
    if((self.woning or self.rechten_woning_onderworpen or self.rechten_lidmaatschap_woning) and
       (self.natuurlijk_persoon == True and self.leeftijd >= 18 and self.leeftijd < 35) and
       (self.vrijstelling_niet_toegepast == True and self.verklaring_vrijstelling == True) and # 
        (self.woning_hoofdverblijf == True and self.verklaring_hoofdverblijf == True) and 
       ((self.waarde_woning + self.waarde_aanhorigheden) <= 525000) 
       ):
      return True
    else:
      return False
