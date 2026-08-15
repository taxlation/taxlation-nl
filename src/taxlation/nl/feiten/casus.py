from dataclasses import dataclass
from datetime import date
from typing import Sequence

from .belastingmiddel import Belastingmiddel
from .hoofdverblijf import Hoofdverblijf
from .onroerende_zaak import OnroerendeZaak
from .verkrijger import Verkrijger
from .verkrijging import Verkrijging


class OnvoldoendeFeiten(ValueError):
  """De feiten laten geen uitspraak toe over deze bepaling."""


@dataclass(kw_only=True)
class Casus:
  """De feiten van een casus, gegroepeerd per werkelijk ding waarover ze gaan.

  Alle velden zijn optioneel: geen enkel artikel leest ze allemaal. None betekent
  onbekend, niet onwaar.
  """

  datum_toepassing: date | None = None  # de datum waarnaar de casus wordt beoordeeld

  # entiteiten worden per wet toegevoegd; wbrv opent de rij
  verkrijger: Verkrijger | None = None
  zaak: OnroerendeZaak | None = None
  hoofdverblijf: Hoofdverblijf | None = None
  verkrijging: Verkrijging | None = None
  belastingmiddel: Belastingmiddel | None = None

  def _lees(self, pad: str):
    waarde = self
    for deel in pad.split("."):
      waarde = getattr(waarde, deel, None)
    return waarde

  def vereist(self, namen: Sequence[str | tuple[str, ...]], door: str) -> None:
    """Controleert of de feiten die een bepaling nodig heeft bepaald zijn.

    Een los pad moet bekend zijn. Een tuple is een disjunctie: bepaald zodra een
    onderdeel True is, of zodra alle onderdelen bekend zijn.

    Werpt OnvoldoendeFeiten met alle ontbrekende feiten tegelijk.
    """
    if isinstance(namen, str):
      raise TypeError("namen moet een sequence van paden zijn, geen losse string")

    ontbreekt = []
    for naam in namen:
      if isinstance(naam, tuple):
        waarden = [self._lees(pad) for pad in naam]
        if not any(w is True for w in waarden) and any(w is None for w in waarden):
          ontbreekt.append(" of ".join(naam))
      elif self._lees(naam) is None:
        ontbreekt.append(naam)

    if ontbreekt:
      raise OnvoldoendeFeiten(f"ontbrekende feiten voor {door}: {', '.join(ontbreekt)}")
