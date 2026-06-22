#import datackasses module
from dataclasses import dataclass

#import datetime module
from datetime import date, timedelta

@dataclass
class Art_6_7:  
  """
  Dataclass voor Art. 6:7 Algemene wet bestuursrecht
  """
  datum_aanvang_indieningstermijn: date  # datum waarop indieningstermijn aanvangt

  @property
  def datum_einde_indieningstermijn(self):
    """
    Berekent de einddatum van de indieningstermijn.

    Functie telt de termijn van zes weken op bij de einddatum van de wettelijke termijn en trekt één dag af om de datum te bepalen waarop de termijn om 23:59 eindigt.

    Geeft terug:
      datetime.date: De datum waarop de indieningstermijn eindigt.
    """
    return self.datum_aanvang_indieningstermijn + timedelta(weeks=6) - timedelta(days=1)