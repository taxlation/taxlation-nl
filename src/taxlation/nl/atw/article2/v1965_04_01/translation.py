#import dataclasses module
from dataclasses import dataclass

#import datetime module
from datetime import date, timedelta

#import Artikel3 dataclass
from taxlation.nl.atw.article3 import Artikel3

@dataclass
class Artikel2:  
  """
  Dataclass voor Art. 2 Algemene termijnenwet
  """
  datum_einde_wettelijke_termijn: date # einddatum van een in de wet gestelde termijn
  wettelijke_termijn: timedelta # in een wet gestelde termijn
  verlenging_termijn: timedelta = timedelta(days=0) # verlenging van een in de wet gestelde termijn
 
  def __post_init__(self):
    self.art_2()

  @property
  def datum_einde_verlengde_termijn(self):
    """
    Berekent de einddatum van de wettelijke termijn met inachtneming van verlenging van de termijn.

    Functie telt de eventuele verlenging op bij de einddatum van de wettelijke termijn.

    Geeft terug:
      date: De einddatum met inachtneming van de verlenging.
    """
    return self.datum_einde_wettelijke_termijn + self.verlenging_termijn

  def art_2(self):
    """
    Verlengt de termijn in geval de termijn ten minste drie dagen is maar niet bestaat uit twee werkdagen.

    Deze functie controleert of de termijn tenminste drie dagen is. 
    Als dat het geval is, wordt zo nodig de termijn zoveel verlengd dat daarin ten minste twee dagen voorkomen die niet een zaterdag, zonder of algemeen erkende feestdag zijn.
    
    Geeft terug:
     timedelta: De verlenging van de termijn.
    """
    if (self.wettelijke_termijn >= timedelta(days=3)):
      datum_start_wettelijke_termijn = self.datum_einde_wettelijke_termijn - self.wettelijke_termijn + timedelta(days=1)
      huidige_datum = datum_start_wettelijke_termijn
      werkdagen = 0

      while (huidige_datum <= self.datum_einde_wettelijke_termijn):
        if huidige_datum.weekday() < 5 and huidige_datum not in Artikel3(jaar=huidige_datum.year).algemeen_erkende_feestdagen:
          werkdagen += 1
        huidige_datum += timedelta(days=1)

      while werkdagen < 2:
        self.verlenging_termijn += timedelta(days=1)

        if self.datum_einde_verlengde_termijn.weekday() < 5  and self.datum_einde_verlengde_termijn not in Artikel3(jaar=self.datum_einde_verlengde_termijn.year).algemeen_erkende_feestdagen:
          werkdagen +=1
      
      return self.verlenging_termijn