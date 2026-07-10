# make correct version of article available
from datetime import date
from taxlation.nl.versioning import VersieArtikel
from .v2009_10_01.translation import Artikel7_10 as v1994_01_01

Artikel7_10 = VersieArtikel(name="Artikel7_10", versions={
  date(1994,1,1): v1994_01_01,
})

__all__ = ["Artikel7_10"]