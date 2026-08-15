from dataclasses import dataclass


@dataclass(kw_only=True)
class OnroerendeZaak:
  """Feiten over de onroerende zaak die wordt verkregen."""

  woning: bool | None = None
  rechten_woning_onderworpen: bool | None = None  # rechten waaraan een woning is onderworpen
  rechten_lidmaatschap_woning: bool | None = None  # lidmaatschapsrechten m.b.t. een woning
  aanhorigheid: bool | None = None  # gelijktijdig verkregen aanhorigheid
  in_nederland_gelegen: bool | None = None
  onroerende_zaken: bool | None = None
  rechten_onroerende_zaken_onderworpen: bool | None = None
  waarde_woning: int | None = None
  # geen aanhorigheid betekent nul; die waarde geeft de wet zelf. Is er wel een
  # aanhorigheid, of is dat onbekend, dan is nul geen wettelijk gegeven maar een gok:
  # de waarde blijft onbekend totdat hij is ingevuld. Onbekend is niet hetzelfde als
  # geen.
  waarde_aanhorigheden: int | None = None

  def __post_init__(self):
    if self.waarde_aanhorigheden is None and self.aanhorigheid is False:
      self.waarde_aanhorigheden = 0
