# make correct version of article available
from datetime import date
from taxlation.nl.core_translation import VersieArtikel
from .v2021_07_01.translation import Artikel6_8 as v2021_07_01

Artikel6_8 = VersieArtikel(name="Artikel6_8", versions={
  date(2021,7,1): v2021_07_01,
})

__all__ = ["Artikel6_8"]