#import dataclasses module
from dataclasses import dataclass

class Artikel4:
  """
  Class voor artikel 4 WBRV
  """

  class Lid1:
    """
    Class voor artikel 4, lid 1 WBRV
    """

    @dataclass (kw_only= True)
    class onderdeelA:  
      """
      Dataclass voor voor artikel 4, lid 1 WBRV
      """
      aandelen_rechtspersoon: bool # WAAR bij de aanwezigheid van aandelen in een rechtspersoon en ONWAAR indien anders
      waarde_onroerende_zaken: int # waarde in het economische verkeer van de onroerende zaken
      waarde_onroerende_zaken_nl: int # waarde in het economische verkeer van in Nederland gelegen onroerende zaken
      waarde_onroerende_zaken_vve: int # waarde in het economische verkeer van onroerende zaken dienstbaar aan verkrijgen, vervreemden of exploiteren
      waarde_roerende_activa: int # waarde in het economische verkeer van alle activa
      fictieve_onroerende_zaak: bool = None

    def __post_init__(self):
      self.fictieve_onroerende_zaken()

    def bezitseis(self):
      if (self.waarde_onroerende_zaken / (self.waarde_onroerende_zaken + self.waarde_roerende_activa)) > 0.5 and (self.waarde_onroerende_zaken_nl / self.waarde_onroerende_zaken) >= 0.3:
        return True
      else:
        return False

    def doeleis(self):
      if (self.waarde_onroerende_zaken_vve / self.waarde_onroerende_zaken) >= 0.7:
        return True
      else:
        return False

    def fictieve_onroerende_zaken(self):
      if self.aandelen_rechtspersoon and self.bezitseis() and self.doeleis():
        self.fictieve_onroerende_zaak = True
        return True
      else:
        self.fictieve_onroerende_zaak = False
        return False

  @property
  def fictieve_onroerende_zaken(self) -> bool:
    return 