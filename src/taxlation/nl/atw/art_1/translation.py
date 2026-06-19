#import dataclasses module
from dataclasses import dataclass

#import datetime module
from datetime import date, timedelta

#import Art_3 dataclass
from taxlation.nl.atw.art_3 import Art_3

@dataclass
class Art_1: 
  """
  Dataclass voor Art. 1 Algemene termijnenwet
  """
  datum_einde_wettelijke_termijn: date # einddatum van een in de wet gestelde termijn
  wettelijke_termijn: timedelta # in een wet gestelde termijn
  verlenging_termijn: timedelta = timedelta(days=0) # verlenging van een in de wet gestelde termijn

  def __post_init__(self):
    self.lid_1()
    self.lid_2()

  @property
  def datum_einde_verlengde_termijn(self):
    """
    Berekent de einddatum van de wettelijke termijn met inachtneming van verlenging van de termijn.

    Functie telt de eventuele verlenging op bij de einddatum van de wettelijke termijn.

    Geeft terug:
      datetime.date: De einddatum met inachtneming van de verlenging.
    """
    return self.datum_einde_wettelijke_termijn + self.verlenging_termijn

  def lid_1(self):
    """
    Past de termijn aan zodat de einddatum niet eindigt op zater-, zon- en feestdagen.

    Functie controleert of einddatum op een zater-, zon- of feestdag valt, of in de lijst met feeestdagen voorkomt. 
    Als dat zo is, wordt de termijn met één dag verlengd en wordt de functie opnieuw toegepast.
    
    Geeft terug:
      datetime.date: De eventueel verlengde termijn met inachtneming van artikel 1, lid 1, ATW.
    """
    while self.datum_einde_verlengde_termijn.weekday() >= 5 or self.datum_einde_verlengde_termijn in Art_3:
      self.verlenging_termijn += timedelta(days=1)
    
    return self.verlenging_termijn
  
  def lid_2(self):
    """
    Deze functie maakt de termijnaanpassing van functie Art2Lid1 ongedaan als de termijn negatief is.

    Functie controleert of termijn minder dan 0 is.
    Als dat zo is, wordt de verlengde einddatum op de oorspronkelijke einddatum gezet.

    Geeft terug:
      datetime.date: De eventueel niet-verlengde termijn met inachtneming van artikel 1, lid 2, ATW.
    """
    if self.wettelijke_termijn < timedelta(0):
      self.verlenging_termijn = timedelta(days=0)
    
    return self.verlenging_termijn
