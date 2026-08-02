
#import datackasses module
from dataclasses import dataclass

#import dataclass
from .paragraph_1.translation import Artikel15Lid1, Artikel15Lid1OnderdeelP

@dataclass
class Artikel15(Artikel15Lid1):
  """
  Dataclass voor artikel 15 WBRV
  """
  
  @property
  def lid_1(self) -> bool:
    """
    Bepaalt of de verkrijging is vrijgesteld.
    Geeft terug:
      bool
    """
    return self.onderdeel_p()