from datetime import date

from taxlation.nl.versioning import VersieArtikel

from .v2025_01_01.translation import Artikel15 as v2025_01_01
from .v2026_01_01.translation import Artikel15 as v2026_01_01

# Geneste niveaus worden hieruit afgeleid: wbrv.Artikel15.Lid1.OnderdeelP kiest
# dezelfde versie als wbrv.Artikel15.
Artikel15 = VersieArtikel(name="Artikel15", versions={
  date(2025, 1, 1): v2025_01_01,
  date(2026, 1, 1): v2026_01_01,
})

__all__ = ["Artikel15"]
