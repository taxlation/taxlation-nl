# make correct version of article available
from datetime import date
from taxlation.nl.core_translation import VersieArtikel
from .v1999_02_17 import Artikel1 as v1999_02_17


Artikel1 = VersieArtikel(name="Artikel1", versions={
  date(1999,2,17): v1999_02_17,
})

__all__ = ["Artikel1"]