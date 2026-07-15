# make correct version of article available
from datetime import date
from taxlation.nl.versioning import VersieArtikel
from .v2025_01_01.translation import Artikel2 as v2025_01_01

Artikel2 = VersieArtikel(name="Artikel2", versions={
  date(2025,1,1): v2025_01_01,
})

__all__ = ["Artikel2"]