
#import datackasses module
from dataclasses import dataclass

#import dataclass
from .subparagraph_p.translation import Artikel15Lid1OnderdeelP

@dataclass
class Artikel15Lid1(Artikel15Lid1OnderdeelP):
  """
  Dataclass voor artikel 15, lid 1 WBRV
  """

  def onderdeel_p(self) -> bool:
    return self.startersvrijstelling()