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
  waarde_aanhorigheden: int = 0  # geen aanhorigheden betekent nul; die waarde geeft de wet zelf
