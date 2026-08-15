from dataclasses import dataclass

from taxlation.nl.feiten import Casus


@dataclass
class Artikel2:
  """Artikel 2 WBRV."""

  casus: Casus

  @dataclass
  class Lid1:
    """Artikel 2, lid 1 WBRV."""

    casus: Casus
    VEREIST = (
      "verkrijging.verkrijging",
      "zaak.in_nederland_gelegen",
      ("zaak.onroerende_zaken", "zaak.rechten_onroerende_zaken_onderworpen"),
    )

    @property
    def belastbaar_feit(self) -> bool:
      self.casus.vereist(self.VEREIST, "Artikel2.Lid1")
      zaak = self.casus.zaak
      return bool(
        self.casus.verkrijging.verkrijging
        and zaak.in_nederland_gelegen
        and (zaak.onroerende_zaken or zaak.rechten_onroerende_zaken_onderworpen)
      )

  @property
  def lid_1(self) -> bool:
    return Artikel2.Lid1(self.casus).belastbaar_feit

  @property
  def overdrachtsbelasting(self) -> bool:
    """Bepaalt of overdrachtsbelasting wordt geheven."""
    return self.lid_1
