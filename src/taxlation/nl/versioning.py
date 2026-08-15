from taxlation.core.versioning import VersionedClass


def _ingetrokken(naam, datum):
  """Vervangt een genest niveau dat op datum niet (meer) bestaat door een aanroep
  die dat expliciet meldt, zodat een ingetrokken lid nooit stilzwijgend terugvalt
  op een oudere of nieuwere versie.
  """

  def werp(**_):
    raise ValueError(f"{naam} bestaat niet in de versie van {datum}")

  return werp


class VersieArtikel(VersionedClass):
  """Selecteert de juiste versie van een artikelklasse."""

  def __call__(self, *, datum_toepassing=None, casus=None, **kwargs):
    """Kiest de versie op de peildatum en bouwt de klasse.

    Met een casus komt de peildatum uitsluitend uit casus.datum_toepassing. Een
    artikel dat een ander artikel bevraagt geeft dezelfde casus door en krijgt dus
    dezelfde versie, ook wanneer die aanroep pas plaatsvindt nadat deze methode is
    teruggekeerd. Twee bronnen voor één datum zouden precies dat kunnen breken.

    De losse datum_toepassing hoort bij de oude aanroepstijl met platte kwargs en
    verdwijnt zodra elk artikel een casus neemt.
    """
    if casus is None:
      return super().__call__(reference_date=datum_toepassing, **kwargs)

    if datum_toepassing is not None:
      raise TypeError(
        "geef de peildatum mee via casus.datum_toepassing, niet als losse "
        "datum_toepassing; twee bronnen kunnen uiteenlopen"
      )

    if casus.datum_toepassing is None:
      # Een casus zonder peildatum mag nooit stilzwijgend op de wandklok
      # terugvallen (dat is precies waarom de peildatum op de casus staat in
      # plaats van impliciet): een juridisch antwoord zonder vaste peildatum is
      # geen antwoord.
      raise ValueError(
        "casus.datum_toepassing is niet gezet; de peildatum moet op de casus "
        "staan voordat een artikel kan worden toegepast"
      )

    return super().__call__(
      reference_date=casus.datum_toepassing, casus=casus, **kwargs
    )

  def __getattr__(self, naam):
    """Leidt de versiemap van een genest niveau af uit die van het artikel.

    Welke geneste klasse geldt hangt af van de peildatum, en die is pas bekend bij
    aanroep; daarom levert dit opnieuw een VersieArtikel op. Alleen een echte
    geneste klasse wordt zo doorgeproxied: een los attribuut (zoals een VEREIST-
    tuple) bestaat pas op de gebouwde instantie, niet op deze proxy.

    De map wordt over alle versies van het artikel opgebouwd, niet alleen die
    waarin het niveau een klasse is: een versie die het niveau niet (meer) kent
    krijgt een aanroep die dat werpt. Zo blijft zowel een later ingevoerd als een
    later ingetrokken lid onbereikbaar buiten zijn eigen geldigheidsbereik, in
    plaats van dat de wet van een andere versie stilzwijgend doorwerkt.
    """
    if naam.startswith("_"):
      raise AttributeError(naam)

    aanwezig = {
      datum: getattr(klasse, naam)
      for datum, klasse in self._versions.items()
      if isinstance(getattr(klasse, naam, None), type)
    }
    if not aanwezig:
      raise AttributeError(naam)

    genest_naam = f"{self._name}.{naam}"
    versies = {
      datum: aanwezig.get(datum, _ingetrokken(genest_naam, datum))
      for datum in self._versions
    }

    resultaat = VersieArtikel(name=genest_naam, versions=versies)
    setattr(self, naam, resultaat)  # memoiseren: zelfde attribuut, zelfde object
    return resultaat

  def __repr__(self):
    return f"VersieArtikel({self._name})"
