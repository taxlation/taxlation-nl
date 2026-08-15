from dataclasses import dataclass


@dataclass(kw_only=True)
class Belastingmiddel:
  """Welk belastingmiddel aan de orde is."""

  overdrachtsbelasting: bool | None = None  # hoofdstuk II WBRV
  assurantiebelasting: bool | None = None  # hoofdstuk III WBRV
