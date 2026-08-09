from dataclasses import replace

from taxlation.core.versioning import VersionedClass


class VersieArtikel(VersionedClass):
  """Selecteert de juiste versie van een artikelklasse."""

  def __call__(self, *, datum_toepassing=None, casus=None, **kwargs):
    """Kiest de versie op de peildatum en bouwt de klasse.

    De casus draagt de peildatum. Een artikel dat een ander artikel bevraagt geeft
    dezelfde casus door en krijgt dus dezelfde versie, ook wanneer die aanroep pas
    plaatsvindt nadat deze methode is teruggekeerd.
    """
    if casus is None:
      return super().__call__(reference_date=datum_toepassing, **kwargs)

    if (
      datum_toepassing is not None
      and casus.datum_toepassing is not None
      and datum_toepassing != casus.datum_toepassing
    ):
      raise ValueError(
        f"datum_toepassing ({datum_toepassing}) en casus.datum_toepassing "
        f"({casus.datum_toepassing}) spreken elkaar tegen"
      )

    peildatum = datum_toepassing or casus.datum_toepassing
    if casus.datum_toepassing is None and peildatum is not None:
      casus = replace(casus, datum_toepassing=peildatum)

    return super().__call__(reference_date=peildatum, casus=casus, **kwargs)

  def __getattr__(self, naam):
    """Leidt de versiemap van een genest niveau af uit die van het artikel.

    Welke geneste klasse geldt hangt af van de peildatum, en die is pas bekend bij
    aanroep; daarom levert dit opnieuw een VersieArtikel op. Versies die het niveau
    niet kennen worden overgeslagen, zodat een later ingevoerd lid vanzelf een map
    krijgt die op dat moment begint.
    """
    if naam.startswith("_"):
      raise AttributeError(naam)

    versies = {
      datum: getattr(klasse, naam)
      for datum, klasse in self._versions.items()
      if hasattr(klasse, naam)
    }
    if not versies:
      raise AttributeError(naam)

    return VersieArtikel(name=f"{self._name}.{naam}", versions=versies)
