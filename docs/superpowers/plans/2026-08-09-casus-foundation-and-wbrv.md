# Casus Foundation + WBRV Conversion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the three `wbrv` articles to nested class namespaces over a `Casus` fact layer, changing no legal outcome except four recorded divergences.

**Architecture:** Facts move out of article classes into small entity dataclasses collected in a `Casus`. Articles become nested class namespaces (`Artikel15.Lid1.OnderdeelP`) where every level holds only `casus` and delegates downward by passing it. `VersieArtikel` takes its peildatum from the casus and derives nested version maps from the article's single map.

**Tech Stack:** Python 3.12, `dataclasses`, `uv`. No new runtime dependencies, and none added to `pyproject.toml`.

**Spec:** `docs/superpowers/specs/2026-08-09-casus-article-structure-design.md`

**Scope:** The `wbrv` articles. `awb` and `atw` are Plan 2; the `taxlation-api` migration is Plan 3. `wbrv` goes first because it has no consumers.

---

## The verification harness lives outside the repo

**The branch must contain law-as-code and nothing else.** The harness that proves the refactor safe is a development tool, not a deliverable, so it lives at:

```
/Users/ralphmoonlit/Documents/Repositories/Taxlation/taxlation-nl-verificatie/
```

a sibling directory, never committed, never `git add`ed. Nothing in `pyproject.toml` changes either — `uv run --with pytest` injects pytest for a single command.

Run it from the repo root:

```bash
uv run --with pytest pytest ../taxlation-nl-verificatie -q
```

### How the oracle works

Hand-writing expected values tests a belief about the law rather than the code's behaviour. Regenerating them after refactoring lets the refactor certify itself. So:

1. **Cases are generated once** from the current implementation, holding inputs *and* expected outputs.
2. **They are frozen.** After Task 2 nothing in `cases/` is ever regenerated.
3. **One `bouw()` helper per law** turns facts into an article. Conversion rewrites that helper and nothing else, so the diff shows assertions untouched.
4. **Authorised changes go in `AFWIJKINGEN`**, naming old value, new value and reason. A mismatch without an entry fails.

There is deliberately no adapter layer, no registry and no separate golden files. An earlier draft had all three so one test could drive both implementations, but both would import the same working tree — the moment an article converts, its pre-change form no longer exists. That capability was never real, so the machinery for it is gone.

### Code style

`src/` uses 2-space indentation, matching every existing file. The harness uses 4-space PEP 8. Comments carry legal definitions, sources, non-obvious defaults and rationale — never a restatement of the line below. No `# import <module> module` narration.

---

## File Structure

**In the repo (the whole deliverable):**

| File | Change |
|---|---|
| `src/taxlation/nl/feiten/casus.py` | new — `Casus` + `vereist()` |
| `src/taxlation/nl/feiten/{verkrijger,onroerende_zaak,hoofdverblijf,verkrijging,belastingmiddel}.py` | new — one entity each |
| `src/taxlation/nl/feiten/__init__.py` | new — public names |
| `src/taxlation/nl/versioning.py` | peildatum from casus (D12), nested proxy (D13) |
| `src/taxlation/nl/wbrv/__init__.py` | one export per article |
| `src/taxlation/nl/wbrv/article_1/{example.py,v2006_01_01/translation.py}` | convert |
| `src/taxlation/nl/wbrv/article_2/{example.py,v2025_01_01/translation.py}` | convert |
| `src/taxlation/nl/wbrv/article_15/{__init__.py,example.py,v2025_01_01/*,v2026_01_01/*}` | convert |
| `src/taxlation/nl/wbrv/article_15/v2026_01_01/paragraph_1/` | **deleted** (6 files) |

**Outside the repo (never committed):** `../taxlation-nl-verificatie/{cases/*.json,genereer.py,test_wbrv.py,test_gequarantaineerd.py,test_versioning.py,test_feiten.py}`

---

## Task 1: Harness skeleton and case generator

**Files:** create `../taxlation-nl-verificatie/{toon.py,genereer.py}`

- [ ] **Step 1: Create the directory and the render helper**

Every exception renders as `"raises"` without its type. A missing fact fails today at construction with `TypeError` and afterwards at evaluation with `ValueError` — a change of mechanism, not of legal outcome, which must not surface as a diff. Types and messages are asserted in Task 14.

```bash
mkdir -p ../taxlation-nl-verificatie/cases
```

Create `../taxlation-nl-verificatie/toon.py`:

```python
"""Observatie -> stabiele string, zodat oude en nieuwe uitkomsten vergelijkbaar zijn."""

from datetime import date, timedelta


def _str(waarde) -> str:
    if isinstance(waarde, bool):
        return str(waarde)
    if isinstance(waarde, date):
        return waarde.isoformat()
    if isinstance(waarde, timedelta):
        return f"{waarde.days}d"
    if isinstance(waarde, list):
        return "[" + ", ".join(_str(x) for x in waarde) + "]"
    return str(waarde)


def toon(observeer) -> str:
    """Elke uitzondering wordt "raises": het mechanisme verandert (TypeError bij
    constructie -> ValueError bij evaluatie), de juridische uitkomst niet."""
    try:
        return _str(observeer())
    except Exception:
        return "raises"
```

- [ ] **Step 2: Verify it works**

```bash
cd /Users/ralphmoonlit/Documents/Repositories/Taxlation/taxlation-nl
uv run --with pytest python -c "
import sys; sys.path.insert(0, '../taxlation-nl-verificatie')
from datetime import date, timedelta
from toon import toon
assert toon(lambda: True) == 'True'
assert toon(lambda: date(2025,12,29)) == '2025-12-29'
assert toon(lambda: timedelta(days=3)) == '3d'
assert toon(lambda: [date(2026,1,1)]) == '[2026-01-01]'
def boom(): raise TypeError('x')
assert toon(boom) == 'raises'
print('toon OK')
"
```
Expected: `toon OK`

---

## Task 2: Freeze the WBRV cases

Article 15's matrix runs against **both versions and all three entry levels**. Per D6 each version is an independent implementation, so passing tests for v2025 say nothing about v2026, and a broken nested delegate in the copy must not be able to hide.

**Files:** create `../taxlation-nl-verificatie/genereer.py`, `cases/wbrv.json`

- [ ] **Step 1: Write the generator**

Create `../taxlation-nl-verificatie/genereer.py`:

```python
"""Genereert de cases eenmalig tegen de HUIDIGE code, daarna nooit meer.

Opnieuw genereren na een refactor is precies hoe een refactor zijn eigen regressie
goedkeurt. Toegestane wijzigingen horen in AFWIJKINGEN in de testbestanden.

Gebruik: uv run python ../taxlation-nl-verificatie/genereer.py wbrv
"""

import json
import sys
from datetime import date
from pathlib import Path

from taxlation.nl import wbrv

sys.path.insert(0, str(Path(__file__).parent))
from toon import toon  # noqa: E402

WORTEL = Path(__file__).parent

# observatie -> (klasse in de OUDE api, is het daar een methode)
OUD = {
    "wbrv.Artikel1": {"belasting_van_rechtsverkeer": ("Artikel1", False)},
    "wbrv.Artikel2": {
        "overdrachtsbelasting": ("Artikel2", False),
        "lid_1": ("Artikel2", True),
    },
    "wbrv.Artikel15": {
        "lid_1": ("Artikel15", False),
        "onderdeel_p": ("Artikel15Lid1", True),
        "startersvrijstelling": ("Artikel15Lid1OnderdeelP", True),
    },
}

KLASSEN = {
    "Artikel1": lambda: wbrv.Artikel1,
    "Artikel2": lambda: wbrv.Artikel2,
    "Artikel15": lambda: wbrv.Artikel15,
    "Artikel15Lid1": lambda: wbrv.Artikel15Lid1,
    "Artikel15Lid1OnderdeelP": lambda: wbrv.Artikel15Lid1OnderdeelP,
}


def _waarneem(case, artikel, observatie):
    klasse, is_methode = OUD[artikel][observatie]
    kwargs = dict(case["feiten"])
    if case.get("datum"):
        kwargs["datum_toepassing"] = date.fromisoformat(case["datum"])
    attr = getattr(KLASSEN[klasse]()(**kwargs), observatie)
    return attr() if is_methode else attr


def verwacht(case):
    return {
        naam: toon(lambda naam=naam: _waarneem(case, case["artikel"], naam))
        for naam in case["observaties"]
    }


# --- wbrv ---------------------------------------------------------------------

ART15_BASIS = {
    "woning": True,
    "natuurlijk_persoon": True,
    "leeftijd": 34,
    "vrijstelling_eerder_toegepast": False,
    "verklaring_vrijstelling": True,
    "woning_tijdelijk_hoofdverblijf": False,
    "verklaring_hoofdverblijf": True,
    "waarde_woning": 400_000,
    "waarde_aanhorigheden": 0,
}

NIVEAUS = ["lid_1", "onderdeel_p", "startersvrijstelling"]


def art15_takken(grens):
    """(naam, overschrijvingen, weg te laten velden) per juridische tak."""
    return [
        ("waarde-onder-grens", {"waarde_woning": grens - 15_000, "waarde_aanhorigheden": 5_000}, []),
        ("waarde-op-grens", {"waarde_woning": grens}, []),
        ("waarde-euro-boven-grens", {"waarde_woning": grens + 1}, []),
        ("leeftijd-17", {"leeftijd": 17}, []),
        ("leeftijd-18", {"leeftijd": 18}, []),
        ("leeftijd-34", {"leeftijd": 34}, []),
        ("leeftijd-35", {"leeftijd": 35}, []),
        ("geen-natuurlijk-persoon", {"natuurlijk_persoon": False}, []),
        ("vrijstelling-eerder-toegepast", {"vrijstelling_eerder_toegepast": True}, []),
        ("geen-verklaring-vrijstelling", {"verklaring_vrijstelling": False}, []),
        ("tijdelijk-hoofdverblijf", {"woning_tijdelijk_hoofdverblijf": True}, []),
        ("geen-verklaring-hoofdverblijf", {"verklaring_hoofdverblijf": False}, []),
        ("rechten-woning-onderworpen", {"rechten_woning_onderworpen": True}, ["woning"]),
        ("lidmaatschapsrechten-met-aanhorigheid",
         {"rechten_lidmaatschap_woning": True, "aanhorigheid": True,
          "waarde_woning": grens - 5_000, "waarde_aanhorigheden": 5_000}, ["woning"]),
        ("geen-enkel-woningfeit", {}, ["woning"]),
        ("alle-woningfeiten-onwaar",
         {"woning": False, "rechten_woning_onderworpen": False,
          "rechten_lidmaatschap_woning": False}, []),
        ("woning-waar-rest-onbekend", {}, []),
        ("waarde-aanhorigheden-weggelaten", {}, ["waarde_aanhorigheden"]),
    ]


def wbrv_cases():
    artikel1 = [
        ("beide-bekend-een-waar", {"overdrachtsbelasting": True, "assurantiebelasting": False}),
        ("beide-bekend-ander-waar", {"overdrachtsbelasting": False, "assurantiebelasting": True}),
        ("beide-onwaar", {"overdrachtsbelasting": False, "assurantiebelasting": False}),
        ("een-waar-ander-onbekend", {"overdrachtsbelasting": True}),
        ("een-onwaar-ander-onbekend", {"overdrachtsbelasting": False}),
    ]
    for naam, feiten in artikel1:
        yield {"id": f"art1-{naam}", "artikel": "wbrv.Artikel1", "datum": None,
               "observaties": ["belasting_van_rechtsverkeer"], "feiten": feiten}

    basis2 = {"verkrijging": True, "in_nederland_gelegen": True,
              "onroerende_zaken": True, "rechten_onroerende_zaken_onderworpen": True}
    artikel2 = [
        ("volledig", {}),
        ("alleen-rechten", {"onroerende_zaken": False}),
        ("geen-verkrijging", {"verkrijging": False}),
        ("niet-in-nederland", {"in_nederland_gelegen": False}),
        ("geen-zaak-en-geen-recht",
         {"onroerende_zaken": False, "rechten_onroerende_zaken_onderworpen": False}),
    ]
    for naam, over in artikel2:
        yield {"id": f"art2-{naam}", "artikel": "wbrv.Artikel2", "datum": None,
               "observaties": ["overdrachtsbelasting", "lid_1"], "feiten": {**basis2, **over}}
    for naam, zaak in (("zaak-waar-recht-onbekend", True), ("zaak-onwaar-recht-onbekend", False)):
        feiten = {"verkrijging": True, "in_nederland_gelegen": True, "onroerende_zaken": zaak}
        yield {"id": f"art2-{naam}", "artikel": "wbrv.Artikel2", "datum": None,
               "observaties": ["overdrachtsbelasting", "lid_1"], "feiten": feiten}

    for datum, grens in (("2025-06-01", 525_000), ("2026-06-01", 555_000)):
        for naam, over, weglaten in art15_takken(grens):
            feiten = {**ART15_BASIS, **over}
            for veld in weglaten:
                feiten.pop(veld, None)
            yield {"id": f"art15-{datum[:4]}-{naam}", "artikel": "wbrv.Artikel15",
                   "datum": datum, "observaties": NIVEAUS, "feiten": feiten}

    for datum in ("2024-12-31", "2025-12-31", "2026-01-01"):
        yield {"id": f"art15-versieselectie-{datum}", "artikel": "wbrv.Artikel15",
               "datum": datum, "observaties": ["lid_1"],
               "feiten": {**ART15_BASIS, "waarde_woning": 540_000}}


BOUWERS = {"wbrv": wbrv_cases}

if __name__ == "__main__":
    naam = sys.argv[1]
    cases = [{**c, "verwacht": verwacht(c)} for c in BOUWERS[naam]()]
    pad = WORTEL / "cases" / f"{naam}.json"
    pad.write_text(json.dumps(cases, indent=2, ensure_ascii=False) + "\n")
    print(f"{pad}: {len(cases)} cases")
```

- [ ] **Step 2: Confirm the tree is unmodified**

Run: `git diff --stat src/`
Expected: no output, i.e. zero tracked modifications. **If anything under `src/` is modified, stop** — the cases would record changed behaviour rather than the baseline. (`git status --short src/` will show the pre-existing untracked `atw/17-02-1996/` and `atw/most_recent/` WIP directories; those are unrelated and not a modification.)

- [ ] **Step 3: Generate**

Run: `uv run python ../taxlation-nl-verificatie/genereer.py wbrv`
Expected: `.../cases/wbrv.json: 51 cases`

- [ ] **Step 4: Sanity-check the baselines that matter**

```bash
uv run python -c "
import json
c = {x['id']: x['verwacht'] for x in json.load(open('../taxlation-nl-verificatie/cases/wbrv.json'))}
assert c['art15-2025-waarde-euro-boven-grens']['lid_1'] == 'False'
assert c['art15-2026-waarde-op-grens']['lid_1'] == 'True'
assert c['art15-2025-geen-enkel-woningfeit']['lid_1'] == 'False'
assert c['art1-een-waar-ander-onbekend']['belasting_van_rechtsverkeer'] == 'raises'
assert c['art2-zaak-waar-recht-onbekend']['lid_1'] == 'raises'
print('versiegrenzen en alle vier de divergentie-uitgangspunten bevestigd')
"
```
Expected: `versiegrenzen en alle vier de divergentie-uitgangspunten bevestigd`

The last two are the D5 disjunction cases: one operand known `True` settles the predicate, so these will start answering where they used to raise.

---

## Task 3: The WBRV test

**Files:** create `../taxlation-nl-verificatie/test_wbrv.py`

- [ ] **Step 1: Write the test**

Create `../taxlation-nl-verificatie/test_wbrv.py`:

```python
"""Bevroren cases vs de huidige implementatie.

Alleen bouw() verandert bij conversie. De verwachte waarden in cases/wbrv.json zijn
gegenereerd tegen de code van voor de refactor en bewegen nooit; bewuste
uitzonderingen staan in AFWIJKINGEN.
"""

import json
from datetime import date
from pathlib import Path

import pytest

from taxlation.nl import wbrv

from toon import toon

CASES = json.loads((Path(__file__).parent / "cases" / "wbrv.json").read_text())

# (case_id, observatie) -> (oud, nieuw, reden)
AFWIJKINGEN: dict[tuple[str, str], tuple[str, str, str]] = {}

# observatie -> pad naar het niveau, in de OUDE api
NIVEAU = {
    "belasting_van_rechtsverkeer": ("Artikel1", False),
    "overdrachtsbelasting": ("Artikel2", False),
    "lid_1": ("Artikel2", True),
    "onderdeel_p": ("Artikel15Lid1", True),
    "startersvrijstelling": ("Artikel15Lid1OnderdeelP", True),
}


def bouw(case, observatie):
    """Het ENIGE dat bij conversie verandert."""
    klasse, is_methode = (
        ("Artikel15", False) if case["artikel"] == "wbrv.Artikel15" and observatie == "lid_1"
        else NIVEAU[observatie]
    )
    kwargs = dict(case["feiten"])
    if case.get("datum"):
        kwargs["datum_toepassing"] = date.fromisoformat(case["datum"])
    attr = getattr(getattr(wbrv, klasse)(**kwargs), observatie)
    return attr() if is_methode else attr


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_case(case):
    for naam, bevroren in case["verwacht"].items():
        oud, nieuw, reden = AFWIJKINGEN.get((case["id"], naam), (bevroren, bevroren, ""))
        assert oud == bevroren, f"AFWIJKINGEN[{case['id']!r}, {naam!r}] zegt oud={oud!r}"
        assert toon(lambda naam=naam: bouw(case, naam)) == nieuw, reden or f"{case['id']}.{naam}"
```

- [ ] **Step 2: Run it**

Run: `uv run --with pytest pytest ../taxlation-nl-verificatie -q`
Expected: PASS — `51 passed`

- [ ] **Step 3: Prove the guard bites**

```bash
uv run python -c "
import json, pathlib
p = pathlib.Path('../taxlation-nl-verificatie/cases/wbrv.json')
c = json.loads(p.read_text())
c[0]['verwacht']['belasting_van_rechtsverkeer'] = 'False'
p.write_text(json.dumps(c, indent=2) + '\n')
"
uv run --with pytest pytest ../taxlation-nl-verificatie -q 2>&1 | tail -3
uv run python ../taxlation-nl-verificatie/genereer.py wbrv
```
Expected: a failure naming `art1-beide-bekend-een-waar`, then the file is regenerated. This is the only time regeneration is allowed — after Task 4 the tree changes and the baseline would be wrong.

---

## Task 4: Quarantine the two known legal defects

Cases record what the code *does*; these record what the law *says*. `strict=True` makes an unexpected pass fail, forcing attention when either issue is fixed.

**Files:** create `../taxlation-nl-verificatie/test_gequarantaineerd.py`

- [ ] **Step 1: Write the tests**

Create `../taxlation-nl-verificatie/test_gequarantaineerd.py`:

```python
"""Bekende juridische gebreken, bewust niet gefixt in deze herstructurering.

Elke test noemt de juridisch juiste uitkomst en faalt zolang de code die niet geeft.
Zie github issues #16 en #17.
"""

from datetime import date, timedelta

import pytest

from taxlation.nl import atw, awb


@pytest.mark.xfail(strict=True, reason="#17: uitstel verleend zonder vastgelegde instemming")
def test_awb710_lid4_zonder_instemming_geen_uitstel():
    # Lid 4 staat verder uitstel alleen toe bij instemming (onderdeel a of b) of
    # wettelijke procedurevoorschriften (onderdeel c).
    artikel = awb.Artikel7_10(
        datum_einde_bezwaartermijn=date(2025, 11, 15),
        commissie_ingesteld=False,
        termijn_verder_uitstel=timedelta(days=21),
    )
    assert artikel.datum_einde_beslistermijn == date(2025, 11, 15) + timedelta(weeks=6)


@pytest.mark.xfail(strict=True, reason="#16: artikel 4 onderdeel b ontbreekt")
def test_atw4_onderdeel_b_sluit_de_wet_uit():
    # "Deze wet geldt niet voor termijnen betreffende de bekendmaking,
    # inwerkingtreding of buitenwerkingtreding van wettelijke voorschriften."
    artikel = atw.Artikel4(
        datum_einde_wettelijke_termijn=date(2025, 12, 27),
        wettelijke_termijn=timedelta(days=42),
        wettelijke_termijn_eenheid="dag",
        betreft_bekendmaking_wettelijk_voorschrift=True,
    )
    assert artikel.wet_geldt_niet is True


@pytest.mark.xfail(strict=True, reason="#16: artikel 4 onderdeel c ontbreekt")
def test_atw4_onderdeel_c_sluit_de_wet_uit():
    # "Deze wet geldt niet voor termijnen van vrijheidsbeneming."
    artikel = atw.Artikel4(
        datum_einde_wettelijke_termijn=date(2025, 12, 27),
        wettelijke_termijn=timedelta(days=42),
        wettelijke_termijn_eenheid="dag",
        betreft_vrijheidsbeneming=True,
    )
    assert artikel.wet_geldt_niet is True
```

- [ ] **Step 2: Run it**

Run: `uv run --with pytest pytest ../taxlation-nl-verificatie -q`
Expected: PASS — `51 passed, 3 xfailed`

---

## Task 5: Casus and vereist()

**Files:** create `src/taxlation/nl/feiten/{__init__,casus}.py`, `../taxlation-nl-verificatie/test_feiten.py`

- [ ] **Step 1: Write the failing test**

Create `../taxlation-nl-verificatie/test_feiten.py`:

```python
from dataclasses import dataclass

import pytest

from taxlation.nl.feiten import Casus


@dataclass
class _Nep:
    a: bool | None = None
    b: bool | None = None
    getal: int | None = None


def _casus(**kw) -> Casus:
    casus = Casus()
    casus.verkrijger = _Nep(**kw)
    return casus


def test_alle_feiten_aanwezig():
    _casus(a=True, getal=3).vereist(("verkrijger.a", "verkrijger.getal"), "Test")


def test_ontbrekend_feit_noemt_naam_en_bepaling():
    with pytest.raises(ValueError) as exc:
        _casus(a=True).vereist(("verkrijger.a", "verkrijger.getal"), "Test")
    assert "verkrijger.getal" in str(exc.value)
    assert "Test" in str(exc.value)


def test_alle_ontbrekende_feiten_tegelijk():
    with pytest.raises(ValueError) as exc:
        _casus().vereist(("verkrijger.a", "verkrijger.getal"), "Test")
    assert "verkrijger.a" in str(exc.value)
    assert "verkrijger.getal" in str(exc.value)


def test_ontbrekende_entiteit_telt_als_ontbrekend_feit():
    with pytest.raises(ValueError, match="verkrijger.a"):
        Casus().vereist(("verkrijger.a",), "Test")


def test_disjunctie_een_waar_is_bepaald():
    _casus(a=True).vereist(((("verkrijger.a", "verkrijger.b")),), "Test")


def test_disjunctie_alles_bekend_is_bepaald():
    _casus(a=False, b=False).vereist(((("verkrijger.a", "verkrijger.b")),), "Test")


def test_disjunctie_deels_onbekend_zonder_waar_is_onbepaald():
    with pytest.raises(ValueError, match="verkrijger.a of verkrijger.b"):
        _casus(a=False).vereist(((("verkrijger.a", "verkrijger.b")),), "Test")


def test_wettelijke_standaardwaarde_nul_telt_niet_als_ontbrekend():
    casus = Casus()
    casus.verkrijger = _Nep(getal=0)
    casus.vereist(("verkrijger.getal",), "Test")
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run --with pytest pytest ../taxlation-nl-verificatie/test_feiten.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'taxlation.nl.feiten'`

- [ ] **Step 3: Write the implementation**

Create `src/taxlation/nl/feiten/casus.py`:

```python
from dataclasses import dataclass
from datetime import date


@dataclass
class Casus:
  """De feiten van een casus, gegroepeerd per werkelijk ding waarover ze gaan.

  Alle velden zijn optioneel: geen enkel artikel leest ze allemaal. None betekent
  onbekend, niet onwaar.
  """

  datum_toepassing: date | None = None  # de datum waarnaar de casus wordt beoordeeld

  # entiteiten worden per wet toegevoegd; wbrv opent de rij
  verkrijger: "Verkrijger | None" = None
  zaak: "OnroerendeZaak | None" = None
  hoofdverblijf: "Hoofdverblijf | None" = None
  verkrijging: "Verkrijging | None" = None
  belastingmiddel: "Belastingmiddel | None" = None

  def _lees(self, pad: str):
    waarde = self
    for deel in pad.split("."):
      if waarde is None:
        return None
      waarde = getattr(waarde, deel, None)
    return waarde

  def vereist(self, namen, door: str) -> None:
    """Controleert of de feiten die een bepaling nodig heeft bepaald zijn.

    Een los pad moet bekend zijn. Een tuple is een disjunctie: bepaald zodra een
    onderdeel True is, of zodra alle onderdelen bekend zijn.

    Werpt ValueError met alle ontbrekende feiten tegelijk.
    """
    ontbreekt = []
    for naam in namen:
      if isinstance(naam, tuple):
        waarden = [self._lees(pad) for pad in naam]
        if not any(w is True for w in waarden) and any(w is None for w in waarden):
          ontbreekt.append(" of ".join(naam))
      elif self._lees(naam) is None:
        ontbreekt.append(naam)

    if ontbreekt:
      raise ValueError(f"ontbrekende feiten voor {door}: {', '.join(ontbreekt)}")
```

Create `src/taxlation/nl/feiten/__init__.py`:

```python
from .casus import Casus

__all__ = ["Casus"]
```

- [ ] **Step 4: Run it to verify it passes**

Run: `uv run --with pytest pytest ../taxlation-nl-verificatie -q`
Expected: PASS — `59 passed, 3 xfailed`

- [ ] **Step 5: Commit**

```bash
git add src/taxlation/nl/feiten/
git commit -m ":sparkles: Add Casus with disjunction-aware vereist()"
```

---

## Task 6: WBRV entities

**Files:** create five entity modules; modify `feiten/{__init__,casus}.py`; extend `test_feiten.py`

- [ ] **Step 1: Write the failing test**

Append to `../taxlation-nl-verificatie/test_feiten.py`:

```python
from taxlation.nl.feiten import (  # noqa: E402
    Belastingmiddel,
    Hoofdverblijf,
    OnroerendeZaak,
    Verkrijger,
    Verkrijging,
)


def test_alles_standaard_onbekend():
    assert Verkrijger().leeftijd is None
    assert OnroerendeZaak().woning is None
    assert Hoofdverblijf().verklaring_hoofdverblijf is None
    assert Verkrijging().verkrijging is None
    assert Belastingmiddel().overdrachtsbelasting is None


def test_waarde_aanhorigheden_is_nul_want_de_wet_geeft_die_waarde():
    assert OnroerendeZaak().waarde_aanhorigheden == 0


def test_casus_leest_door_naar_entiteiten():
    casus = Casus(verkrijger=Verkrijger(leeftijd=34), zaak=OnroerendeZaak(woning=True))
    assert casus._lees("verkrijger.leeftijd") == 34
    assert casus._lees("zaak.woning") is True
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run --with pytest pytest ../taxlation-nl-verificatie/test_feiten.py -q`
Expected: FAIL — `ImportError: cannot import name 'Belastingmiddel'`

- [ ] **Step 3: Write the entities**

`src/taxlation/nl/feiten/verkrijger.py`:

```python
from dataclasses import dataclass


@dataclass(kw_only=True)
class Verkrijger:
  """Feiten over de persoon die verkrijgt."""

  natuurlijk_persoon: bool | None = None
  leeftijd: int | None = None
  vrijstelling_eerder_toegepast: bool | None = None
  verklaring_vrijstelling: bool | None = None  # verklaard de vrijstelling niet eerder te hebben toegepast
```

`src/taxlation/nl/feiten/onroerende_zaak.py`:

```python
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
```

`src/taxlation/nl/feiten/hoofdverblijf.py`:

```python
from dataclasses import dataclass


@dataclass(kw_only=True)
class Hoofdverblijf:
  """Feiten over het gebruik van de woning als hoofdverblijf."""

  woning_tijdelijk_hoofdverblijf: bool | None = None
  verklaring_hoofdverblijf: bool | None = None  # verklaard de woning anders dan tijdelijk als hoofdverblijf te gaan gebruiken
```

`src/taxlation/nl/feiten/verkrijging.py`:

```python
from dataclasses import dataclass


@dataclass(kw_only=True)
class Verkrijging:
  """Feiten over de verkrijging zelf."""

  verkrijging: bool | None = None
```

`src/taxlation/nl/feiten/belastingmiddel.py`:

```python
from dataclasses import dataclass


@dataclass(kw_only=True)
class Belastingmiddel:
  """Welk belastingmiddel aan de orde is."""

  overdrachtsbelasting: bool | None = None  # hoofdstuk II WBRV
  assurantiebelasting: bool | None = None  # hoofdstuk III WBRV
```

In `casus.py` add the imports and drop the quotes from the five slot annotations:

```python
from .belastingmiddel import Belastingmiddel
from .hoofdverblijf import Hoofdverblijf
from .onroerende_zaak import OnroerendeZaak
from .verkrijger import Verkrijger
from .verkrijging import Verkrijging
```

```python
  verkrijger: Verkrijger | None = None
  zaak: OnroerendeZaak | None = None
  hoofdverblijf: Hoofdverblijf | None = None
  verkrijging: Verkrijging | None = None
  belastingmiddel: Belastingmiddel | None = None
```

Replace `src/taxlation/nl/feiten/__init__.py`:

```python
from .belastingmiddel import Belastingmiddel
from .casus import Casus
from .hoofdverblijf import Hoofdverblijf
from .onroerende_zaak import OnroerendeZaak
from .verkrijger import Verkrijger
from .verkrijging import Verkrijging

__all__ = [
    "Belastingmiddel",
    "Casus",
    "Hoofdverblijf",
    "OnroerendeZaak",
    "Verkrijger",
    "Verkrijging",
]
```

- [ ] **Step 4: Run it to verify it passes**

Run: `uv run --with pytest pytest ../taxlation-nl-verificatie -q`
Expected: PASS — `62 passed, 3 xfailed`

- [ ] **Step 5: Commit**

```bash
git add src/taxlation/nl/feiten/
git commit -m ":sparkles: Add WBRV fact entities"
```

---

## Task 7: VersieArtikel takes the peildatum from the casus (D12)

An explicit `datum_toepassing` selects the outer version, but a delegated call later re-reads `casus.datum_toepassing` — so without normalising, one evaluation can mix versions. The casus is made authoritative and a conflict refused.

**Files:** modify `src/taxlation/nl/versioning.py`; create `../taxlation-nl-verificatie/test_versioning.py`

- [ ] **Step 1: Write the failing test**

Create `../taxlation-nl-verificatie/test_versioning.py`:

```python
from dataclasses import dataclass
from datetime import date

import pytest

from taxlation.nl.feiten import Casus
from taxlation.nl.versioning import VersieArtikel


@dataclass
class _V2025:
    casus: Casus

    @property
    def antwoord(self) -> str:
        return "2025"

    @property
    def via_delegatie(self) -> str:
        # Pas gelezen nadat __call__ is teruggekeerd; hier faalt een contextvariabele
        # en moet de casus de peildatum dragen.
        return ARTIKEL(casus=self.casus).antwoord


@dataclass
class _V2026:
    casus: Casus

    @property
    def antwoord(self) -> str:
        return "2026"

    @property
    def via_delegatie(self) -> str:
        return ARTIKEL(casus=self.casus).antwoord


ARTIKEL = VersieArtikel(name="Test", versions={date(2025, 1, 1): _V2025, date(2026, 1, 1): _V2026})


def test_casusdatum_kiest_de_versie():
    assert ARTIKEL(casus=Casus(datum_toepassing=date(2025, 6, 1))).antwoord == "2025"
    assert ARTIKEL(casus=Casus(datum_toepassing=date(2026, 6, 1))).antwoord == "2026"


def test_expliciete_datum_kiest_de_versie():
    assert ARTIKEL(datum_toepassing=date(2026, 6, 1), casus=Casus()).antwoord == "2026"


def test_expliciete_datum_bereikt_ook_gedelegeerde_aanroepen():
    # Zonder stempelen zou via_delegatie terugvallen op date.today().
    assert ARTIKEL(datum_toepassing=date(2025, 6, 1), casus=Casus()).via_delegatie == "2025"


def test_gedelegeerde_aanroep_houdt_dezelfde_versie():
    artikel = ARTIKEL(casus=Casus(datum_toepassing=date(2026, 6, 1)))
    assert artikel.antwoord == artikel.via_delegatie == "2026"


def test_tegenstrijdige_datums_worden_geweigerd():
    with pytest.raises(ValueError, match="spreken elkaar tegen"):
        ARTIKEL(datum_toepassing=date(2025, 6, 1), casus=Casus(datum_toepassing=date(2026, 6, 1)))


def test_voor_de_eerste_versie_werpt():
    with pytest.raises(ValueError, match="No version from Test"):
        ARTIKEL(casus=Casus(datum_toepassing=date(2024, 1, 1)))
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run --with pytest pytest ../taxlation-nl-verificatie/test_versioning.py -q`
Expected: FAIL — `TypeError: __call__() got an unexpected keyword argument 'casus'`

- [ ] **Step 3: Write the implementation**

Replace `src/taxlation/nl/versioning.py`:

```python
from dataclasses import replace

from taxlation.core.versioning import VersionedClass


class VersieArtikel(VersionedClass):
  """Selecteert de juiste versie van een artikelklasse."""

  def __call__(self, *, datum_toepassing=None, casus=None, **kwargs):
    """Kiest de versie op de peildatum en bouwt de klasse.

    De casus draagt de peildatum. Een artikel dat een ander artikel bevraagt geeft
    dezelfde casus door en krijgt dus dezelfde versie, ook wanneer die aanroep pas
    plaatsvindt nadat deze methode is teruggekeerd.
    """
    if casus is None:
      return super().__call__(reference_date=datum_toepassing, **kwargs)

    if (
      datum_toepassing is not None
      and casus.datum_toepassing is not None
      and datum_toepassing != casus.datum_toepassing
    ):
      raise ValueError(
        f"datum_toepassing ({datum_toepassing}) en casus.datum_toepassing "
        f"({casus.datum_toepassing}) spreken elkaar tegen"
      )

    peildatum = datum_toepassing or casus.datum_toepassing
    if casus.datum_toepassing is None and peildatum is not None:
      casus = replace(casus, datum_toepassing=peildatum)

    return super().__call__(reference_date=peildatum, casus=casus, **kwargs)
```

- [ ] **Step 4: Run it to verify it passes**

Run: `uv run --with pytest pytest ../taxlation-nl-verificatie -q`
Expected: PASS — `68 passed, 3 xfailed`. The old articles pass no `casus`, so nothing changes for them.

- [ ] **Step 5: Commit**

```bash
git add src/taxlation/nl/versioning.py
git commit -m ":sparkles: VersieArtikel takes the peildatum from the casus"
```

---

## Task 8: Derive nested version maps (D13)

**Files:** modify `src/taxlation/nl/versioning.py`, `test_versioning.py`

- [ ] **Step 1: Write the failing test**

Append to `../taxlation-nl-verificatie/test_versioning.py`:

```python
@dataclass
class _Buiten2025:
    casus: Casus

    @dataclass
    class Lid1:
        casus: Casus

        @property
        def antwoord(self) -> str:
            return "lid1-2025"


@dataclass
class _Buiten2026:
    casus: Casus

    @dataclass
    class Lid1:
        casus: Casus

        @property
        def antwoord(self) -> str:
            return "lid1-2026"

    @dataclass
    class Lid3:
        casus: Casus

        @property
        def antwoord(self) -> str:
            return "lid3-2026"


GENEST = VersieArtikel(
    name="Genest", versions={date(2025, 1, 1): _Buiten2025, date(2026, 1, 1): _Buiten2026}
)


def test_genest_niveau_kiest_dezelfde_versie():
    assert GENEST.Lid1(casus=Casus(datum_toepassing=date(2025, 6, 1))).antwoord == "lid1-2025"
    assert GENEST.Lid1(casus=Casus(datum_toepassing=date(2026, 6, 1))).antwoord == "lid1-2026"


def test_later_ingevoerd_lid_bestaat_pas_vanaf_zijn_versie():
    assert GENEST.Lid3(casus=Casus(datum_toepassing=date(2026, 6, 1))).antwoord == "lid3-2026"
    with pytest.raises(ValueError, match="No version from Genest.Lid3"):
        GENEST.Lid3(casus=Casus(datum_toepassing=date(2025, 6, 1)))


def test_onbekend_attribuut_werpt_attributeerror():
    with pytest.raises(AttributeError):
        GENEST.Lid9
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run --with pytest pytest ../taxlation-nl-verificatie/test_versioning.py -q`
Expected: FAIL — `AttributeError: 'VersieArtikel' object has no attribute 'Lid1'`

- [ ] **Step 3: Write the implementation**

Append to `VersieArtikel`:

```python
  def __getattr__(self, naam):
    """Leidt de versiemap van een genest niveau af uit die van het artikel.

    Welke geneste klasse geldt hangt af van de peildatum, en die is pas bekend bij
    aanroep; daarom levert dit opnieuw een VersieArtikel op. Versies die het niveau
    niet kennen worden overgeslagen, zodat een later ingevoerd lid vanzelf een map
    krijgt die op dat moment begint.
    """
    if naam.startswith("_"):
      raise AttributeError(naam)

    versies = {
      datum: getattr(klasse, naam)
      for datum, klasse in self._versions.items()
      if hasattr(klasse, naam)
    }
    if not versies:
      raise AttributeError(naam)

    return VersieArtikel(name=f"{self._name}.{naam}", versions=versies)
```

- [ ] **Step 4: Run it to verify it passes**

Run: `uv run --with pytest pytest ../taxlation-nl-verificatie -q`
Expected: PASS — `71 passed, 3 xfailed`

- [ ] **Step 5: Commit**

```bash
git add src/taxlation/nl/versioning.py
git commit -m ":sparkles: Derive nested version maps from the article's single map"
```

---

## Task 9: Switch bouw() to the Casus API

From here the test builds articles the new way. Every article is still old, so everything fails — then each conversion task turns a group green.

**Files:** modify `../taxlation-nl-verificatie/test_wbrv.py`

- [ ] **Step 1: Rewrite bouw()**

In `test_wbrv.py`, replace the `NIVEAU` table and `bouw()` with:

```python
from taxlation.nl.feiten import (
    Belastingmiddel,
    Casus,
    Hoofdverblijf,
    OnroerendeZaak,
    Verkrijger,
    Verkrijging,
)

ENTITEITEN = {
    "verkrijger": (Verkrijger, {
        "natuurlijk_persoon", "leeftijd",
        "vrijstelling_eerder_toegepast", "verklaring_vrijstelling",
    }),
    "zaak": (OnroerendeZaak, {
        "woning", "rechten_woning_onderworpen", "rechten_lidmaatschap_woning",
        "aanhorigheid", "in_nederland_gelegen", "onroerende_zaken",
        "rechten_onroerende_zaken_onderworpen", "waarde_woning", "waarde_aanhorigheden",
    }),
    "hoofdverblijf": (Hoofdverblijf, {
        "woning_tijdelijk_hoofdverblijf", "verklaring_hoofdverblijf",
    }),
    "verkrijging": (Verkrijging, {"verkrijging"}),
    "belastingmiddel": (Belastingmiddel, {"overdrachtsbelasting", "assurantiebelasting"}),
}

# observatie -> pad van geneste niveaus onder het artikel
NIVEAU = {
    "belasting_van_rechtsverkeer": (),
    "overdrachtsbelasting": (),
    "lid_1": (),
    "onderdeel_p": ("Lid1",),
    "startersvrijstelling": ("Lid1", "OnderdeelP"),
}


def bouw(case, observatie):
    """Het ENIGE dat bij conversie verandert."""
    casus = Casus(
        datum_toepassing=date.fromisoformat(case["datum"]) if case.get("datum") else None
    )
    for slot, (klasse, velden) in ENTITEITEN.items():
        gevuld = {k: v for k, v in case["feiten"].items() if k in velden}
        if gevuld:
            setattr(casus, slot, klasse(**gevuld))

    doel = getattr(wbrv, case["artikel"].split(".")[1])
    for niveau in NIVEAU[observatie]:
        doel = getattr(doel, niveau)
    return getattr(doel(casus=casus), observatie)
```

- [ ] **Step 2: Confirm everything fails**

Run: `uv run --with pytest pytest ../taxlation-nl-verificatie/test_wbrv.py -q`
Expected: FAIL — all 51 cases, since no article accepts `casus` yet.

---

## Task 10: Convert wbrv artikel 1

**Files:** modify `article_1/v2006_01_01/translation.py`, `article_1/example.py`

- [ ] **Step 1: Convert the article**

Replace `src/taxlation/nl/wbrv/article_1/v2006_01_01/translation.py`:

```python
from dataclasses import dataclass

from taxlation.nl.feiten import Casus


@dataclass
class Artikel1:
  """Artikel 1 WBRV."""

  casus: Casus
  VEREIST = (
    ("belastingmiddel.overdrachtsbelasting", "belastingmiddel.assurantiebelasting"),
  )

  @property
  def belasting_van_rechtsverkeer(self) -> bool:
    """Sprake van een belasting van rechtsverkeer bij overdrachts- of assurantiebelasting."""
    self.casus.vereist(self.VEREIST, "Artikel1")
    belastingmiddel = self.casus.belastingmiddel
    return bool(belastingmiddel.overdrachtsbelasting or belastingmiddel.assurantiebelasting)
```

Replace `src/taxlation/nl/wbrv/article_1/example.py`:

```python
from taxlation.nl import wbrv
from taxlation.nl.feiten import Belastingmiddel, Casus

casus = Casus(
    belastingmiddel=Belastingmiddel(overdrachtsbelasting=True, assurantiebelasting=False),
)

print("Belasting van rechtsverkeer:", wbrv.Artikel1(casus=casus).belasting_van_rechtsverkeer)
```

- [ ] **Step 2: Run it**

Run: `uv run --with pytest pytest ../taxlation-nl-verificatie/test_wbrv.py -q -k "art1-"`
Expected: FAIL — exactly one failure, `art1-een-waar-ander-onbekend`, which now answers `True` where the frozen case says `raises`. The other four pass. This is the D5 disjunction divergence, recorded in Task 14.

Run: `uv run python src/taxlation/nl/wbrv/article_1/example.py`
Expected: `Belasting van rechtsverkeer: True`

- [ ] **Step 3: Commit**

```bash
git add src/taxlation/nl/wbrv/article_1/
git commit -m ":recycle: Convert wbrv artikel 1 to Casus with a disjunctive VEREIST"
```

---

## Task 11: Convert wbrv artikel 2

**Files:** modify `article_2/v2025_01_01/translation.py`, `article_2/example.py`

- [ ] **Step 1: Convert the article**

Replace `src/taxlation/nl/wbrv/article_2/v2025_01_01/translation.py`:

```python
from dataclasses import dataclass

from taxlation.nl.feiten import Casus


@dataclass
class Artikel2:
  """Artikel 2 WBRV."""

  casus: Casus

  @dataclass
  class Lid1:
    """Artikel 2, lid 1 WBRV."""

    casus: Casus
    VEREIST = (
      "verkrijging.verkrijging",
      "zaak.in_nederland_gelegen",
      ("zaak.onroerende_zaken", "zaak.rechten_onroerende_zaken_onderworpen"),
    )

    @property
    def belastbaar_feit(self) -> bool:
      self.casus.vereist(self.VEREIST, "Artikel2.Lid1")
      zaak = self.casus.zaak
      return bool(
        self.casus.verkrijging.verkrijging
        and zaak.in_nederland_gelegen
        and (zaak.onroerende_zaken or zaak.rechten_onroerende_zaken_onderworpen)
      )

  @property
  def lid_1(self) -> bool:
    return Artikel2.Lid1(self.casus).belastbaar_feit

  @property
  def overdrachtsbelasting(self) -> bool:
    """Bepaalt of overdrachtsbelasting wordt geheven."""
    return self.lid_1
```

Replace `src/taxlation/nl/wbrv/article_2/example.py`:

```python
from taxlation.nl import wbrv
from taxlation.nl.feiten import Casus, OnroerendeZaak, Verkrijging

casus = Casus(
    verkrijging=Verkrijging(verkrijging=True),
    zaak=OnroerendeZaak(
        in_nederland_gelegen=True,
        onroerende_zaken=True,
        rechten_onroerende_zaken_onderworpen=True,
    ),
)

print("Belastbaar feit:", wbrv.Artikel2(casus=casus).overdrachtsbelasting)
```

- [ ] **Step 2: Run it**

Run: `uv run --with pytest pytest ../taxlation-nl-verificatie/test_wbrv.py -q -k "art2-"`
Expected: FAIL — exactly one failure, `art2-zaak-waar-recht-onbekend`, which now answers where the frozen case says `raises`. The other six pass.

Run: `uv run python src/taxlation/nl/wbrv/article_2/example.py`
Expected: `Belastbaar feit: True`

- [ ] **Step 3: Commit**

```bash
git add src/taxlation/nl/wbrv/article_2/
git commit -m ":recycle: Convert wbrv artikel 2 to nested Lid1 with a disjunctive VEREIST"
```

---

## Task 12: Convert wbrv artikel 15, both versions

**Files:** modify `article_15/v2025_01_01/{translation,__init__}.py`, `v2026_01_01/{translation,__init__}.py`, `v2026_01_01/README.md`; delete `v2026_01_01/paragraph_1/`

- [ ] **Step 1: Convert v2025**

Replace `src/taxlation/nl/wbrv/article_15/v2025_01_01/translation.py`:

```python
from dataclasses import dataclass

from taxlation.nl.feiten import Casus

WAARDEGRENS = 525_000
LEEFTIJD_MINIMUM = 18
LEEFTIJD_MAXIMUM = 35  # exclusief: de verkrijger moet jonger dan 35 zijn


@dataclass
class Artikel15:
  """Artikel 15 WBRV."""

  casus: Casus

  @dataclass
  class Lid1:
    """Artikel 15, lid 1 WBRV."""

    casus: Casus

    @dataclass
    class OnderdeelP:
      """Artikel 15, lid 1, onderdeel p WBRV: de startersvrijstelling."""

      casus: Casus
      VEREIST = (
        ("zaak.woning", "zaak.rechten_woning_onderworpen", "zaak.rechten_lidmaatschap_woning"),
        "verkrijger.natuurlijk_persoon",
        "verkrijger.leeftijd",
        "verkrijger.vrijstelling_eerder_toegepast",
        "verkrijger.verklaring_vrijstelling",
        "hoofdverblijf.woning_tijdelijk_hoofdverblijf",
        "hoofdverblijf.verklaring_hoofdverblijf",
        "zaak.waarde_woning",
      )

      @property
      def startersvrijstelling(self) -> bool:
        self.casus.vereist(self.VEREIST, "Artikel15.Lid1.OnderdeelP")
        return (
          self._verkrijging_woning
          and self._verkrijger_kwalificeert
          and self._eenmalig_beroep
          and self._hoofdverblijfeis
          and self._binnen_waardegrens
        )

      @property
      def _verkrijging_woning(self) -> bool:
        # Een aanhorigheid deelt in de vrijstelling maar kan die niet zelfstandig doen
        # ontstaan; die telt alleen mee in de waarde.
        zaak = self.casus.zaak
        return bool(
          zaak.woning or zaak.rechten_woning_onderworpen or zaak.rechten_lidmaatschap_woning
        )

      @property
      def _verkrijger_kwalificeert(self) -> bool:
        verkrijger = self.casus.verkrijger
        return bool(
          verkrijger.natuurlijk_persoon
          and LEEFTIJD_MINIMUM <= verkrijger.leeftijd < LEEFTIJD_MAXIMUM
        )

      @property
      def _eenmalig_beroep(self) -> bool:
        verkrijger = self.casus.verkrijger
        return bool(
          not verkrijger.vrijstelling_eerder_toegepast and verkrijger.verklaring_vrijstelling
        )

      @property
      def _hoofdverblijfeis(self) -> bool:
        hoofdverblijf = self.casus.hoofdverblijf
        return bool(
          not hoofdverblijf.woning_tijdelijk_hoofdverblijf
          and hoofdverblijf.verklaring_hoofdverblijf
        )

      @property
      def _binnen_waardegrens(self) -> bool:
        zaak = self.casus.zaak
        return (zaak.waarde_woning + zaak.waarde_aanhorigheden) <= WAARDEGRENS

    @property
    def onderdeel_p(self) -> bool:
      return Artikel15.Lid1.OnderdeelP(self.casus).startersvrijstelling

  @property
  def lid_1(self) -> bool:
    """Bepaalt of de verkrijging is vrijgesteld."""
    return Artikel15.Lid1(self.casus).onderdeel_p
```

Replace both `v2025_01_01/__init__.py` and `v2026_01_01/__init__.py`:

```python
from .translation import Artikel15

__all__ = ["Artikel15"]
```

- [ ] **Step 2: Copy to v2026 and change the one constant**

Per D6 the versions are independent implementations, so this is a **copy**, never an import. Coupling them means a later amendment silently rewrites history.

```bash
cd src/taxlation/nl/wbrv/article_15
cp v2025_01_01/translation.py v2026_01_01/translation.py
sed -i '' 's/^WAARDEGRENS = 525_000$/WAARDEGRENS = 555_000/' v2026_01_01/translation.py
cd -
diff src/taxlation/nl/wbrv/article_15/v2025_01_01/translation.py \
     src/taxlation/nl/wbrv/article_15/v2026_01_01/translation.py
```
Expected:
```
5c5
< WAARDEGRENS = 525_000
---
> WAARDEGRENS = 555_000
```

- [ ] **Step 3: Merge the nested READMEs upward and delete the directories**

Replace `src/taxlation/nl/wbrv/article_15/v2026_01_01/README.md`:

```markdown
# wbrv - artikel 15

## Classes

### Artikel15
- _lid_1_: Stelt vast of artikel 15, lid 1, WBRV van toepassing is (bool).

### Artikel15.Lid1
- _onderdeel_p_: Stelt vast of artikel 15, lid 1, onderdeel p, WBRV van toepassing is (bool).

### Artikel15.Lid1.OnderdeelP
- _startersvrijstelling_: Stelt vast of de startersvrijstelling van toepassing is (bool).

**Feiten** (gelezen uit de casus)
- _zaak.woning_: Of een woning wordt verkregen (bool).
- _zaak.rechten_woning_onderworpen_: Of rechten waaraan een woning is onderworpen worden verkregen (bool).
- _zaak.rechten_lidmaatschap_woning_: Of lidmaatschapsrechten met betrekking tot een woning worden verkregen (bool).
- _zaak.aanhorigheid_: Of gelijktijdig een tot de woning behorende aanhorigheid wordt verkregen (bool).
- _verkrijger.natuurlijk_persoon_: Of de verkrijger een natuurlijk persoon is (bool).
- _verkrijger.leeftijd_: Leeftijd van de verkrijger (int).
- _verkrijger.vrijstelling_eerder_toegepast_: Of de verkrijger de vrijstelling eerder heeft toegepast (bool).
- _verkrijger.verklaring_vrijstelling_: Of de verkrijger heeft verklaard de vrijstelling niet eerder te hebben toegepast (bool).
- _hoofdverblijf.woning_tijdelijk_hoofdverblijf_: Of de woning slechts tijdelijk als hoofdverblijf wordt gebruikt (bool).
- _hoofdverblijf.verklaring_hoofdverblijf_: Of de verkrijger heeft verklaard de woning anders dan tijdelijk als hoofdverblijf te gaan gebruiken (bool).
- _zaak.waarde_woning_: De waarde van de woning (int).
- _zaak.waarde_aanhorigheden_: De waarde van de aanhorigheden (int, standaard 0).
```

```bash
git rm -r src/taxlation/nl/wbrv/article_15/v2026_01_01/paragraph_1
```
Expected: 6 files removed.

- [ ] **Step 4: Commit**

```bash
git add -A src/taxlation/nl/wbrv/article_15/
git commit -m ":recycle: Convert wbrv artikel 15 to nested classes and remove the nested directories"
```

---

## Task 13: Wire up the exports

**Files:** modify `article_15/__init__.py`, `wbrv/__init__.py`, `article_15/example.py`

- [ ] **Step 1: Declare the versions once**

Replace `src/taxlation/nl/wbrv/article_15/__init__.py`:

```python
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
```

- [ ] **Step 2: Reduce the law-level exports**

Replace `src/taxlation/nl/wbrv/__init__.py`:

```python
from .article_1 import Artikel1
from .article_2 import Artikel2
from .article_15 import Artikel15

__all__ = ["Artikel1", "Artikel2", "Artikel15"]
```

- [ ] **Step 3: Rewrite the example**

Replace `src/taxlation/nl/wbrv/article_15/example.py`:

```python
from datetime import date

from taxlation.nl import wbrv
from taxlation.nl.feiten import Casus, Hoofdverblijf, OnroerendeZaak, Verkrijger

casus = Casus(
    datum_toepassing=date(2025, 1, 1),
    verkrijger=Verkrijger(
        natuurlijk_persoon=True,
        leeftijd=34,
        vrijstelling_eerder_toegepast=False,
        verklaring_vrijstelling=True,
    ),
    zaak=OnroerendeZaak(woning=True, waarde_woning=510000, waarde_aanhorigheden=5000),
    hoofdverblijf=Hoofdverblijf(
        woning_tijdelijk_hoofdverblijf=False,
        verklaring_hoofdverblijf=True,
    ),
)

print("Startersvrijstelling artikel 15:", wbrv.Artikel15(casus=casus).lid_1)
print("Artikel 15, lid 1:", wbrv.Artikel15.Lid1(casus=casus).onderdeel_p)
print(
    "Artikel 15, lid 1, onderdeel p:",
    wbrv.Artikel15.Lid1.OnderdeelP(casus=casus).startersvrijstelling,
)
```

- [ ] **Step 4: Run it**

Run: `uv run --with pytest pytest ../taxlation-nl-verificatie/test_wbrv.py -q -k "art15-"`
Expected: FAIL — exactly two failures, `art15-2025-geen-enkel-woningfeit` and `art15-2026-geen-enkel-woningfeit`, which now raise where the frozen cases say `False`. All 37 other article-15 cases pass, across **both** versions and all three entry levels.

Run: `uv run python src/taxlation/nl/wbrv/article_15/example.py`
Expected:
```
Startersvrijstelling artikel 15: True
Artikel 15, lid 1: True
Artikel 15, lid 1, onderdeel p: True
```

- [ ] **Step 5: Commit**

```bash
git add src/taxlation/nl/wbrv/
git commit -m ":recycle: Declare wbrv artikel 15 versions once and derive nested levels"
```

---

## Task 14: Record the four divergences

**Files:** modify `../taxlation-nl-verificatie/test_wbrv.py`

- [ ] **Step 1: Record them**

Replace the empty `AFWIJKINGEN` in `test_wbrv.py`:

```python
_D5 = (
    "Spec D5: VEREIST volgt de juridische voorwaarde, niet de oude dataclass-"
    "standaardwaarden. Een disjunctie is bepaald zodra een onderdeel True is, of zodra "
    "alle onderdelen bekend zijn."
)

AFWIJKINGEN: dict[tuple[str, str], tuple[str, str, str]] = {
    # Voorheen stil False: 'niet vrijgesteld' en 'onvoldoende gegevens' werden op één
    # hoop gegooid, terwijl dat juridisch verschillende antwoorden zijn.
    ("art15-2025-geen-enkel-woningfeit", "lid_1"): ("False", "raises", _D5),
    ("art15-2026-geen-enkel-woningfeit", "lid_1"): ("False", "raises", _D5),
    # Voorheen een TypeError bij constructie: het ontbrekende tweede onderdeel werd
    # geëist terwijl het eerste de uitkomst al bepaalt.
    ("art1-een-waar-ander-onbekend", "belasting_van_rechtsverkeer"): ("raises", "True", _D5),
    ("art2-zaak-waar-recht-onbekend", "lid_1"): ("raises", "True", _D5),
}
```

- [ ] **Step 2: Assert the exception messages**

`toon()` collapses every exception to `"raises"`, so type and message are pinned separately. Append to `test_wbrv.py`:

```python
def _casus_art15(**zaak) -> Casus:
    return Casus(
        datum_toepassing=date(2025, 6, 1),
        verkrijger=Verkrijger(
            natuurlijk_persoon=True,
            leeftijd=34,
            vrijstelling_eerder_toegepast=False,
            verklaring_vrijstelling=True,
        ),
        zaak=OnroerendeZaak(waarde_woning=400000, waarde_aanhorigheden=0, **zaak),
        hoofdverblijf=Hoofdverblijf(
            woning_tijdelijk_hoofdverblijf=False,
            verklaring_hoofdverblijf=True,
        ),
    )


def test_art15_geen_woningfeit_noemt_de_disjunctie():
    with pytest.raises(ValueError) as exc:
        wbrv.Artikel15(casus=_casus_art15()).lid_1
    boodschap = str(exc.value)
    assert "Artikel15.Lid1.OnderdeelP" in boodschap
    assert (
        "zaak.woning of zaak.rechten_woning_onderworpen of zaak.rechten_lidmaatschap_woning"
        in boodschap
    )


def test_art15_een_waar_woningfeit_is_genoeg():
    assert wbrv.Artikel15(casus=_casus_art15(rechten_lidmaatschap_woning=True)).lid_1 is True


def test_art15_alle_woningfeiten_onwaar_is_bepaald():
    casus = _casus_art15(
        woning=False, rechten_woning_onderworpen=False, rechten_lidmaatschap_woning=False
    )
    assert wbrv.Artikel15(casus=casus).lid_1 is False


def test_art1_een_onwaar_middel_laat_de_vraag_open():
    casus = Casus(belastingmiddel=Belastingmiddel(overdrachtsbelasting=False))
    with pytest.raises(ValueError, match="overdrachtsbelasting of"):
        wbrv.Artikel1(casus=casus).belasting_van_rechtsverkeer


def test_art2_een_onwaar_zaakfeit_laat_de_vraag_open():
    casus = Casus(
        verkrijging=Verkrijging(verkrijging=True),
        zaak=OnroerendeZaak(in_nederland_gelegen=True, onroerende_zaken=False),
    )
    with pytest.raises(ValueError, match="onroerende_zaken of"):
        wbrv.Artikel2(casus=casus).overdrachtsbelasting
```

- [ ] **Step 3: Run everything**

Run: `uv run --with pytest pytest ../taxlation-nl-verificatie -q`
Expected: PASS — `76 passed, 3 xfailed`

Note the two `geen-enkel-woningfeit` cases carry three observations but only `lid_1` needs an entry: `onderdeel_p` and `startersvrijstelling` already froze as `raises`, since the old nested classes required those fields at construction.

---

## Task 15: Final verification and the D9 record

- [ ] **Step 1: Full suite**

Run: `uv run --with pytest pytest ../taxlation-nl-verificatie -q`
Expected: PASS — `76 passed, 3 xfailed`

- [ ] **Step 2: Confirm the cases were never regenerated after Task 4**

Run: `ls -l ../taxlation-nl-verificatie/cases/wbrv.json`
The mtime must predate the first `src/` change. If it does not, the baseline recorded refactored behaviour and the whole run is void.

- [ ] **Step 3: Run every example**

```bash
for f in src/taxlation/nl/wbrv/article_*/example.py; do echo "--- $f"; uv run python "$f"; done
```
Expected:
```
--- src/taxlation/nl/wbrv/article_15/example.py
Startersvrijstelling artikel 15: True
Artikel 15, lid 1: True
Artikel 15, lid 1, onderdeel p: True
--- src/taxlation/nl/wbrv/article_1/example.py
Belasting van rechtsverkeer: True
--- src/taxlation/nl/wbrv/article_2/example.py
Belastbaar feit: True
```

- [ ] **Step 4: Confirm the branch holds only core code**

```bash
git status --short
git diff --stat wbrv..HEAD -- src/
```
Expected: `git status` shows only the pre-existing untracked `atw/17-02-1996/` and `atw/most_recent/` directories, and **nothing from `../taxlation-nl-verificatie/`**. The `src/` diff touches only `feiten/`, `versioning.py`, `wbrv/**` and the `atw` legislation swap.

- [ ] **Step 5: Confirm no comment narration crept in**

Run: `grep -rn "^\s*#\s*import .* module" src/taxlation/nl/feiten src/taxlation/nl/wbrv src/taxlation/nl/versioning.py || echo "clean"`
Expected: `clean`

- [ ] **Step 6: Commit the D9 record**

```bash
git commit --allow-empty -m ":memo: D9 record: members removed by the wbrv conversion

Removed by nesting + delegation (spec D9; no consumers, so no shims):

  wbrv.Artikel15Lid1                   -> wbrv.Artikel15.Lid1
  wbrv.Artikel15Lid1OnderdeelP         -> wbrv.Artikel15.Lid1.OnderdeelP
  Artikel15.onderdeel_p()              -> Artikel15.Lid1(casus).onderdeel_p
  Artikel15.startersvrijstelling()     -> Artikel15.Lid1.OnderdeelP(casus).startersvrijstelling
  Artikel15Lid1.startersvrijstelling() -> as above
  Artikel2.lid_1()                     -> Artikel2.lid_1 (property)

All flat-kwargs constructors are replaced by casus=. Inherited members disappear
because levels no longer inherit; each exposes only its own provision.

wbrv has no consumer: absent from taxlation-api's vendored copy, imported by no
route."
```

---

## Definition of done

- [ ] `uv run --with pytest pytest ../taxlation-nl-verificatie -q` reports `76 passed, 3 xfailed`
- [ ] `cases/wbrv.json` mtime predates the first `src/` change
- [ ] `AFWIJKINGEN` holds exactly four entries, all citing D5
- [ ] `pyproject.toml` is unchanged
- [ ] Nothing from `../taxlation-nl-verificatie/` is tracked by git
- [ ] `src/taxlation/nl/wbrv/article_15/v2026_01_01/paragraph_1/` is gone
- [ ] No `# import <module> module` comments in any touched file

## Handover to Plan 2

Plan 2 converts `awb` and `atw`, reusing this harness. It must first freeze `awb` and `atw` cases the same way, and its ATW cases need **per-article observations** — article 1's and article 2's own `verlenging_termijn`, plus article 3's holiday list — not only the chain's final date, because article 4's reset can otherwise mask a regression upstream.

The case that matters most is the ATW chain returning `2025-12-29` for a 42-day term ending 2025-12-27: that is the assertion `taxlation-api`'s currently-passing route test depends on, and it is what the D11 delegation rewrite is measured against.
