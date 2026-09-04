# make correct version of article available
from datetime import date
from taxlation.nl.core_translation import VersieArtikel
from .v1965_04_01.translation import Artikel4 as v1965_04_01

Artikel4 = VersieArtikel(name="Artikel4", versions={
  date(1965,4,1): v1965_04_01,
})

__all__ = ["Artikel4"]