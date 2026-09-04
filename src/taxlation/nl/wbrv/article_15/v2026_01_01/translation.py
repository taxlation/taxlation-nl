from dataclasses import dataclass
from taxlation.core.result import Result

@dataclass
class Artikel15:
  """
  Class voor artikel 15 WBRV
  """

  @dataclass
  class Lid1:
    """
    Class voor artikel 15, lid 1 WBRV
    """

    @dataclass
    class OnderdeelP:  
      """
      Dataclass voor artikel 15, lid 1, onderdeel p, WBRV
      """
      woning: bool # True indien sprake is van een verkrijging van een woning of van rechten van waaraan deze is onderworpen of van rechten van lidmaatschap als bedoeld in artikel 4, eerste lid , onderdeel b, voor zover deze laatste rechten betrekking hebben op een woning
      verkrijger_natuurlijk_persoon: bool # True indien sprake is van verkrijger die natuurlijk persoon is/
      verkrijger_leeftijd: int # Leeftijd van de verkrijger.
      verkrijger_vrijstelling_niet_eerder_toegepast: bool # True indien vrijstelling niet eerder is toegepast.
      verkrijger_niet_eerder_toegepast_verklaring: bool # True indien verklaring van verkrijger niet eerder startersvrijstelling heeft toegepast.
      verkrijger_woning_hoofdverblijf: bool # True indien de verkrijger de woning anders dan tijdelijk als hoofdverblijf gaat gebruiken.
      verkrijger_hoofdverblijf_verklaring: bool # True indien verklaring van verkrijger de woning anders dan tijdelijk als hoofdverblijf gaat gebruiken.
      woning_waarde: int # Waarde woning.
      aanhorigheden_waarde: int = 0 # Waarde gelijktijdige verkrijging aanhorigheden.

      @property
      def verkrijging_woning(self) -> Result:
        if (self.woning == True):
          return Result("Artikel 15, lid 1, onderdeel p, WBRV", True, "Woning verkregen.")
        else:
          return Result("Artikel 15, lid 1, onderdeel p, WBRV", False, "Geen woning verkregen.")

      @property
      def subonderdeel_1(self) -> Result:
        if (self.verkrijger_natuurlijk_persoon == True and self.verkrijger_leeftijd >= 18 and self.verkrijger_leeftijd < 35):
          return Result("Artikel 15, lid 1, onderdeel p, subonderdeel 1, WBRV", True, "Verkrijger meerderjarig natuurlijk persoon jonger dan vijfendertig jaar.")
        else:
          return Result("Artikel 15, lid 1, onderdeel p, subonderdeel 1, WBRV", False, "Verkrijger geen meerderjarig natuurlijk persoon jonger dan vijfendertig jaar.")

      @property
      def subonderdeel_2(self) -> Result:
        if (self.verkrijger_vrijstelling_niet_eerder_toegepast == True and self.verkrijger_niet_eerder_toegepast_verklaring == True):
          return Result("Artikel 15, lid 1, onderdeel p, subonderdeel 2, WBRV", True, "Verkrijger heeft vrijstelling niet eerder toegepast en heeft dit verklaard.")
        else:
          return Result("Artikel 15, lid 1, onderdeel p, subonderdeel 2, WBRV", False, "Verkrijger heeft vrijstelling eerder toegepast of heeft dit niet verklaard.")
        
      @property
      def subonderdeel_3(self) -> Result:
        if (self.verkrijger_woning_hoofdverblijf == True and self.verkrijger_hoofdverblijf_verklaring == True):
          return Result("Artikel 15, lid 1, onderdeel p, subonderdeel 3, WBRV", True, "Verkrijger gaat woning anders dan tijdelijk als hoofdverblijf gebruiken en heeft dit verklaard.")
        else:
          return Result("Artikel 15, lid 1, onderdeel p, subonderdeel 3, WBRV", False, "Verkrijger gaat woning niet anders dan tijdelijk als hoofdverblijf gebruiken of heeft dit niet verklaard.")

      @property
      def subonderdeel_4(self) -> Result:
        if (self.woning_waarde + self.aanhorigheden_waarde) <= 555000:
          return Result("Artikel 15, lid 1, onderdeel p, subonderdeel 4, WBRV", True, "Het totaal van de waarde van de woning en tot die woning behorende aanhorigheden komt niet uit boven de woningwaardegrens")
        else:
          return Result("Artikel 15, lid 1, onderdeel p, subonderdeel 4, WBRV", False, "Het totaal van de waarde van de woning en tot die woning behorende aanhorigheden komt uit boven de woningwaardegrens")

      @property
      def startersvrijstelling(self) -> Result:
        if (self.verkrijging_woning and self.subonderdeel_1 and self.subonderdeel_2 and self.subonderdeel_3 and self.subonderdeel_4):
          return Result("Artikel 15, lid 1, onderdeel p, WBRV", True, "Startersvrijstelling van toepassing", (self.verkrijging_woning, self.subonderdeel_1, self.subonderdeel_2, self.subonderdeel_3, self.subonderdeel_4))
        else:
          return Result("Artikel 15, lid 1, onderdeel p, WBRV", False, "Startersvrijstelling niet van toepassing", (self.verkrijging_woning, self.subonderdeel_1, self.subonderdeel_2, self.subonderdeel_3, self.subonderdeel_4))

    onderdeel_p: OnderdeelP

    @property
    def vrijstelling(self) -> Result:
      if (self.onderdeel_p.startersvrijstelling):
        return Result("Artikel 15, lid 1, WBRV", True, "Vrijstelling van toepassing", (self.onderdeel_p.startersvrijstelling,))
      else:
        return Result("Artikel 15, lid 1, WBRV", False, "Geen vrijstelling van toepassing", (self.onderdeel_p.startersvrijstelling,))