from dataclasses import dataclass

from taxlation.nl.feiten import Casus

WAARDEGRENS = 525_000
LEEFTIJD_MINIMUM = 18
LEEFTIJD_MAXIMUM = 35  # exclusief: de verkrijger moet jonger dan 35 zijn


@dataclass
class Artikel15:
  """Artikel 15 WBRV."""

  casus: Casus

  @dataclass
  class Lid1:
    """Artikel 15, lid 1 WBRV."""

    casus: Casus

    @dataclass
    class OnderdeelP:
      """Artikel 15, lid 1, onderdeel p WBRV: de startersvrijstelling."""

      casus: Casus
      VEREIST = (
        ("zaak.woning", "zaak.rechten_woning_onderworpen", "zaak.rechten_lidmaatschap_woning"),
        "verkrijger.natuurlijk_persoon",
        "verkrijger.leeftijd",
        "verkrijger.vrijstelling_eerder_toegepast",
        "verkrijger.verklaring_vrijstelling",
        "hoofdverblijf.woning_tijdelijk_hoofdverblijf",
        "hoofdverblijf.verklaring_hoofdverblijf",
        "zaak.waarde_woning",
      )

      @property
      def startersvrijstelling(self) -> bool:
        self.casus.vereist(self._vereist(), "Artikel15.Lid1.OnderdeelP")
        return (
          self._verkrijging_woning
          and self._verkrijger_kwalificeert
          and self._eenmalig_beroep
          and self._hoofdverblijfeis
          and self._binnen_waardegrens
        )

      def _vereist(self):
        """De waarde van een aanhorigheid telt mee in de waardegrens, dus zodra een
        aanhorigheid niet uitgesloten is - bevestigd, of onbekend - moet die waarde
        bekend zijn. De standaardwaarde nul geldt alleen wanneer er geen aanhorigheid
        is verkregen."""
        if self.casus.zaak is not None and self.casus.zaak.aanhorigheid is not False:
          return self.VEREIST + ("zaak.waarde_aanhorigheden",)
        return self.VEREIST

      @property
      def _verkrijging_woning(self) -> bool:
        # Een aanhorigheid deelt in de vrijstelling maar kan die niet zelfstandig doen
        # ontstaan; die telt alleen mee in de waarde.
        zaak = self.casus.zaak
        return bool(
          zaak.woning or zaak.rechten_woning_onderworpen or zaak.rechten_lidmaatschap_woning
        )

      @property
      def _verkrijger_kwalificeert(self) -> bool:
        verkrijger = self.casus.verkrijger
        return bool(
          verkrijger.natuurlijk_persoon
          and LEEFTIJD_MINIMUM <= verkrijger.leeftijd < LEEFTIJD_MAXIMUM
        )

      @property
      def _eenmalig_beroep(self) -> bool:
        verkrijger = self.casus.verkrijger
        return bool(
          not verkrijger.vrijstelling_eerder_toegepast and verkrijger.verklaring_vrijstelling
        )

      @property
      def _hoofdverblijfeis(self) -> bool:
        hoofdverblijf = self.casus.hoofdverblijf
        return bool(
          not hoofdverblijf.woning_tijdelijk_hoofdverblijf
          and hoofdverblijf.verklaring_hoofdverblijf
        )

      @property
      def _binnen_waardegrens(self) -> bool:
        zaak = self.casus.zaak
        return (zaak.waarde_woning + zaak.waarde_aanhorigheden) <= WAARDEGRENS

    @property
    def onderdeel_p(self) -> bool:
      return Artikel15.Lid1.OnderdeelP(self.casus).startersvrijstelling

  @property
  def lid_1(self) -> bool:
    """Bepaalt of de verkrijging is vrijgesteld."""
    return Artikel15.Lid1(self.casus).onderdeel_p
