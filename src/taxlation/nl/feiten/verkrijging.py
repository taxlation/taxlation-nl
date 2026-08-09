from dataclasses import dataclass


@dataclass(kw_only=True)
class Verkrijging:
  """Feiten over de verkrijging zelf."""

  verkrijging: bool | None = None
