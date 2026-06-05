from dataclasses import dataclass
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

@dataclass
class Art_4: 
  """
  Dataclass voor Art. 4 Algemene termijnenwet
  """
  startDatum: date # startdatum
  wettelijkeTermijn: timedelta # in een wet gestelde termijn
  wettelijkeTermijnEenheid: str # Eenheid van de in een wet gestelde termijn (uur, dag, week, maand, jaar)
  verlengingTermijn: timedelta = timedelta(days=0) # verlenging van termijn

  def __post_init__(self):
    self.onderdeel_a()
    self._applies = self.onderdeel_a()

  @property
  def einddatum(self):
    """
    Berekent de einddatum van de gestelde termijn.

    Functie telt het wettelijke termijn en de eventuele verlenging op bij de startdatum.

    Geeft terug:
      datetime.date: De einddatum met inachtneming van de wettelijke termijn en verlenging.
    """
    return self.startDatum + self.wettelijkeTermijn + self.verlengingTermijn

  @property
  def applies(self) -> bool:
      return self._applies
  
  def onderdeel_a(self) -> bool:
      """
      Laat verlengde termijnen niet van toepassing zijn indien de wettelijke termijn specifiek is geformuleerd.
      
      Returns:
        bool: True if Art. 4 applies (no extensions allowed)
      """
      if ((self.wettelijkeTermijnEenheid == 'uur') or
        (self.wettelijkeTermijn > timedelta(days=90) and self.wettelijkeTermijnEenheid == 'dag') or
        (self.wettelijkeTermijn > timedelta(weeks=12) and self.wettelijkeTermijnEenheid == 'week') or
        (self.wettelijkeTermijn > (self.startDatum + relativedelta(months=1) - self.startDatum) and self.wettelijkeTermijnEenheid == 'maand') or
        (self.wettelijkeTermijn >= (self.startDatum + relativedelta(year=12) - self.startDatum) and self.wettelijkeTermijnEenheid == 'jaar')
      ):
        self.verlengingTermijn = timedelta(days=0)
        return True
      return False