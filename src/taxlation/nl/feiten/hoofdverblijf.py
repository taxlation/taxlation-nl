from dataclasses import dataclass


@dataclass(kw_only=True)
class Hoofdverblijf:
  """Feiten over het gebruik van de woning als hoofdverblijf."""

  woning_tijdelijk_hoofdverblijf: bool | None = None
  # verklaard de woning anders dan tijdelijk als hoofdverblijf te gaan gebruiken
  verklaring_hoofdverblijf: bool | None = None
