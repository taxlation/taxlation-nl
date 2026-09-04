# make correct version of article available
from datetime import date
from taxlation.nl.core_translation import VersieArtikel
from .v2006_01_01.translation import Artikel1 as v2006_01_01

Artikel1 = VersieArtikel(name="Artikel1", versions={
  date(2006,1,1): v2006_01_01,
})

__all__ = ["Artikel1"]