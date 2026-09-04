#import datackasses module
from dataclasses import dataclass

@dataclass
class Artikel2:  
  """
  Dataclass voor artikel 2, WBRV
  """
  verkrijging: bool # True indien sprake is van een verkrijging.
  in_nederland_gelegen: bool # True indien sprake is van een in Nederland gelegen onroerende zaak.
  onroerende_zaken: bool # True indien sprake is van een onroerende zaken.
  rechten_onroerende_zaken_onderworpen: bool # True indien sprake is van een recht waaraan een onroerende zaak is onderworpen.

  @property
  def overdrachtsbelasting(self) -> bool:
    """
    Bepaalt of overdrachtsbelasting wordt geheven.

    Functie geeft aan of overdrachtsbelasting wordt geheven.

    Geeft terug:
      bool
    """
    return self.lid_1()

  def lid_1(self) -> bool:
    """
    Bepaalt of sprake is van een belastbaar feit.

    Functie geeft aan of sprake is van een belastbaar feit.

    Geeft terug:
      bool
    """
    if self.verkrijging and self.in_nederland_gelegen and (self.onroerende_zaken or self.rechten_onroerende_zaken_onderworpen):
      return True
    else:
      return False