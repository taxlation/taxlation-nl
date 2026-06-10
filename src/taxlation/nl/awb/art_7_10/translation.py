#import dataclasses module
from dataclasses import dataclass

#import datetime module
from datetime import date, timedelta

@dataclass
class Art_7_10:
  """
  Dataclass voor Art. 7:10 Algemene wet bestuursrecht
  """
  einddatum_bezwaartermijn: date # datum waarop de bezwaartermijn is verstreken 
  commissie_ingesteld: bool # commissie ingesteld als bedoeld in artikel 7:13
  beslistermijn: timedelta = timedelta(days=0) # beslistermijn va bezwaar

  def __post_init__(self):
    self.lid_1()

  @property 
  def einddatum_beslistermijn(self):
    """
    Berekent de einddatum van de beslistermijn van een bezwaar.

    Functie telt de de beslistermijn op bij de startdatum, gerekend vanaf de dag na die waarop de termijn voor het indienden van het bezwaarschrift is verstreken.

    Geeft terug:
      date: De einddatum van de beslistermijn op een bezwaar.
    """
    return self.einddatum_bezwaartermijn + self.beslistermijn
  
  def lid_1(self):
    if (self.commissie_ingesteld):
      self.beslistermijn = timedelta(weeks=12)
    else:
      self.beslistermijn = timedelta(weeks=6)
    return self.beslistermijn