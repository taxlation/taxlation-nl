#import dataclasses module
from dataclasses import dataclass

#import datetime module
from datetime import date, timedelta

#import Art3 dataclass
from taxlation.nl.atw.art_3 import Art_3

@dataclass
class Art_1: 
  """
  Dataclass voor Art. 1 Algemene termijnenwet
  """
  startDatum: date # startdatum
  wettelijkeTermijn: timedelta # in een wet gestelde termijn
  verlengingTermijn: timedelta = timedelta(days=0) # verlenging van termijn

  def __post_init__(self):
    self.lid_1()
    self.lid_2()

  @property
  def einddatum(self):
    """
    Berekent de einddatum van de gestelde termijn.

    Functie telt het wettelijke termijn en de eventuele verlenging op bij de startdatum.

    Geeft terug:
      datetime.date: De einddatum met inachtneming van de wettelijke termijn en verlenging.
    """
    return self.startDatum + self.wettelijkeTermijn + self.verlengingTermijn

  def lid_1(self):
    """
    Past de termijn aan zodat de einddatum niet eindigt op zater-, zon- en feestdagen.

    Functie controleert of einddatum op een zater-, zon- of feestdag valt, of in de lijst met feeestdagen voorkomt. 
    Als dat zo is, wordt de termijn met één dag verlengd en wordt de functie opnieuw toegepast.
    
    Geeft terug:
      datetime.date: De eventueel verlengde termijn met inachtneming van artikel 1, lid 1, ATW.
    """
    while self.einddatum.weekday() >= 5 or self.einddatum in Art_3:
      self.verlengingTermijn += timedelta(days=1)
    
    return self.verlengingTermijn
  
  def lid_2(self):
    """
    Deze functie maakt de termijnaanpassing van functie Art2Lid1 ongedaan als de termijn negatief is.

    Functie controleert of termijn minder dan 0 is.
    Als dat zo is, wordt de verlengde einddatum op de oorspronkelijke einddatum gezet.

    Geeft terug:
      datetime.date: De eventueel niet-verlengde termijn met inachtneming van artikel 1, lid 2, ATW.
    """
    if self.wettelijkeTermijn < timedelta(0):
      self.verlengingTermijn = timedelta(days=0)
    
    return self.verlengingTermijn
