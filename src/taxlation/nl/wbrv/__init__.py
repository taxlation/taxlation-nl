# make dataclasses directly available for atw
from .article_1 import Artikel1
from .article_2 import Artikel2
from .article_15 import Artikel15, Artikel15Lid1, Artikel15Lid1OnderdeelP

__all__ = ["Artikel1", "Artikel2", "Artikel15", "Artikel15Lid1", "Artikel15Lid1OnderdeelP"]