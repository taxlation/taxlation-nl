# make correct version of article available
from datetime import date
from taxlation.nl.versioning import VersieArtikel
from .v1982_03_31.translation import Artikel3 as v1982_03_31

Artikel3 = VersieArtikel(name="Artikel3", versions={
  date(1982,3,31): v1982_03_31,
})

__all__ = ["Artikel3"]