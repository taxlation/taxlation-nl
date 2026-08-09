import functools
from dataclasses import dataclass, is_dataclass
from datetime import date
from typing import Sequence, get_args, get_origin, get_type_hints

from .belastingmiddel import Belastingmiddel
from .hoofdverblijf import Hoofdverblijf
from .onroerende_zaak import OnroerendeZaak
from .verkrijger import Verkrijger
from .verkrijging import Verkrijging


class OnvoldoendeFeiten(ValueError):
  """De feiten laten geen uitspraak toe over deze bepaling."""


def _zonder_none(tipe):
  """Pakt het echte type uit een `X | None`-annotatie; andere annotaties blijven
  ongewijzigd."""
  if get_origin(tipe) is not None and type(None) in get_args(tipe):
    opties = [arg for arg in get_args(tipe) if arg is not type(None)]
    if len(opties) == 1:
      return opties[0]
  return tipe


def _veldtype(klasse: type, naam: str, pad: str) -> type:
  """Zoekt het type van naam op klasse op via de type hints van het dataclassveld;
  werpt AttributeError als het veld niet bestaat."""
  hints = get_type_hints(klasse)
  if naam not in hints:
    raise AttributeError(f"onbekend pad {pad!r}: {klasse.__name__} heeft geen veld {naam!r}")
  return _zonder_none(hints[naam])


def _controleer_pad(pad: str) -> None:
  """Loopt pad af over het veldenschema van Casus; werpt AttributeError zodra het
  pad niet kan bestaan, bijvoorbeeld door een typefout of doordat het voorbij een
  blad (geen entiteit) doorloopt."""
  eerste, *rest = pad.split(".")
  tipe = _veldtype(Casus, eerste, pad)
  for deel in rest:
    if not is_dataclass(tipe):
      raise AttributeError(f"onbekend pad {pad!r}: {tipe} is geen entiteit")
    tipe = _veldtype(tipe, deel, pad)


@functools.lru_cache
def _controleer_namen(namen: tuple) -> None:
  """Valideert elk pad in namen tegen het veldenschema van Casus.

  VEREIST-tuples zijn klasse-constanten die per artikel bevroren zijn, dus levert
  cachen op de tuple zelf herhaalde evaluatie (elke keer dat de bepaling wordt
  getoetst) gratis op.
  """
  for naam in namen:
    for pad in (naam if isinstance(naam, tuple) else (naam,)):
      _controleer_pad(pad)


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

    _controleer_namen(tuple(namen))

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
