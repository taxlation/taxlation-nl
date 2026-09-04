# make correct version of article available
from datetime import date
from taxlation.nl.core_translation import VersieArtikel
from .v1994_01_01.translation import Artikel6_7 as v1994_01_01

Artikel6_7 = VersieArtikel(name="Artikel6_7", versions={
  date(1994,1,1): v1994_01_01,
})

__all__ = ["Artikel6_7"]