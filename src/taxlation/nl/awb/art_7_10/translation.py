#import dataclasses module
from dataclasses import dataclass

#import datetime module
from datetime import date, timedelta

@dataclass
class Art_7_10:
  """
  Dataclass voor Art. 7:10 Algemene wet bestuursrecht
  """
  datum_einde_bezwaartermijn: date # datum waarop de bezwaartermijn is verstreken 
  commissie_ingesteld: bool # commissie ingesteld als bedoeld in artikel 7:13
  termijn_beslissing_bezwaar: timedelta = timedelta(days=0) # termijn van beslissing op bezwaar
  
  datum_verzoek_verzuim: date = None # de dag waarop de indiener is verzocht een verzuim als bedoeld in artikel 6:6 te herstellen
  termijn_verzoek_verzuim: timedelta = timedelta(days=0) # de voor het herstel van het verzuim gestelde termijn
  datum_herstel_verzuim: date = None # de dag waarop het verzuim is hersteld

  termijn_verdagen: timedelta = timedelta(days=0) # de termijn voor het verdagen

  termijn_verder_uitstel: timedelta = timedelta(days=0) # de termijn voor verder uitstel

  instemming_alle_belanghebbenden: bool = None # alle belanghebbende stemmen in met verder uitstel
  instemming_indiener: bool = None # de indiener van het bezwaarschrift stemt in met verder uitstel
  andere_belanghebbende_niet_geschaad: bool = None # andere belanghebbende worden door verder uitstel niet in hun belangen geschaad
  naleving_wettelijke_procedurevoorschriften: bool = None # verder uitstel is nodig in verband met de nalevign van wettelijke procedurevoorschriften

  def __post_init__(self):
    self.lid_1()
    self.lid_2()
    self.lid_3()
    self.lid_4()

  @property 
  def datum_einde_beslistermijn(self):
    """
    Berekent de einddatum van de beslistermijn van een bezwaar.

    Functie telt de de beslistermijn op bij de startdatum, gerekend vanaf de dag na die waarop de termijn voor het indienden van het bezwaarschrift is verstreken.

    Geeft terug:
      date: De einddatum van de beslistermijn op een bezwaar.
    """
    return self.datum_einde_bezwaartermijn + self.termijn_beslissing_bezwaar + self.termijn_opschorten + self.termijn_verdagen + self.termijn_verder_uitstel
  
  def lid_1(self):
    """
    Bepaalt aan de hand van of een adviescommissie is ingesteld of de beslistermijn van zes werken of twaalf weken van toepassing is.
    
    Geeft terug:
      timedelta: De termijn van een beslissing op een bezwaar.
    """
    if (self.commissie_ingesteld):
      self.termijn_beslissing_bezwaar = timedelta(weeks=12)
    else:
      self.termijn_beslissing_bezwaar = timedelta(weeks=6)

    return self.termijn_beslissing_bezwaar
  
  def lid_2(self):
    """
    Schort de beslistermijn op in geval de indiener van het bezwaarschrift wordt verzocht een verzuim als bedoeld in artikel 6:6 te herstellen en hiervoor een termijn wordt meegegeven.

    Opschorting kan niet eerder plaatsvinden dan de einddatum van de bezwaartermijn (ECLI:NL:CRVB:2016:4204). 
    
    De termijn wordt opgeschort tot de eerstvolgende dag waarop het verzuim is hersteld of de daarvoor gestelde termijn ongebruikt is verstreken.

    Geeft terug:
      timedelta: De termijn van het opschorten van de beslistermijn.
    """
    self.termijn_opschorten = timedelta(days=0)

    if (self.datum_verzoek_verzuim and self.termijn_verzoek_verzuim > timedelta(days=0)):
      
      self.datum_einde_verzoek_verzuim = self.datum_verzoek_verzuim + self.termijn_verzoek_verzuim
      self.datum_start_opschorten = max(self.datum_verzoek_verzuim, self.datum_einde_bezwaartermijn)

      if (self.datum_herstel_verzuim == None):
        self.termijn_opschorten = self.datum_einde_verzoek_verzuim - self.datum_start_opschorten
      else:
        self.termijn_opschorten = min(self.datum_herstel_verzuim, self.datum_einde_verzoek_verzuim) - self.datum_start_opschorten

    return self.termijn_opschorten
  
  def lid_3(self):
    """
    Verdaagt de beslistermijn met ten hoogste zes weken.
    
    Geeft terug:
      timedelta: De termijn van het verdagen van de beslistermijn.
    """
    self.termijn_verdagen = min(self.termijn_verdagen, timedelta(weeks=6))
    return self.termijn_verdagen
  
  def lid_4(self):
    """
    Stelt de beslistermijn uit zodra aan de voorwaarden van onderdeel a, b of c wordt voldaan.
    
    Geeft terug:
      timedelta: Het verdere uitstel van de beslistermijn.
    """
    onderdeel_a = self.instemming_alle_belanghebbenden
    onderdeel_b = self.instemming_indiener and self.andere_belanghebbende_niet_geschaad
    onderdeel_c = self.naleving_wettelijke_procedurevoorschriften

    if (onderdeel_a or onderdeel_b or onderdeel_c):
      self.termijn_verder_uitstel = self.termijn_verder_uitstel
    elif (onderdeel_a is False and onderdeel_b is False and onderdeel_c is False):
      self.termijn_verder_uitstel = timedelta(days=0)
    return self.termijn_verder_uitstel