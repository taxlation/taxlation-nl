# make correct version of article available
from datetime import date
from taxlation.nl.versioning import VersieArtikel
from .v2025_01_01 import translation as v2025_01_01
from .v2026_01_01 import translation as v2026_01_01

Artikel15 = VersieArtikel(name="Artikel15", versions={
  date(2025,1,1): v2025_01_01.Artikel15,
  date(2026,1,1): v2026_01_01.Artikel15,
})

Artikel15Lid1 = VersieArtikel(name="Artikel15Lid1", versions={
  date(2025,1,1): v2025_01_01.Artikel15Lid1,
  date(2026,1,1): v2026_01_01.Artikel15Lid1,
})

Artikel15Lid1OnderdeelP = VersieArtikel(name="Artikel15Lid1", versions={
  date(2025,1,1): v2025_01_01.Artikel15Lid1,
  date(2026,1,1): v2026_01_01.Artikel15Lid1OnderdeelP,
})

__all__ = ["Artikel15", "Artikel15Lid1"]