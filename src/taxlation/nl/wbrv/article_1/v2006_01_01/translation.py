#import datackasses module
from dataclasses import dataclass

@dataclass
class Artikel1:  
  """
  Dataclass voor artikel 1, WBRV
  """
  overdrachtsbelasting: bool # overdrachtsbelasting geregeld in hoofdstuk II WBRV
  assurantiebelasting: bool # assurantiebelasting geregeld in hoofdstuk III WBRV

  @property
  def belasting_van_rechtsverkeer(self):
    """
    Bepaalt of sprake is van een belasting van rechtsverkeer.

    Functie geeft aan dat sprake is van een belasting van rechtsverkeer indien de overdrachtsbelasting of assurantiebelasting van toepassing is.

    Geeft terug:
      bool
    """
    if self.overdrachtsbelasting or self.assurantiebelasting:
      return True
    else:
      return False