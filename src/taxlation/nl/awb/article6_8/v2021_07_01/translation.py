#import datackasses module
from dataclasses import dataclass

#import datetime module
from datetime import date, timedelta

@dataclass
class Artikel6_8:
  """
  Dataclass voor Art. 6:8 Algemene wet bestuursrecht
  """

  datum_bekendmaking_besluit: date # de dag waarop het besluit op de voorgeschreven wijze is bekendgemaakt.

  @property
  def datum_aanvang_indieningstermijn(self):
    return self.lid_1()
  
  def lid_1(self):
    return self.datum_bekendmaking_besluit + timedelta(days=1)
    

