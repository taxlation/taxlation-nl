from taxlation.core.versioning import VersionedClass

class VersieArtikel(VersionedClass):
  def __call__(self, *, datum_toepassing = None, **kwargs):
    return super().__call__(reference_date=datum_toepassing, **kwargs)