#import dataclasses module
from dataclasses import dataclass

#import datetime module
from datetime import date, timedelta

#import relativedelta module
from dateutil.relativedelta import relativedelta

@dataclass
class Art_4: 
  """
  Dataclass voor Art. 4 Algemene termijnenwet
  """
  datum_einde_wettelijke_termijn: date # einddatum van een in de wet gestelde termijn
  wettelijke_termijn: timedelta # in een wet gestelde termijn
  wettelijke_termijn_eenheid: str # eenheid van de in een wet gestelde termijn (uur, dag, week, maand, jaar)
  verlenging_termijn: timedelta = timedelta(days=0) # verlenging van een in de wet gestelde termijn

  def __post_init__(self):
    self.onderdeel_a()
    self.wet_geldt_niet
    
  @property   
  def wet_geldt_niet(self) -> bool:
    """
      Laat verlengde termijnen niet van toepassing zijn indien onderdeel a van toepassing is.

      Geeft terug:
        bool: False als wet geldt voor de termijn.
      """
    if (self.onderdeel_a() == True):
      self.verlenging_termijn = timedelta(days=0)
      return True
    else:
      return False

  @property
  def datum_einde_verlengde_termijn(self):
    """
    Berekent de einddatum van de verlengde termijn.

    Functie telt de eventuele verlenging op bij de einddatum van de wettelijke termijn.

    Geeft terug:
      datetime.date: De einddatum met inachtneming van de wettelijke termijn en verlenging.
    """
    return self.datum_einde_wettelijke_termijn + self.verlenging_termijn

  def onderdeel_a(self) -> bool:
      """
      Onderdeel is van toepassing indien de wettelijke termijn specifiek is geformuleerd.
      
      Geeft terug:
        bool: True als onderdeel van toepassing is.
      """
      datum_start_wettelijke_termijn = self.datum_einde_wettelijke_termijn - self.wettelijke_termijn
      if ((self.wettelijke_termijn_eenheid == 'uur') or
        (self.wettelijke_termijn > timedelta(days=90) and self.wettelijke_termijn_eenheid == 'dag') or
        (self.wettelijke_termijn > timedelta(weeks=12) and self.wettelijke_termijn_eenheid == 'week') or
        (self.wettelijke_termijn > (datum_start_wettelijke_termijn + relativedelta(months=3) - datum_start_wettelijke_termijn) and self.wettelijke_termijn_eenheid == 'maand') or
        (self.wettelijke_termijn >= (datum_start_wettelijke_termijn + relativedelta(year=1) - datum_start_wettelijke_termijn) and self.wettelijke_termijn_eenheid == 'jaar')
      ):
        return True
      else:
        return False