# make correct version of article available
from datetime import date
from taxlation.nl.versioning import VersieArtikel
from .v2025_01_01 import translation as v2025_01_01
from .v2026_01_01 import translation as v2026_01_01

Artikel15 = VersieArtikel(name="Artikel15", versions={
  date(2025,1,1): v2025_01_01.Artikel15,
  date(2026,1,1): v2026_01_01.Artikel15,
})

__all__ = ["Artikel15",]