from dataclasses import dataclass

from taxlation.nl.feiten import Casus


@dataclass
class Artikel1:
  """Artikel 1 WBRV."""

  casus: Casus
  VEREIST = (
    ("belastingmiddel.overdrachtsbelasting", "belastingmiddel.assurantiebelasting"),
  )

  @property
  def belasting_van_rechtsverkeer(self) -> bool:
    """Sprake van een belasting van rechtsverkeer bij overdrachts- of assurantiebelasting."""
    self.casus.vereist(self.VEREIST, "Artikel1")
    belastingmiddel = self.casus.belastingmiddel
    return bool(belastingmiddel.overdrachtsbelasting or belastingmiddel.assurantiebelasting)
