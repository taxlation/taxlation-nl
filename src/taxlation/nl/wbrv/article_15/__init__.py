# make correct version of article available
from datetime import date
from taxlation.nl.versioning import VersieArtikel
from .v2026_01_01.translation import Artikel15 as v2026_01_01

Artikel15 = VersieArtikel(name="Artikel15", versions={
  date(2026,1,1): v2026_01_01,
})

__all__ = ["Artikel15"]