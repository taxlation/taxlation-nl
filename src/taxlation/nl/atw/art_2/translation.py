from dataclasses import dataclass
from datetime import date, timedelta
from taxlation.nl.atw.art_3.translation import Art_3

@dataclass
class Art_2:  
  """
  Dataclass voor Art. 2 Algemene termijnenwet
  """
  startDatum: date # startdatum
  wettelijkeTermijn: timedelta # in een wet gestelde termijn
  verlengingTermijn: timedelta = timedelta(days=0) # verlenging van termijn
  
  def __post_init__(self):
    self.art_2()

  @property
  def einddatum(self):
    """
    Berekent de einddatum van de gestelde termijn.

    Functie telt het wettelijke termijn en de eventuele verlenging op bij de startdatum.

    Geeft terug:
      date: De einddatum met inachtneming van de wettelijke termijn en verlenging.
    """
    return self.startDatum + self.wettelijkeTermijn + self.verlengingTermijn

  def art_2(self):
    """
    Verlengt de termijn in geval de termijn ten minste drie dagen is maar niet bestaat uit twee werkdagen.

    Deze functie controleert of de termijn tenminste drie dagen is. 
    Als dat het geval is, wordt zo nodig de termijn zoveel verlengd dat daarin ten minste twee dagen voorkomen die niet een zaterdag, zonder of algemeen erkende feestdag zijn.
    
    Geeft terug:
     timedelta: De verlenging van de termijn.
    """
    if (self.einddatum - self.startDatum) >= timedelta(days=3):
      huidige_datum = self.startDatum
      werk_dagen = 0

      while (huidige_datum <= self.einddatum):
        if huidige_datum.weekday() < 5 and huidige_datum not in Art_3:
          werk_dagen += 1
        huidige_datum += timedelta(days=1)

      while werk_dagen < 2:
        self.verlengingTermijn += timedelta(days=1)
        if self.einddatum.weekday() < 5  and self.einddatum not in Art_3:
          werk_dagen +=1

      return self.verlengingTermijn