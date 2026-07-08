from datetime import date

class VersionedClass:
  """Selects the right version of an article class"""

  def __init__(self, name: str, versions: dict[date, type]):
      self._name = name
      self._versions = dict(sorted(versions.items()))

  def __call__(self,*, reference_date: date | None = None, **kwargs):
    reference_date = reference_date or date.today()

    apply_dataclass  = None

    for effective_date, dataclass in self._versions.items():
      if effective_date <= reference_date:
        apply_dataclass = dataclass
      else:
        break

    if apply_dataclass is None:
      raise ValueError(f"No version from {self._name} on {reference_date}")
    
    if not callable(apply_dataclass):
      return apply_dataclass
    
    return apply_dataclass(**kwargs)


