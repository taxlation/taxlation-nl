from dataclasses import dataclass


@dataclass(kw_only=True)
class Verkrijger:
  """Feiten over de persoon die verkrijgt."""

  natuurlijk_persoon: bool | None = None
  leeftijd: int | None = None
  vrijstelling_eerder_toegepast: bool | None = None
  verklaring_vrijstelling: bool | None = None  # verklaard de vrijstelling niet eerder te hebben toegepast
