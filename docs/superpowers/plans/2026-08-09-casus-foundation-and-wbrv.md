# Casus Foundation + WBRV Conversion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the characterization oracle for all ten articles, add the `Casus` fact layer and versioning support, and convert the three `wbrv` articles to nested class namespaces without changing any legal outcome.

**Architecture:** Facts move out of article classes into small entity dataclasses collected in a `Casus`. Articles become nested class namespaces (`Artikel15.Lid1.OnderdeelP`) where every level holds only `casus` and delegates downward by passing it. `VersieArtikel` gains a `casus.datum_toepassing` fallback and an attribute proxy so nested levels derive their version map from the article's single map. Correctness is protected by frozen input vectors plus golden results generated from the pre-change code, run through separate old and new adapters.

**Tech Stack:** Python 3.12, `dataclasses`, `pytest`, `uv`. No new runtime dependencies.

**Spec:** `docs/superpowers/specs/2026-08-09-casus-article-structure-design.md`

**Scope:** This plan covers Phase 0 (oracle, all ten articles) and the `wbrv` half of Phase 1. `awb` and `atw` conversion is Plan 2. The `taxlation-api` migration is Plan 3. `wbrv` is first because it has no consumers.

---

## File Structure

**Created:**

| File | Responsibility |
|---|---|
| `tests/conftest.py` | Selects the active adapter via `--adapter` |
| `tests/render.py` | Turns an observation into a stable comparable string |
| `tests/adapters/old.py` | Vector → today's flat-kwargs constructors |
| `tests/adapters/new.py` | Vector → `Casus` |
| `tests/vectors/*.json` | Frozen inputs, facts in domain terms |
| `tests/golden/*.json` | Frozen expected observations, generated once |
| `tests/divergences.py` | Allowlist of authorised behaviour changes |
| `tests/test_characterization.py` | Runs vectors through the active adapter against golden |
| `tests/generate_golden.py` | One-shot golden generator |
| `src/taxlation/nl/feiten/__init__.py` | Public names for the fact layer |
| `src/taxlation/nl/feiten/casus.py` | `Casus` + `vereist()` |
| `src/taxlation/nl/feiten/verkrijger.py` | `Verkrijger` |
| `src/taxlation/nl/feiten/onroerende_zaak.py` | `OnroerendeZaak` |
| `src/taxlation/nl/feiten/hoofdverblijf.py` | `Hoofdverblijf` |
| `src/taxlation/nl/feiten/verkrijging.py` | `Verkrijging` |
| `src/taxlation/nl/feiten/belastingmiddel.py` | `Belastingmiddel` |

**Modified:**

| File | Change |
|---|---|
| `pyproject.toml` | pytest dev group + pytest config |
| `src/taxlation/nl/versioning.py` | `casus` fallback (D12), `__getattr__` proxy (D13) |
| `src/taxlation/nl/wbrv/__init__.py` | One export per article |
| `src/taxlation/nl/wbrv/article_1/{__init__,example}.py`, `v2006_01_01/translation.py` | Convert |
| `src/taxlation/nl/wbrv/article_2/{__init__,example}.py`, `v2025_01_01/translation.py` | Convert |
| `src/taxlation/nl/wbrv/article_15/{__init__,example}.py`, `v2025_01_01/`, `v2026_01_01/` | Convert |

**Deleted:** `src/taxlation/nl/wbrv/article_15/v2026_01_01/paragraph_1/` (6 files)

---

## Task 1: pytest scaffolding

**Files:**
- Modify: `pyproject.toml`
- Create: `tests/__init__.py`, `tests/adapters/__init__.py`, `tests/test_smoke.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_smoke.py`:

```python
def test_package_imports():
    import taxlation.nl  # noqa: F401
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run pytest tests/test_smoke.py -q`
Expected: FAIL — `uv run pytest` errors with "Failed to spawn: `pytest`" because pytest is not installed.

- [ ] **Step 3: Add pytest and its config**

Append to `pyproject.toml`:

```toml
[dependency-groups]
dev = [
    "pytest>=9.1.1",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

Create empty `tests/__init__.py` and `tests/adapters/__init__.py`.

- [ ] **Step 4: Install and run**

Run: `uv sync && uv run pytest tests/test_smoke.py -q`
Expected: PASS — `1 passed`

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock tests/
git commit -m ":white_check_mark: Add pytest scaffolding"
```

---

## Task 2: The render helper

Observations must compare as stable strings across two implementations. Exceptions render as `"raises"` **without the type**, because a missing fact currently fails at construction with `TypeError` and afterwards fails at evaluation with `ValueError` — a change in mechanism, not in legal outcome. Exception types and messages are asserted separately in Task 18.

**Files:**
- Create: `tests/render.py`, `tests/test_render.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_render.py`:

```python
from datetime import date, timedelta

from tests.render import render


def test_bool():
    assert render(lambda: True) == "True"
    assert render(lambda: False) == "False"


def test_int():
    assert render(lambda: 42) == "42"


def test_date():
    assert render(lambda: date(2025, 12, 29)) == "2025-12-29"


def test_timedelta():
    assert render(lambda: timedelta(days=3)) == "3d"


def test_none():
    assert render(lambda: None) == "None"


def test_any_exception_renders_the_same():
    def boom_type():
        raise TypeError("missing argument")

    def boom_value():
        raise ValueError("ontbrekende feiten")

    assert render(boom_type) == "raises"
    assert render(boom_value) == "raises"
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run pytest tests/test_render.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'tests.render'`

- [ ] **Step 3: Write the implementation**

Create `tests/render.py`:

```python
"""Turn an observation into a stable string for golden comparison.

Exceptions render as "raises" without the type. A missing fact fails today at
construction (TypeError) and afterwards at evaluation (ValueError); that is a
change of mechanism, not of legal outcome, so it must not show up as a golden
diff. Exception types and messages are asserted in test_vereist.py instead.
"""

from datetime import date, timedelta


def render(observe) -> str:
    try:
        waarde = observe()
    except Exception:
        return "raises"
    if isinstance(waarde, bool):
        return str(waarde)
    if isinstance(waarde, date):
        return waarde.isoformat()
    if isinstance(waarde, timedelta):
        return f"{waarde.days}d"
    return str(waarde)
```

- [ ] **Step 4: Run it to verify it passes**

Run: `uv run pytest tests/test_render.py -q`
Expected: PASS — `6 passed`

- [ ] **Step 5: Commit**

```bash
git add tests/render.py tests/test_render.py
git commit -m ":white_check_mark: Add render helper for golden comparison"
```

---

## Task 3: WBRV vectors

Vectors hold **inputs only**. Expected values are generated in Task 5, never hand-written — hand-writing them would encode a belief about the code rather than a record of it.

Facts are named in domain terms so the same file feeds both adapters.

**Files:**
- Create: `tests/vectors/wbrv.json`

- [ ] **Step 1: Write the vector file**

Create `tests/vectors/wbrv.json`:

```json
[
  {
    "id": "art1-alleen-overdrachtsbelasting",
    "artikel": "wbrv.Artikel1",
    "observaties": ["belasting_van_rechtsverkeer"],
    "feiten": {"overdrachtsbelasting": true, "assurantiebelasting": false}
  },
  {
    "id": "art1-alleen-assurantiebelasting",
    "artikel": "wbrv.Artikel1",
    "observaties": ["belasting_van_rechtsverkeer"],
    "feiten": {"overdrachtsbelasting": false, "assurantiebelasting": true}
  },
  {
    "id": "art1-geen-van-beide",
    "artikel": "wbrv.Artikel1",
    "observaties": ["belasting_van_rechtsverkeer"],
    "feiten": {"overdrachtsbelasting": false, "assurantiebelasting": false}
  },
  {
    "id": "art1-ontbrekend-feit",
    "artikel": "wbrv.Artikel1",
    "observaties": ["belasting_van_rechtsverkeer"],
    "feiten": {"overdrachtsbelasting": true}
  },
  {
    "id": "art2-volledig-belastbaar-feit",
    "artikel": "wbrv.Artikel2",
    "observaties": ["overdrachtsbelasting", "lid_1"],
    "feiten": {"verkrijging": true, "in_nederland_gelegen": true, "onroerende_zaken": true, "rechten_onroerende_zaken_onderworpen": true}
  },
  {
    "id": "art2-alleen-rechten",
    "artikel": "wbrv.Artikel2",
    "observaties": ["overdrachtsbelasting", "lid_1"],
    "feiten": {"verkrijging": true, "in_nederland_gelegen": true, "onroerende_zaken": false, "rechten_onroerende_zaken_onderworpen": true}
  },
  {
    "id": "art2-geen-verkrijging",
    "artikel": "wbrv.Artikel2",
    "observaties": ["overdrachtsbelasting", "lid_1"],
    "feiten": {"verkrijging": false, "in_nederland_gelegen": true, "onroerende_zaken": true, "rechten_onroerende_zaken_onderworpen": true}
  },
  {
    "id": "art2-niet-in-nederland",
    "artikel": "wbrv.Artikel2",
    "observaties": ["overdrachtsbelasting", "lid_1"],
    "feiten": {"verkrijging": true, "in_nederland_gelegen": false, "onroerende_zaken": true, "rechten_onroerende_zaken_onderworpen": true}
  },
  {
    "id": "art2-geen-zaak-en-geen-recht",
    "artikel": "wbrv.Artikel2",
    "observaties": ["overdrachtsbelasting", "lid_1"],
    "feiten": {"verkrijging": true, "in_nederland_gelegen": true, "onroerende_zaken": false, "rechten_onroerende_zaken_onderworpen": false}
  },
  {
    "id": "art15-2025-onder-waardegrens",
    "artikel": "wbrv.Artikel15",
    "datum_toepassing": "2025-06-01",
    "observaties": ["lid_1", "onderdeel_p", "startersvrijstelling"],
    "feiten": {"woning": true, "natuurlijk_persoon": true, "leeftijd": 34, "vrijstelling_eerder_toegepast": false, "verklaring_vrijstelling": true, "woning_tijdelijk_hoofdverblijf": false, "verklaring_hoofdverblijf": true, "waarde_woning": 510000, "waarde_aanhorigheden": 5000}
  },
  {
    "id": "art15-2025-precies-op-waardegrens",
    "artikel": "wbrv.Artikel15",
    "datum_toepassing": "2025-06-01",
    "observaties": ["lid_1", "onderdeel_p", "startersvrijstelling"],
    "feiten": {"woning": true, "natuurlijk_persoon": true, "leeftijd": 34, "vrijstelling_eerder_toegepast": false, "verklaring_vrijstelling": true, "woning_tijdelijk_hoofdverblijf": false, "verklaring_hoofdverblijf": true, "waarde_woning": 525000, "waarde_aanhorigheden": 0}
  },
  {
    "id": "art15-2025-een-euro-boven-waardegrens",
    "artikel": "wbrv.Artikel15",
    "datum_toepassing": "2025-06-01",
    "observaties": ["lid_1", "onderdeel_p", "startersvrijstelling"],
    "feiten": {"woning": true, "natuurlijk_persoon": true, "leeftijd": 34, "vrijstelling_eerder_toegepast": false, "verklaring_vrijstelling": true, "woning_tijdelijk_hoofdverblijf": false, "verklaring_hoofdverblijf": true, "waarde_woning": 525001, "waarde_aanhorigheden": 0}
  },
  {
    "id": "art15-2025-545k-boven-grens",
    "artikel": "wbrv.Artikel15",
    "datum_toepassing": "2025-06-01",
    "observaties": ["lid_1"],
    "feiten": {"woning": true, "natuurlijk_persoon": true, "leeftijd": 34, "vrijstelling_eerder_toegepast": false, "verklaring_vrijstelling": true, "woning_tijdelijk_hoofdverblijf": false, "verklaring_hoofdverblijf": true, "waarde_woning": 540000, "waarde_aanhorigheden": 5000}
  },
  {
    "id": "art15-2026-545k-onder-grens",
    "artikel": "wbrv.Artikel15",
    "datum_toepassing": "2026-06-01",
    "observaties": ["lid_1"],
    "feiten": {"woning": true, "natuurlijk_persoon": true, "leeftijd": 34, "vrijstelling_eerder_toegepast": false, "verklaring_vrijstelling": true, "woning_tijdelijk_hoofdverblijf": false, "verklaring_hoofdverblijf": true, "waarde_woning": 540000, "waarde_aanhorigheden": 5000}
  },
  {
    "id": "art15-2026-precies-op-waardegrens",
    "artikel": "wbrv.Artikel15",
    "datum_toepassing": "2026-06-01",
    "observaties": ["lid_1"],
    "feiten": {"woning": true, "natuurlijk_persoon": true, "leeftijd": 34, "vrijstelling_eerder_toegepast": false, "verklaring_vrijstelling": true, "woning_tijdelijk_hoofdverblijf": false, "verklaring_hoofdverblijf": true, "waarde_woning": 555000, "waarde_aanhorigheden": 0}
  },
  {
    "id": "art15-2026-een-euro-boven-waardegrens",
    "artikel": "wbrv.Artikel15",
    "datum_toepassing": "2026-06-01",
    "observaties": ["lid_1"],
    "feiten": {"woning": true, "natuurlijk_persoon": true, "leeftijd": 34, "vrijstelling_eerder_toegepast": false, "verklaring_vrijstelling": true, "woning_tijdelijk_hoofdverblijf": false, "verklaring_hoofdverblijf": true, "waarde_woning": 555001, "waarde_aanhorigheden": 0}
  },
  {
    "id": "art15-2025-daags-voor-inwerkingtreding-2026",
    "artikel": "wbrv.Artikel15",
    "datum_toepassing": "2025-12-31",
    "observaties": ["lid_1"],
    "feiten": {"woning": true, "natuurlijk_persoon": true, "leeftijd": 34, "vrijstelling_eerder_toegepast": false, "verklaring_vrijstelling": true, "woning_tijdelijk_hoofdverblijf": false, "verklaring_hoofdverblijf": true, "waarde_woning": 540000, "waarde_aanhorigheden": 0}
  },
  {
    "id": "art15-2026-op-inwerkingtreding",
    "artikel": "wbrv.Artikel15",
    "datum_toepassing": "2026-01-01",
    "observaties": ["lid_1"],
    "feiten": {"woning": true, "natuurlijk_persoon": true, "leeftijd": 34, "vrijstelling_eerder_toegepast": false, "verklaring_vrijstelling": true, "woning_tijdelijk_hoofdverblijf": false, "verklaring_hoofdverblijf": true, "waarde_woning": 540000, "waarde_aanhorigheden": 0}
  },
  {
    "id": "art15-voor-eerste-versie",
    "artikel": "wbrv.Artikel15",
    "datum_toepassing": "2024-12-31",
    "observaties": ["lid_1"],
    "feiten": {"woning": true, "natuurlijk_persoon": true, "leeftijd": 34, "vrijstelling_eerder_toegepast": false, "verklaring_vrijstelling": true, "woning_tijdelijk_hoofdverblijf": false, "verklaring_hoofdverblijf": true, "waarde_woning": 400000, "waarde_aanhorigheden": 0}
  },
  {
    "id": "art15-leeftijd-17-te-jong",
    "artikel": "wbrv.Artikel15",
    "datum_toepassing": "2025-06-01",
    "observaties": ["lid_1"],
    "feiten": {"woning": true, "natuurlijk_persoon": true, "leeftijd": 17, "vrijstelling_eerder_toegepast": false, "verklaring_vrijstelling": true, "woning_tijdelijk_hoofdverblijf": false, "verklaring_hoofdverblijf": true, "waarde_woning": 400000, "waarde_aanhorigheden": 0}
  },
  {
    "id": "art15-leeftijd-18-ondergrens",
    "artikel": "wbrv.Artikel15",
    "datum_toepassing": "2025-06-01",
    "observaties": ["lid_1"],
    "feiten": {"woning": true, "natuurlijk_persoon": true, "leeftijd": 18, "vrijstelling_eerder_toegepast": false, "verklaring_vrijstelling": true, "woning_tijdelijk_hoofdverblijf": false, "verklaring_hoofdverblijf": true, "waarde_woning": 400000, "waarde_aanhorigheden": 0}
  },
  {
    "id": "art15-leeftijd-34-bovengrens",
    "artikel": "wbrv.Artikel15",
    "datum_toepassing": "2025-06-01",
    "observaties": ["lid_1"],
    "feiten": {"woning": true, "natuurlijk_persoon": true, "leeftijd": 34, "vrijstelling_eerder_toegepast": false, "verklaring_vrijstelling": true, "woning_tijdelijk_hoofdverblijf": false, "verklaring_hoofdverblijf": true, "waarde_woning": 400000, "waarde_aanhorigheden": 0}
  },
  {
    "id": "art15-leeftijd-35-te-oud",
    "artikel": "wbrv.Artikel15",
    "datum_toepassing": "2025-06-01",
    "observaties": ["lid_1"],
    "feiten": {"woning": true, "natuurlijk_persoon": true, "leeftijd": 35, "vrijstelling_eerder_toegepast": false, "verklaring_vrijstelling": true, "woning_tijdelijk_hoofdverblijf": false, "verklaring_hoofdverblijf": true, "waarde_woning": 400000, "waarde_aanhorigheden": 0}
  },
  {
    "id": "art15-geen-natuurlijk-persoon",
    "artikel": "wbrv.Artikel15",
    "datum_toepassing": "2025-06-01",
    "observaties": ["lid_1"],
    "feiten": {"woning": true, "natuurlijk_persoon": false, "leeftijd": 34, "vrijstelling_eerder_toegepast": false, "verklaring_vrijstelling": true, "woning_tijdelijk_hoofdverblijf": false, "verklaring_hoofdverblijf": true, "waarde_woning": 400000, "waarde_aanhorigheden": 0}
  },
  {
    "id": "art15-vrijstelling-eerder-toegepast",
    "artikel": "wbrv.Artikel15",
    "datum_toepassing": "2025-06-01",
    "observaties": ["lid_1"],
    "feiten": {"woning": true, "natuurlijk_persoon": true, "leeftijd": 34, "vrijstelling_eerder_toegepast": true, "verklaring_vrijstelling": true, "woning_tijdelijk_hoofdverblijf": false, "verklaring_hoofdverblijf": true, "waarde_woning": 400000, "waarde_aanhorigheden": 0}
  },
  {
    "id": "art15-geen-verklaring-vrijstelling",
    "artikel": "wbrv.Artikel15",
    "datum_toepassing": "2025-06-01",
    "observaties": ["lid_1"],
    "feiten": {"woning": true, "natuurlijk_persoon": true, "leeftijd": 34, "vrijstelling_eerder_toegepast": false, "verklaring_vrijstelling": false, "woning_tijdelijk_hoofdverblijf": false, "verklaring_hoofdverblijf": true, "waarde_woning": 400000, "waarde_aanhorigheden": 0}
  },
  {
    "id": "art15-tijdelijk-hoofdverblijf",
    "artikel": "wbrv.Artikel15",
    "datum_toepassing": "2025-06-01",
    "observaties": ["lid_1"],
    "feiten": {"woning": true, "natuurlijk_persoon": true, "leeftijd": 34, "vrijstelling_eerder_toegepast": false, "verklaring_vrijstelling": true, "woning_tijdelijk_hoofdverblijf": true, "verklaring_hoofdverblijf": true, "waarde_woning": 400000, "waarde_aanhorigheden": 0}
  },
  {
    "id": "art15-geen-verklaring-hoofdverblijf",
    "artikel": "wbrv.Artikel15",
    "datum_toepassing": "2025-06-01",
    "observaties": ["lid_1"],
    "feiten": {"woning": true, "natuurlijk_persoon": true, "leeftijd": 34, "vrijstelling_eerder_toegepast": false, "verklaring_vrijstelling": true, "woning_tijdelijk_hoofdverblijf": false, "verklaring_hoofdverblijf": false, "waarde_woning": 400000, "waarde_aanhorigheden": 0}
  },
  {
    "id": "art15-rechten-woning-onderworpen",
    "artikel": "wbrv.Artikel15",
    "datum_toepassing": "2025-06-01",
    "observaties": ["lid_1"],
    "feiten": {"rechten_woning_onderworpen": true, "natuurlijk_persoon": true, "leeftijd": 34, "vrijstelling_eerder_toegepast": false, "verklaring_vrijstelling": true, "woning_tijdelijk_hoofdverblijf": false, "verklaring_hoofdverblijf": true, "waarde_woning": 400000, "waarde_aanhorigheden": 0}
  },
  {
    "id": "art15-lidmaatschapsrechten-met-aanhorigheid",
    "artikel": "wbrv.Artikel15",
    "datum_toepassing": "2025-06-01",
    "observaties": ["lid_1"],
    "feiten": {"rechten_lidmaatschap_woning": true, "aanhorigheid": true, "natuurlijk_persoon": true, "leeftijd": 34, "vrijstelling_eerder_toegepast": false, "verklaring_vrijstelling": true, "woning_tijdelijk_hoofdverblijf": false, "verklaring_hoofdverblijf": true, "waarde_woning": 520000, "waarde_aanhorigheden": 5000}
  },
  {
    "id": "art15-geen-enkel-woningfeit",
    "artikel": "wbrv.Artikel15",
    "datum_toepassing": "2025-06-01",
    "observaties": ["lid_1"],
    "feiten": {"natuurlijk_persoon": true, "leeftijd": 34, "vrijstelling_eerder_toegepast": false, "verklaring_vrijstelling": true, "woning_tijdelijk_hoofdverblijf": false, "verklaring_hoofdverblijf": true, "waarde_woning": 400000, "waarde_aanhorigheden": 0}
  },
  {
    "id": "art15-waarde-aanhorigheden-weggelaten",
    "artikel": "wbrv.Artikel15",
    "datum_toepassing": "2025-06-01",
    "observaties": ["lid_1"],
    "feiten": {"woning": true, "natuurlijk_persoon": true, "leeftijd": 34, "vrijstelling_eerder_toegepast": false, "verklaring_vrijstelling": true, "woning_tijdelijk_hoofdverblijf": false, "verklaring_hoofdverblijf": true, "waarde_woning": 400000}
  }
]
```

`art15-geen-enkel-woningfeit` is the vector that will diverge in Task 18. `art15-waarde-aanhorigheden-weggelaten` pins the law-supplied `0` default. `art1-ontbrekend-feit` pins that an omitted required fact raises.

- [ ] **Step 2: Verify it parses and ids are unique**

Run:
```bash
uv run python -c "
import json, collections
v = json.load(open('tests/vectors/wbrv.json'))
ids = [x['id'] for x in v]
dupes = [i for i, n in collections.Counter(ids).items() if n > 1]
assert not dupes, dupes
print(len(v), 'vectors, ids unique')
"
```
Expected: `32 vectors, ids unique`

- [ ] **Step 3: Commit**

```bash
git add tests/vectors/wbrv.json
git commit -m ":white_check_mark: Add frozen WBRV case vectors"
```

---

## Task 4: The old adapter

**Files:**
- Create: `tests/adapters/old.py`, `tests/test_adapter_old.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_adapter_old.py`:

```python
from tests.adapters.old import observeer


def test_art1_true():
    vector = {
        "artikel": "wbrv.Artikel1",
        "feiten": {"overdrachtsbelasting": True, "assurantiebelasting": False},
        "observaties": ["belasting_van_rechtsverkeer"],
    }
    assert observeer(vector) == {"belasting_van_rechtsverkeer": "True"}


def test_art15_version_boundary():
    feiten = {
        "woning": True, "natuurlijk_persoon": True, "leeftijd": 34,
        "vrijstelling_eerder_toegepast": False, "verklaring_vrijstelling": True,
        "woning_tijdelijk_hoofdverblijf": False, "verklaring_hoofdverblijf": True,
        "waarde_woning": 540000, "waarde_aanhorigheden": 5000,
    }
    base = {"artikel": "wbrv.Artikel15", "feiten": feiten, "observaties": ["lid_1"]}
    assert observeer({**base, "datum_toepassing": "2025-06-01"}) == {"lid_1": "False"}
    assert observeer({**base, "datum_toepassing": "2026-06-01"}) == {"lid_1": "True"}


def test_missing_fact_renders_as_raises():
    vector = {
        "artikel": "wbrv.Artikel1",
        "feiten": {"overdrachtsbelasting": True},
        "observaties": ["belasting_van_rechtsverkeer"],
    }
    assert observeer(vector) == {"belasting_van_rechtsverkeer": "raises"}
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run pytest tests/test_adapter_old.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'tests.adapters.old'`

- [ ] **Step 3: Write the implementation**

Create `tests/adapters/old.py`:

```python
"""Vector -> today's flat-kwargs constructors.

Deleted together with the old implementation once Plan 2 finishes. Until then it
is what proves the new adapter produces identical legal outcomes.
"""

from datetime import date

from taxlation.nl import wbrv

from tests.render import render

# Which class carries each observation, and whether it is a method today.
# ("", ...) means the observation lives on the article class itself.
OBSERVATIES = {
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

# The old API exposes each level as its own top-level name.
NIVEAUS = {
    "Artikel1": lambda: wbrv.Artikel1,
    "Artikel2": lambda: wbrv.Artikel2,
    "Artikel15": lambda: wbrv.Artikel15,
    "Artikel15Lid1": lambda: wbrv.Artikel15Lid1,
    "Artikel15Lid1OnderdeelP": lambda: wbrv.Artikel15Lid1OnderdeelP,
}


def _bouw(vector, niveau):
    kwargs = dict(vector["feiten"])
    if "datum_toepassing" in vector:
        kwargs["datum_toepassing"] = date.fromisoformat(vector["datum_toepassing"])
    return NIVEAUS[niveau]()(**kwargs)


def observeer(vector) -> dict:
    resultaat = {}
    for naam in vector["observaties"]:
        niveau, is_methode = OBSERVATIES[vector["artikel"]][naam]

        def waarnemen(niveau=niveau, naam=naam, is_methode=is_methode):
            obj = _bouw(vector, niveau)
            attr = getattr(obj, naam)
            return attr() if is_methode else attr

        resultaat[naam] = render(waarnemen)
    return resultaat
```

- [ ] **Step 4: Run it to verify it passes**

Run: `uv run pytest tests/test_adapter_old.py -q`
Expected: PASS — `3 passed`

- [ ] **Step 5: Commit**

```bash
git add tests/adapters/old.py tests/test_adapter_old.py
git commit -m ":white_check_mark: Add old-API adapter"
```

---

## Task 5: Generate and freeze the WBRV goldens

**Files:**
- Create: `tests/generate_golden.py`, `tests/golden/wbrv.json`

- [ ] **Step 1: Write the generator**

Create `tests/generate_golden.py`:

```python
"""One-shot golden generator. Run against UNMODIFIED code, then never again.

Regenerating goldens after a refactor is how a refactor certifies its own
regression. Golden files are frozen artifacts; authorised changes go in
tests/divergences.py.

Usage: uv run python -m tests.generate_golden wbrv
"""

import json
import sys
from pathlib import Path

from tests.adapters.old import observeer

WORTEL = Path(__file__).parent


def genereer(naam: str) -> None:
    vectors = json.loads((WORTEL / "vectors" / f"{naam}.json").read_text())
    golden = {v["id"]: observeer(v) for v in vectors}
    pad = WORTEL / "golden" / f"{naam}.json"
    pad.parent.mkdir(exist_ok=True)
    pad.write_text(json.dumps(golden, indent=2, ensure_ascii=False) + "\n")
    print(f"{pad}: {len(golden)} entries")


if __name__ == "__main__":
    genereer(sys.argv[1])
```

- [ ] **Step 2: Confirm the working tree is unmodified before generating**

Run: `git status --short src/`
Expected: no output. **If any file under `src/` is modified, stop** — the goldens would record changed behaviour rather than the baseline.

- [ ] **Step 3: Generate**

Run: `uv run python -m tests.generate_golden wbrv`
Expected: `tests/golden/wbrv.json: 32 entries`

- [ ] **Step 4: Sanity-check three known values**

Run:
```bash
uv run python -c "
import json
g = json.load(open('tests/golden/wbrv.json'))
assert g['art15-2025-545k-boven-grens']['lid_1'] == 'False', g['art15-2025-545k-boven-grens']
assert g['art15-2026-545k-onder-grens']['lid_1'] == 'True', g['art15-2026-545k-onder-grens']
assert g['art15-geen-enkel-woningfeit']['lid_1'] == 'False', g['art15-geen-enkel-woningfeit']
print('version boundary and divergence baseline confirmed')
"
```
Expected: `version boundary and divergence baseline confirmed`

- [ ] **Step 5: Commit**

```bash
git add tests/generate_golden.py tests/golden/wbrv.json
git commit -m ":white_check_mark: Freeze WBRV golden results from pre-change code"
```

---

## Task 6: The characterization test and the divergence allowlist

**Files:**
- Create: `tests/divergences.py`, `tests/conftest.py`, `tests/test_characterization.py`

- [ ] **Step 1: Write the divergence allowlist**

Create `tests/divergences.py`:

```python
"""Authorised behaviour changes.

Key: (vector_id, observation). Value: (old, new, reason).

An entry here is a deliberate decision recorded in the spec. A golden mismatch
with no entry fails the suite, so behaviour cannot move silently.
"""

AFWIJKINGEN: dict[tuple[str, str], tuple[str, str, str]] = {}
```

- [ ] **Step 2: Write the conftest**

Create `tests/conftest.py`:

```python
import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--adapter",
        default="old",
        choices=["old", "new"],
        help="Which implementation to run the vectors through",
    )


@pytest.fixture(scope="session")
def adapter(request):
    naam = request.config.getoption("--adapter")
    if naam == "old":
        from tests.adapters.old import observeer
    else:
        from tests.adapters.new import observeer
    return observeer
```

- [ ] **Step 3: Write the failing test**

Create `tests/test_characterization.py`:

```python
import json
from pathlib import Path

import pytest

from tests.divergences import AFWIJKINGEN

WORTEL = Path(__file__).parent
SETS = ["wbrv"]


def _vectors():
    for naam in SETS:
        for vector in json.loads((WORTEL / "vectors" / f"{naam}.json").read_text()):
            yield naam, vector


@pytest.mark.parametrize(
    "set_naam,vector", list(_vectors()), ids=lambda v: v["id"] if isinstance(v, dict) else v
)
def test_vector_matches_golden(set_naam, vector, adapter, request):
    golden = json.loads((WORTEL / "golden" / f"{set_naam}.json").read_text())
    verwacht = golden[vector["id"]]
    gekregen = adapter(vector)

    for naam, verwachte_waarde in verwacht.items():
        sleutel = (vector["id"], naam)
        if sleutel in AFWIJKINGEN:
            oud, nieuw, reden = AFWIJKINGEN[sleutel]
            assert oud == verwachte_waarde, (
                f"divergence entry for {sleutel} claims old={oud!r} "
                f"but golden says {verwachte_waarde!r}"
            )
            if request.config.getoption("--adapter") == "new":
                assert gekregen[naam] == nieuw, f"{sleutel}: {reden}"
                continue
        assert gekregen[naam] == verwachte_waarde, f"{sleutel} moved without a divergence entry"
```

- [ ] **Step 4: Run it against the old adapter**

Run: `uv run pytest tests/test_characterization.py -q`
Expected: PASS — `32 passed`

- [ ] **Step 5: Prove the guard bites**

Run:
```bash
uv run python -c "
import json, pathlib
p = pathlib.Path('tests/golden/wbrv.json')
g = json.loads(p.read_text())
g['art1-alleen-overdrachtsbelasting']['belasting_van_rechtsverkeer'] = 'False'
p.write_text(json.dumps(g, indent=2) + '\n')
"
uv run pytest tests/test_characterization.py -q 2>&1 | tail -3
git checkout tests/golden/wbrv.json
```
Expected: a failure naming `art1-alleen-overdrachtsbelasting`, then the file is restored.

- [ ] **Step 6: Commit**

```bash
git add tests/conftest.py tests/divergences.py tests/test_characterization.py
git commit -m ":white_check_mark: Add characterization harness with divergence allowlist"
```

---

## Task 7: AWB and ATW vectors and goldens

Goldens for **all ten** articles are frozen now, before any production file changes, even though `awb` and `atw` convert in Plan 2. Generating them later would capture a baseline already touched by this plan's versioning changes.

**Files:**
- Create: `tests/vectors/awb.json`, `tests/vectors/atw.json`, `tests/golden/awb.json`, `tests/golden/atw.json`
- Modify: `tests/adapters/old.py`, `tests/test_characterization.py:8`

- [ ] **Step 1: Write the AWB vectors**

Create `tests/vectors/awb.json`:

```json
[
  {
    "id": "awb68-bekendmaking-werkdag",
    "artikel": "awb.Artikel6_8",
    "observaties": ["datum_aanvang_indieningstermijn"],
    "feiten": {"datum_bekendmaking_besluit": "2023-11-03"}
  },
  {
    "id": "awb68-bekendmaking-zaterdag",
    "artikel": "awb.Artikel6_8",
    "observaties": ["datum_aanvang_indieningstermijn"],
    "feiten": {"datum_bekendmaking_besluit": "2023-11-04"}
  },
  {
    "id": "awb67-indieningstermijn-zes-weken",
    "artikel": "awb.Artikel6_7",
    "observaties": ["indieningstermijn", "datum_einde_indieningstermijn"],
    "feiten": {"datum_aanvang_indieningstermijn": "2023-11-04"}
  },
  {
    "id": "awb67-jaargrens",
    "artikel": "awb.Artikel6_7",
    "observaties": ["indieningstermijn", "datum_einde_indieningstermijn"],
    "feiten": {"datum_aanvang_indieningstermijn": "2025-12-01"}
  },
  {
    "id": "awb710-zonder-commissie",
    "artikel": "awb.Artikel7_10",
    "observaties": ["termijn_beslissing_bezwaar", "datum_einde_beslistermijn"],
    "feiten": {"datum_einde_bezwaartermijn": "2025-11-15", "commissie_ingesteld": false}
  },
  {
    "id": "awb710-met-commissie",
    "artikel": "awb.Artikel7_10",
    "observaties": ["termijn_beslissing_bezwaar", "datum_einde_beslistermijn"],
    "feiten": {"datum_einde_bezwaartermijn": "2025-11-15", "commissie_ingesteld": true}
  },
  {
    "id": "awb710-verzuim-niet-hersteld",
    "artikel": "awb.Artikel7_10",
    "observaties": ["datum_einde_beslistermijn"],
    "feiten": {"datum_einde_bezwaartermijn": "2021-08-13", "commissie_ingesteld": false, "datum_verzoek_verzuim": "2021-09-01", "termijn_verzoek_verzuim_dagen": 14}
  },
  {
    "id": "awb710-verzuim-hersteld-binnen-termijn",
    "artikel": "awb.Artikel7_10",
    "observaties": ["datum_einde_beslistermijn"],
    "feiten": {"datum_einde_bezwaartermijn": "2021-08-13", "commissie_ingesteld": false, "datum_verzoek_verzuim": "2021-09-01", "termijn_verzoek_verzuim_dagen": 14, "datum_herstel_verzuim": "2021-09-07"}
  },
  {
    "id": "awb710-verzoek-verzuim-voor-einde-bezwaartermijn",
    "artikel": "awb.Artikel7_10",
    "observaties": ["datum_einde_beslistermijn"],
    "feiten": {"datum_einde_bezwaartermijn": "2021-08-13", "commissie_ingesteld": false, "datum_verzoek_verzuim": "2021-08-01", "termijn_verzoek_verzuim_dagen": 14}
  },
  {
    "id": "awb710-verdagen-binnen-zes-weken",
    "artikel": "awb.Artikel7_10",
    "observaties": ["datum_einde_beslistermijn"],
    "feiten": {"datum_einde_bezwaartermijn": "2025-11-15", "commissie_ingesteld": false, "termijn_verdagen_dagen": 14}
  },
  {
    "id": "awb710-verdagen-boven-zes-weken-wordt-gekapt",
    "artikel": "awb.Artikel7_10",
    "observaties": ["datum_einde_beslistermijn"],
    "feiten": {"datum_einde_bezwaartermijn": "2025-11-15", "commissie_ingesteld": false, "termijn_verdagen_dagen": 70}
  },
  {
    "id": "awb710-lid4-instemming-alle-belanghebbenden",
    "artikel": "awb.Artikel7_10",
    "observaties": ["datum_einde_beslistermijn"],
    "feiten": {"datum_einde_bezwaartermijn": "2025-11-15", "commissie_ingesteld": false, "termijn_verder_uitstel_dagen": 21, "instemming_alle_belanghebbenden": true}
  },
  {
    "id": "awb710-lid4-expliciet-geen-instemming",
    "artikel": "awb.Artikel7_10",
    "observaties": ["datum_einde_beslistermijn"],
    "feiten": {"datum_einde_bezwaartermijn": "2025-11-15", "commissie_ingesteld": false, "termijn_verder_uitstel_dagen": 21, "instemming_alle_belanghebbenden": false, "instemming_indiener": false, "andere_belanghebbende_niet_geschaad": false, "naleving_wettelijke_procedurevoorschriften": false}
  },
  {
    "id": "awb710-lid4-instemming-onbekend-issue-17",
    "artikel": "awb.Artikel7_10",
    "observaties": ["datum_einde_beslistermijn"],
    "feiten": {"datum_einde_bezwaartermijn": "2025-11-15", "commissie_ingesteld": false, "termijn_verder_uitstel_dagen": 21}
  }
]
```

`awb710-lid4-instemming-onbekend-issue-17` records the quarantined defect from issue #17: uitstel granted with no consent recorded.

- [ ] **Step 2: Write the ATW vectors**

The ATW cross-product is generated rather than hand-written, then frozen. Create `tests/vectors/atw_generate.py`:

```python
"""Generate the ATW cross-product once. Output is frozen in atw.json.

Covers: carry-in zero and non-zero, negative term (art. 1 lid 2 reset), the
art. 2 three-day threshold, every eenheid either side of each art. 4 onderdeel a
boundary, weekends, fixed and computed holidays with their adjacent days, and
year boundaries.

Usage: uv run python -m tests.vectors.atw_generate > tests/vectors/atw.json
"""

import json
from datetime import date

# Saturdays, Sundays, fixed and computed holidays, and their adjacent days.
DATA = [
    "2025-12-26", "2025-12-27", "2025-12-28", "2025-12-29",  # 2e kerstdag, za, zo, ma
    "2025-12-31", "2026-01-01", "2026-01-02",                # jaargrens + nieuwjaar
    "2026-04-03", "2026-04-06", "2026-04-07",                # Goede Vrijdag, 2e Paasdag
    "2026-04-27", "2026-04-28",                              # Koningsdag
    "2026-05-05", "2026-05-06",                              # 5 mei
    "2026-05-14", "2026-05-25",                              # Hemelvaart, 2e Pinksterdag
    "2026-06-13", "2026-06-14", "2026-06-15",                # za, zo, ma
]

EENHEDEN = {
    "uur": [1, 24],
    "dag": [1, 3, 90, 91],
    "week": [7, 84, 85],
    "maand": [30, 90, 92],
    "jaar": [364, 365, 366],
}


def vectors():
    n = 0
    for datum in DATA:
        for eenheid, dagen_lijst in EENHEDEN.items():
            for dagen in dagen_lijst:
                for verlenging in (0, 2):
                    n += 1
                    yield {
                        "id": f"atw-{datum}-{eenheid}-{dagen}d-carry{verlenging}",
                        "artikel": "atw.verlenging",
                        "observaties": ["datum_einde_verlengde_termijn"],
                        "feiten": {
                            "datum_einde_wettelijke_termijn": datum,
                            "wettelijke_termijn_dagen": dagen,
                            "wettelijke_termijn_eenheid": eenheid,
                            "verlenging_termijn_dagen": verlenging,
                        },
                    }
    # art. 1 lid 2: negative term resets the extension
    for datum in ("2025-12-27", "2026-04-06"):
        yield {
            "id": f"atw-{datum}-negatieve-termijn",
            "artikel": "atw.verlenging",
            "observaties": ["datum_einde_verlengde_termijn"],
            "feiten": {
                "datum_einde_wettelijke_termijn": datum,
                "wettelijke_termijn_dagen": -5,
                "wettelijke_termijn_eenheid": "dag",
                "verlenging_termijn_dagen": 0,
            },
        }
    # the assertion taxlation-api already relies on
    yield {
        "id": "atw-route-beslistermijn-2025-12-29",
        "artikel": "atw.verlenging",
        "observaties": ["datum_einde_verlengde_termijn"],
        "feiten": {
            "datum_einde_wettelijke_termijn": "2025-12-27",
            "wettelijke_termijn_dagen": 42,
            "wettelijke_termijn_eenheid": "dag",
            "verlenging_termijn_dagen": 0,
        },
    }


if __name__ == "__main__":
    print(json.dumps(list(vectors()), indent=2))
```

Run: `uv run python -m tests.vectors.atw_generate > tests/vectors/atw.json`
Expected: `tests/vectors/atw.json` written, 573 vectors.

Verify: `uv run python -c "import json; print(len(json.load(open('tests/vectors/atw.json'))), 'vectors')"`
Expected: `573 vectors`

- [ ] **Step 3: Extend the old adapter**

Replace the **whole** of `tests/adapters/old.py` with:

```python
"""Vector -> today's flat-kwargs constructors.

Deleted together with the old implementation once Plan 2 finishes. Until then it
is what proves the new adapter produces identical legal outcomes.
"""

from datetime import date, timedelta

from taxlation.nl import atw, awb, wbrv

from tests.render import render

# Which class carries each observation, and whether it is a method today.
OBSERVATIES = {
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
    "awb.Artikel6_7": {
        "indieningstermijn": ("Artikel6_7", False),
        "datum_einde_indieningstermijn": ("Artikel6_7", False),
    },
    "awb.Artikel6_8": {"datum_aanvang_indieningstermijn": ("Artikel6_8", False)},
    "awb.Artikel7_10": {
        "termijn_beslissing_bezwaar": ("Artikel7_10", False),
        "datum_einde_beslistermijn": ("Artikel7_10", False),
    },
}

NIVEAUS = {
    "Artikel1": lambda: wbrv.Artikel1,
    "Artikel2": lambda: wbrv.Artikel2,
    "Artikel15": lambda: wbrv.Artikel15,
    "Artikel15Lid1": lambda: wbrv.Artikel15Lid1,
    "Artikel15Lid1OnderdeelP": lambda: wbrv.Artikel15Lid1OnderdeelP,
    "Artikel6_7": lambda: awb.Artikel6_7,
    "Artikel6_8": lambda: awb.Artikel6_8,
    "Artikel7_10": lambda: awb.Artikel7_10,
}

# Vector fact names ending in _dagen are timedeltas; _datum-like names are dates.
DAGEN_SUFFIX = "_dagen"


def _waarde(naam, ruw):
    if naam.endswith(DAGEN_SUFFIX):
        return timedelta(days=ruw)
    if isinstance(ruw, str) and len(ruw) == 10 and ruw[4] == "-":
        return date.fromisoformat(ruw)
    return ruw


def _kwargs(vector):
    return {
        naam.removesuffix(DAGEN_SUFFIX) if naam.endswith(DAGEN_SUFFIX) else naam: _waarde(naam, ruw)
        for naam, ruw in vector["feiten"].items()
    }


def _bouw(vector, niveau):
    kwargs = _kwargs(vector)
    if "datum_toepassing" in vector:
        kwargs["datum_toepassing"] = date.fromisoformat(vector["datum_toepassing"])
    return NIVEAUS[niveau]()(**kwargs)


def _atw_verlenging(vector):
    """Mirror of taxlation-api's services/nl/atw_verlenging.py."""
    f = _kwargs(vector)
    art_1 = atw.Artikel1(
        datum_einde_wettelijke_termijn=f["datum_einde_wettelijke_termijn"],
        wettelijke_termijn=f["wettelijke_termijn"],
        verlenging_termijn=f["verlenging_termijn"],
    )
    art_2 = atw.Artikel2(
        datum_einde_wettelijke_termijn=f["datum_einde_wettelijke_termijn"],
        wettelijke_termijn=f["wettelijke_termijn"],
        verlenging_termijn=art_1.verlenging_termijn,
    )
    art_4 = atw.Artikel4(
        datum_einde_wettelijke_termijn=f["datum_einde_wettelijke_termijn"],
        wettelijke_termijn=f["wettelijke_termijn"],
        wettelijke_termijn_eenheid=f["wettelijke_termijn_eenheid"],
        verlenging_termijn=art_2.verlenging_termijn,
    )
    return art_4.datum_einde_verlengde_termijn


def observeer(vector) -> dict:
    if vector["artikel"] == "atw.verlenging":
        return {"datum_einde_verlengde_termijn": render(lambda: _atw_verlenging(vector))}

    resultaat = {}
    for naam in vector["observaties"]:
        niveau, is_methode = OBSERVATIES[vector["artikel"]][naam]

        def waarnemen(niveau=niveau, naam=naam, is_methode=is_methode):
            obj = _bouw(vector, niveau)
            attr = getattr(obj, naam)
            return attr() if is_methode else attr

        resultaat[naam] = render(waarnemen)
    return resultaat
```

- [ ] **Step 4: Confirm the tree is still unmodified, then generate**

Run: `git status --short src/`
Expected: no output.

Run:
```bash
uv run python -m tests.generate_golden awb
uv run python -m tests.generate_golden atw
```
Expected: `tests/golden/awb.json: 14 entries` and `tests/golden/atw.json: 573 entries`

- [ ] **Step 5: Verify the taxlation-api assertion is reproduced**

Run:
```bash
uv run python -c "
import json
g = json.load(open('tests/golden/atw.json'))
got = g['atw-route-beslistermijn-2025-12-29']['datum_einde_verlengde_termijn']
assert got == '2025-12-29', got
print('atw chain reproduces the route assertion:', got)
"
```
Expected: `atw chain reproduces the route assertion: 2025-12-29`

This is the single most important check in the plan. It proves the harness models the `atw` chain the way the live service does, which is what Plan 2's delegation rewrite will be measured against.

- [ ] **Step 6: Quarantine the two known legal defects**

The goldens record what the code *does*. These tests record what the law *says*, so parity with a known-wrong answer stays visible instead of being silently certified. `strict=True` means an unexpected pass fails the suite, which is what forces attention when either issue is fixed.

Create `tests/test_gequarantainede_gebreken.py`:

```python
"""Bekende juridische gebreken, bewust niet gefixt in deze herstructurering.

Elke test noemt de juridisch juiste uitkomst en is xfail zolang de code die niet
geeft. strict=True zorgt dat een onverwachte pass de suite laat falen, zodat het
opvalt zodra een issue wordt opgelost.
"""

from datetime import date, timedelta

import pytest

from taxlation.nl import atw, awb


@pytest.mark.xfail(
    strict=True,
    reason="issue #17: zonder vastgelegde instemming wordt verder uitstel toch verleend",
)
def test_awb710_lid4_zonder_instemming_geen_verder_uitstel():
    # Artikel 7:10 lid 4 staat verder uitstel alleen toe bij instemming (onderdeel a
    # of b) of wettelijke procedurevoorschriften (onderdeel c). Is niets vastgelegd,
    # dan hoort er geen uitstel te zijn en eindigt de beslistermijn na zes weken.
    artikel = awb.Artikel7_10(
        datum_einde_bezwaartermijn=date(2025, 11, 15),
        commissie_ingesteld=False,
        termijn_verder_uitstel=timedelta(days=21),
    )
    assert artikel.datum_einde_beslistermijn == date(2025, 11, 15) + timedelta(weeks=6)


@pytest.mark.xfail(
    strict=True,
    reason="issue #16: artikel 4 onderdeel b is niet geimplementeerd, het feit kan niet worden opgegeven",
)
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


@pytest.mark.xfail(
    strict=True,
    reason="issue #16: artikel 4 onderdeel c is niet geimplementeerd, het feit kan niet worden opgegeven",
)
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

Run: `uv run pytest tests/test_gequarantainede_gebreken.py -q`
Expected: `3 xfailed`

- [ ] **Step 7: Register the new sets and run everything**

In `tests/test_characterization.py`, change line 8:

```python
SETS = ["wbrv", "awb", "atw"]
```

Run: `uv run pytest tests/test_characterization.py -q`
Expected: PASS — `619 passed`

- [ ] **Step 8: Commit**

```bash
git add tests/vectors/ tests/golden/ tests/adapters/old.py tests/test_characterization.py tests/test_gequarantainede_gebreken.py
git commit -m ":white_check_mark: Freeze AWB and ATW vectors, goldens and quarantined defects"
```

---

## Task 8: The Casus and vereist()

**Files:**
- Create: `src/taxlation/nl/feiten/__init__.py`, `src/taxlation/nl/feiten/casus.py`, `tests/test_vereist.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_vereist.py`:

```python
from dataclasses import dataclass

import pytest

from taxlation.nl.feiten import Casus


@dataclass
class _Nep:
    a: bool | None = None
    b: bool | None = None
    getal: int | None = None


def _casus(**kw):
    c = Casus()
    c.verkrijger = _Nep(**kw)
    return c


def test_alle_feiten_aanwezig_gaat_door():
    _casus(a=True, getal=3).vereist(("verkrijger.a", "verkrijger.getal"), "Test")


def test_ontbrekend_feit_noemt_de_naam():
    with pytest.raises(ValueError) as exc:
        _casus(a=True).vereist(("verkrijger.a", "verkrijger.getal"), "Test")
    assert "verkrijger.getal" in str(exc.value)
    assert "Test" in str(exc.value)


def test_alle_ontbrekende_feiten_worden_tegelijk_genoemd():
    with pytest.raises(ValueError) as exc:
        _casus().vereist(("verkrijger.a", "verkrijger.getal"), "Test")
    boodschap = str(exc.value)
    assert "verkrijger.a" in boodschap and "verkrijger.getal" in boodschap


def test_ontbrekende_entiteit_telt_als_ontbrekend_feit():
    with pytest.raises(ValueError) as exc:
        Casus().vereist(("verkrijger.a",), "Test")
    assert "verkrijger.a" in str(exc.value)


def test_disjunctie_een_waar_is_bepaald():
    _casus(a=True).vereist((("verkrijger.a", "verkrijger.b"),), "Test")


def test_disjunctie_alle_bekend_is_bepaald():
    _casus(a=False, b=False).vereist((("verkrijger.a", "verkrijger.b"),), "Test")


def test_disjunctie_deels_onbekend_en_geen_waar_is_onbepaald():
    with pytest.raises(ValueError) as exc:
        _casus(a=False).vereist((("verkrijger.a", "verkrijger.b"),), "Test")
    assert "verkrijger.a of verkrijger.b" in str(exc.value)


def test_wettelijke_standaardwaarde_telt_niet_als_ontbrekend():
    c = Casus()
    c.verkrijger = _Nep(getal=0)
    c.vereist(("verkrijger.getal",), "Test")
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run pytest tests/test_vereist.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'taxlation.nl.feiten'`

- [ ] **Step 3: Write the implementation**

Create `src/taxlation/nl/feiten/casus.py`:

```python
# import dataclasses module
from dataclasses import dataclass

# import datetime module
from datetime import date


@dataclass
class Casus:
  """
  De feiten van een casus, gegroepeerd per werkelijk ding waarover ze gaan.

  Elk artikel leest wat het nodig heeft en niets meer. Alle velden zijn optioneel,
  omdat geen enkel artikel ze allemaal leest.
  """

  datum_toepassing: date = None  # de datum waarnaar de casus wordt beoordeeld

  # entiteiten worden per wet toegevoegd; wbrv opent de rij
  verkrijger: object = None
  zaak: object = None
  hoofdverblijf: object = None
  verkrijging: object = None
  belastingmiddel: object = None

  def _lees(self, pad: str):
    """
    Leest een puntpad zoals "verkrijger.leeftijd".

    Een ontbrekende entiteit telt als een ontbrekend feit.
    """
    waarde = self
    for deel in pad.split("."):
      if waarde is None:
        return None
      waarde = getattr(waarde, deel, None)
    return waarde

  def vereist(self, namen, door: str) -> None:
    """
    Controleert of de feiten die een bepaling nodig heeft bepaald zijn.

    Een los pad moet bekend zijn. Een tuple is een disjunctie en is bepaald zodra
    een van de onderdelen True is, of zodra alle onderdelen bekend zijn.

    Werpt:
      ValueError: met alle ontbrekende feiten tegelijk.
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
# make the fact layer directly available
from .casus import Casus

__all__ = ["Casus"]
```

- [ ] **Step 4: Run it to verify it passes**

Run: `uv run pytest tests/test_vereist.py -q`
Expected: PASS — `8 passed`

- [ ] **Step 5: Confirm the oracle is untouched**

Run: `uv run pytest tests/test_characterization.py -q`
Expected: PASS — `619 passed`

- [ ] **Step 6: Commit**

```bash
git add src/taxlation/nl/feiten/ tests/test_vereist.py
git commit -m ":sparkles: Add Casus with disjunction-aware vereist()"
```

---

## Task 9: WBRV entities

**Files:**
- Create: `src/taxlation/nl/feiten/verkrijger.py`, `onroerende_zaak.py`, `hoofdverblijf.py`, `verkrijging.py`, `belastingmiddel.py`
- Modify: `src/taxlation/nl/feiten/__init__.py`, `src/taxlation/nl/feiten/casus.py`
- Create: `tests/test_entiteiten.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_entiteiten.py`:

```python
from taxlation.nl.feiten import (
    Belastingmiddel,
    Casus,
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


def test_waarde_aanhorigheden_heeft_wettelijke_standaardwaarde_nul():
    # Geen aanhorigheden verkrijgen betekent een waarde van nul. Dat is een feit
    # dat de wet zelf geeft, geen ontbrekend gegeven.
    assert OnroerendeZaak().waarde_aanhorigheden == 0


def test_casus_heeft_een_slot_per_entiteit():
    c = Casus(
        verkrijger=Verkrijger(leeftijd=34),
        zaak=OnroerendeZaak(woning=True),
        hoofdverblijf=Hoofdverblijf(verklaring_hoofdverblijf=True),
        verkrijging=Verkrijging(verkrijging=True),
        belastingmiddel=Belastingmiddel(overdrachtsbelasting=True),
    )
    assert c._lees("verkrijger.leeftijd") == 34
    assert c._lees("zaak.woning") is True
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run pytest tests/test_entiteiten.py -q`
Expected: FAIL — `ImportError: cannot import name 'Belastingmiddel'`

- [ ] **Step 3: Write the entities**

Create `src/taxlation/nl/feiten/verkrijger.py`:

```python
# import dataclasses module
from dataclasses import dataclass


@dataclass(kw_only=True)
class Verkrijger:
  """
  Feiten over de persoon die verkrijgt.
  """
  natuurlijk_persoon: bool = None  # of de verkrijger een natuurlijk persoon is
  leeftijd: int = None  # leeftijd van de verkrijger
  vrijstelling_eerder_toegepast: bool = None  # of de verkrijger de vrijstelling eerder heeft toegepast
  verklaring_vrijstelling: bool = None  # of de verkrijger heeft verklaard de vrijstelling niet eerder te hebben toegepast
```

Create `src/taxlation/nl/feiten/onroerende_zaak.py`:

```python
# import dataclasses module
from dataclasses import dataclass


@dataclass(kw_only=True)
class OnroerendeZaak:
  """
  Feiten over de onroerende zaak die wordt verkregen.
  """
  woning: bool = None  # of een woning wordt verkregen
  rechten_woning_onderworpen: bool = None  # of rechten waaraan een woning is onderworpen worden verkregen
  rechten_lidmaatschap_woning: bool = None  # of lidmaatschapsrechten met betrekking tot een woning worden verkregen
  aanhorigheid: bool = None  # of gelijktijdig een tot de woning behorende aanhorigheid wordt verkregen
  in_nederland_gelegen: bool = None  # of de onroerende zaak in Nederland is gelegen
  onroerende_zaken: bool = None  # of sprake is van onroerende zaken
  rechten_onroerende_zaken_onderworpen: bool = None  # of sprake is van een recht waaraan een onroerende zaak is onderworpen
  waarde_woning: int = None  # de waarde van de woning
  waarde_aanhorigheden: int = 0  # de waarde van de aanhorigheden; geen aanhorigheden betekent nul, wat de wet zelf geeft
```

Create `src/taxlation/nl/feiten/hoofdverblijf.py`:

```python
# import dataclasses module
from dataclasses import dataclass


@dataclass(kw_only=True)
class Hoofdverblijf:
  """
  Feiten over het gebruik van de woning als hoofdverblijf.
  """
  woning_tijdelijk_hoofdverblijf: bool = None  # of de woning slechts tijdelijk als hoofdverblijf wordt gebruikt
  verklaring_hoofdverblijf: bool = None  # of de verkrijger heeft verklaard de woning anders dan tijdelijk als hoofdverblijf te gaan gebruiken
```

Create `src/taxlation/nl/feiten/verkrijging.py`:

```python
# import dataclasses module
from dataclasses import dataclass


@dataclass(kw_only=True)
class Verkrijging:
  """
  Feiten over de verkrijging zelf.
  """
  verkrijging: bool = None  # of sprake is van een verkrijging
```

Create `src/taxlation/nl/feiten/belastingmiddel.py`:

```python
# import dataclasses module
from dataclasses import dataclass


@dataclass(kw_only=True)
class Belastingmiddel:
  """
  Feiten over welk belastingmiddel aan de orde is.
  """
  overdrachtsbelasting: bool = None  # of overdrachtsbelasting als bedoeld in hoofdstuk II WBRV aan de orde is
  assurantiebelasting: bool = None  # of assurantiebelasting als bedoeld in hoofdstuk III WBRV aan de orde is
```

Replace the entity slots in `src/taxlation/nl/feiten/casus.py` with typed ones. Change the imports at the top:

```python
# import dataclasses module
from dataclasses import dataclass

# import datetime module
from datetime import date

# import entities
from .belastingmiddel import Belastingmiddel
from .hoofdverblijf import Hoofdverblijf
from .onroerende_zaak import OnroerendeZaak
from .verkrijger import Verkrijger
from .verkrijging import Verkrijging
```

and the slot block:

```python
  # entiteiten worden per wet toegevoegd; wbrv opent de rij
  verkrijger: Verkrijger = None
  zaak: OnroerendeZaak = None
  hoofdverblijf: Hoofdverblijf = None
  verkrijging: Verkrijging = None
  belastingmiddel: Belastingmiddel = None
```

Replace `src/taxlation/nl/feiten/__init__.py`:

```python
# make the fact layer directly available
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

Run: `uv run pytest tests/test_entiteiten.py tests/test_vereist.py -q`
Expected: PASS — `11 passed`

- [ ] **Step 5: Commit**

```bash
git add src/taxlation/nl/feiten/ tests/test_entiteiten.py
git commit -m ":sparkles: Add WBRV fact entities"
```

---

## Task 10: VersieArtikel — casus fallback (D12)

**Files:**
- Modify: `src/taxlation/nl/versioning.py`
- Create: `tests/test_versioning.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_versioning.py`:

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


@dataclass
class _V2026:
    casus: Casus

    @property
    def antwoord(self) -> str:
        return "2026"


ARTIKEL = VersieArtikel(
    name="Test", versions={date(2025, 1, 1): _V2025, date(2026, 1, 1): _V2026}
)


def test_expliciete_datum_kiest_de_versie():
    assert ARTIKEL(datum_toepassing=date(2025, 6, 1), casus=Casus()).antwoord == "2025"
    assert ARTIKEL(datum_toepassing=date(2026, 6, 1), casus=Casus()).antwoord == "2026"


def test_casus_datum_kiest_de_versie():
    assert ARTIKEL(casus=Casus(datum_toepassing=date(2025, 6, 1))).antwoord == "2025"
    assert ARTIKEL(casus=Casus(datum_toepassing=date(2026, 6, 1))).antwoord == "2026"


def test_expliciete_datum_gaat_voor_op_de_casus():
    casus = Casus(datum_toepassing=date(2026, 6, 1))
    assert ARTIKEL(datum_toepassing=date(2025, 6, 1), casus=casus).antwoord == "2025"


def test_voor_de_eerste_versie_werpt():
    with pytest.raises(ValueError, match="No version from Test"):
        ARTIKEL(casus=Casus(datum_toepassing=date(2024, 1, 1)))
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run pytest tests/test_versioning.py -q`
Expected: FAIL — `TypeError: __call__() got an unexpected keyword argument 'casus'`

- [ ] **Step 3: Write the implementation**

Replace `src/taxlation/nl/versioning.py`:

```python
from taxlation.core.versioning import VersionedClass


class VersieArtikel(VersionedClass):
  """Selecteert de juiste versie van een artikelklasse."""

  def __call__(self, *, datum_toepassing=None, casus=None, **kwargs):
    """
    Kiest de versie op de peildatum en bouwt de klasse.

    De peildatum komt uit datum_toepassing, of anders uit de casus. Zo staat de
    versie op één plek, ook wanneer een artikel een ander artikel bevraagt: dat
    geeft dezelfde casus door en krijgt dus dezelfde versie.
    """
    peildatum = datum_toepassing
    if peildatum is None and casus is not None:
      peildatum = casus.datum_toepassing

    if casus is not None:
      kwargs["casus"] = casus

    return super().__call__(reference_date=peildatum, **kwargs)
```

- [ ] **Step 4: Run it to verify it passes**

Run: `uv run pytest tests/test_versioning.py -q`
Expected: PASS — `4 passed`

- [ ] **Step 5: Confirm the oracle is untouched**

Run: `uv run pytest tests/test_characterization.py -q`
Expected: PASS — `619 passed`. The old articles pass no `casus`, so nothing changes for them.

- [ ] **Step 6: Commit**

```bash
git add src/taxlation/nl/versioning.py tests/test_versioning.py
git commit -m ":sparkles: VersieArtikel takes the peildatum from the casus"
```

---

## Task 11: VersieArtikel — nested proxy (D13)

**Files:**
- Modify: `src/taxlation/nl/versioning.py`
- Modify: `tests/test_versioning.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_versioning.py`:

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


def test_klasse_die_pas_later_bestaat_werpt_voor_haar_invoering():
    assert GENEST.Lid3(casus=Casus(datum_toepassing=date(2026, 6, 1))).antwoord == "lid3-2026"
    with pytest.raises(ValueError, match="No version from Genest.Lid3"):
        GENEST.Lid3(casus=Casus(datum_toepassing=date(2025, 6, 1)))


def test_onbekend_attribuut_werpt_attributeerror():
    with pytest.raises(AttributeError):
        GENEST.Lid9
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run pytest tests/test_versioning.py -q`
Expected: FAIL — `AttributeError: 'VersieArtikel' object has no attribute 'Lid1'`

- [ ] **Step 3: Write the implementation**

Append to the `VersieArtikel` class in `src/taxlation/nl/versioning.py`:

```python
  def __getattr__(self, naam):
    """
    Leidt de versiemap van een genest niveau af uit die van het artikel.

    Welke geneste klasse geldt, hangt af van de peildatum, en die is pas bekend
    bij aanroep. Daarom levert dit opnieuw een VersieArtikel op in plaats van een
    klasse. Versies die het niveau niet kennen worden overgeslagen, zodat een lid
    dat pas later is ingevoerd vanzelf een map krijgt die op dat moment begint.
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

Run: `uv run pytest tests/test_versioning.py -q`
Expected: PASS — `7 passed`

- [ ] **Step 5: Confirm the oracle is untouched**

Run: `uv run pytest tests/test_characterization.py -q`
Expected: PASS — `619 passed`

- [ ] **Step 6: Commit**

```bash
git add src/taxlation/nl/versioning.py tests/test_versioning.py
git commit -m ":sparkles: Derive nested version maps from the article's single map"
```

---

## Task 12: Convert wbrv article 1

**Files:**
- Modify: `src/taxlation/nl/wbrv/article_1/v2006_01_01/translation.py`, `src/taxlation/nl/wbrv/article_1/example.py`
- Create: `tests/adapters/new.py`

- [ ] **Step 1: Write the new adapter**

Create `tests/adapters/new.py`:

```python
"""Vector -> Casus.

Reads the same vectors as the old adapter. Fact names in a vector are domain
terms, so this is where they are routed onto entities; getting that routing wrong
is exactly what the golden comparison catches.
"""

from datetime import date

from taxlation.nl import wbrv
from taxlation.nl.feiten import (
    Belastingmiddel,
    Casus,
    Hoofdverblijf,
    OnroerendeZaak,
    Verkrijger,
    Verkrijging,
)

from tests.render import render

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

OBSERVATIES = {
    "wbrv.Artikel1": {"belasting_van_rechtsverkeer": ()},
    "wbrv.Artikel2": {"overdrachtsbelasting": (), "lid_1": ()},
    "wbrv.Artikel15": {
        "lid_1": (),
        "onderdeel_p": ("Lid1",),
        "startersvrijstelling": ("Lid1", "OnderdeelP"),
    },
}

ARTIKELEN = {
    "wbrv.Artikel1": lambda: wbrv.Artikel1,
    "wbrv.Artikel2": lambda: wbrv.Artikel2,
    "wbrv.Artikel15": lambda: wbrv.Artikel15,
}


def _casus(vector) -> Casus:
    feiten = vector["feiten"]
    casus = Casus()
    if "datum_toepassing" in vector:
        casus.datum_toepassing = date.fromisoformat(vector["datum_toepassing"])
    for slot, (klasse, velden) in ENTITEITEN.items():
        gevuld = {k: v for k, v in feiten.items() if k in velden}
        if gevuld:
            setattr(casus, slot, klasse(**gevuld))
    return casus


def observeer(vector) -> dict:
    resultaat = {}
    for naam in vector["observaties"]:
        pad = OBSERVATIES[vector["artikel"]][naam]

        def waarnemen(pad=pad, naam=naam):
            doel = ARTIKELEN[vector["artikel"]]()
            for niveau in pad:
                doel = getattr(doel, niveau)
            return getattr(doel(casus=_casus(vector)), naam)

        resultaat[naam] = render(waarnemen)
    return resultaat
```

- [ ] **Step 2: Run the new adapter to verify article 1 fails**

Run: `uv run pytest tests/test_characterization.py --adapter new -q -k "art1-"`
Expected: FAIL — the old `Artikel1` rejects `casus` as a keyword argument, so every `art1-*` vector mismatches.

- [ ] **Step 3: Convert the article**

Replace `src/taxlation/nl/wbrv/article_1/v2006_01_01/translation.py`:

```python
# import dataclasses module
from dataclasses import dataclass

# import casus
from taxlation.nl.feiten import Casus


@dataclass
class Artikel1:
  """
  Dataclass voor artikel 1, WBRV
  """
  casus: Casus
  VEREIST = (
    "belastingmiddel.overdrachtsbelasting",
    "belastingmiddel.assurantiebelasting",
  )

  @property
  def belasting_van_rechtsverkeer(self) -> bool:
    """
    Bepaalt of sprake is van een belasting van rechtsverkeer.

    Sprake is van een belasting van rechtsverkeer indien de overdrachtsbelasting
    of de assurantiebelasting van toepassing is.

    Geeft terug:
      bool
    """
    self.casus.vereist(self.VEREIST, "Artikel1")
    belastingmiddel = self.casus.belastingmiddel
    return bool(belastingmiddel.overdrachtsbelasting or belastingmiddel.assurantiebelasting)
```

Replace `src/taxlation/nl/wbrv/article_1/example.py`:

```python
# import package
from taxlation.nl import wbrv
from taxlation.nl.feiten import Belastingmiddel, Casus

casus = Casus(
    belastingmiddel=Belastingmiddel(overdrachtsbelasting=True, assurantiebelasting=False),
)

art_1_voorbeeld = wbrv.Artikel1(casus=casus)

print("Belasting van rechtsverkeer:", art_1_voorbeeld.belasting_van_rechtsverkeer)
```

- [ ] **Step 4: Run the new adapter to verify article 1 passes**

Run: `uv run pytest tests/test_characterization.py --adapter new -q -k "art1-"`
Expected: PASS — `4 passed`

Run: `uv run python src/taxlation/nl/wbrv/article_1/example.py`
Expected: `Belasting van rechtsverkeer: True`

- [ ] **Step 5: Commit**

```bash
git add src/taxlation/nl/wbrv/article_1/ tests/adapters/new.py
git commit -m ":recycle: Convert wbrv artikel 1 to Casus"
```

---

## Task 13: Convert wbrv article 2

**Files:**
- Modify: `src/taxlation/nl/wbrv/article_2/v2025_01_01/translation.py`, `src/taxlation/nl/wbrv/article_2/example.py`

- [ ] **Step 1: Run the new adapter to verify article 2 fails**

Run: `uv run pytest tests/test_characterization.py --adapter new -q -k "art2-"`
Expected: FAIL — 5 failures, `Artikel2` does not accept `casus`.

- [ ] **Step 2: Convert the article**

Replace `src/taxlation/nl/wbrv/article_2/v2025_01_01/translation.py`:

```python
# import dataclasses module
from dataclasses import dataclass

# import casus
from taxlation.nl.feiten import Casus


@dataclass
class Artikel2:
  """
  Dataclass voor artikel 2 WBRV
  """
  casus: Casus

  @dataclass
  class Lid1:
    """
    Dataclass voor artikel 2, lid 1 WBRV
    """
    casus: Casus
    VEREIST = (
      "verkrijging.verkrijging",
      "zaak.in_nederland_gelegen",
      "zaak.onroerende_zaken",
      "zaak.rechten_onroerende_zaken_onderworpen",
    )

    @property
    def belastbaar_feit(self) -> bool:
      """
      Bepaalt of sprake is van een belastbaar feit.

      Geeft terug:
        bool
      """
      self.casus.vereist(self.VEREIST, "Artikel2.Lid1")
      verkrijging = self.casus.verkrijging
      zaak = self.casus.zaak
      return bool(
        verkrijging.verkrijging
        and zaak.in_nederland_gelegen
        and (zaak.onroerende_zaken or zaak.rechten_onroerende_zaken_onderworpen)
      )

  @property
  def lid_1(self) -> bool:
    """
    Bepaalt of sprake is van een belastbaar feit als bedoeld in lid 1.

    Geeft terug:
      bool
    """
    return Artikel2.Lid1(self.casus).belastbaar_feit

  @property
  def overdrachtsbelasting(self) -> bool:
    """
    Bepaalt of overdrachtsbelasting wordt geheven.

    Geeft terug:
      bool
    """
    return self.lid_1
```

Replace `src/taxlation/nl/wbrv/article_2/example.py`:

```python
# import package
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

art_2_voorbeeld = wbrv.Artikel2(casus=casus)

print("Belastbaar feit:", art_2_voorbeeld.overdrachtsbelasting)
```

- [ ] **Step 3: Run the new adapter to verify article 2 passes**

Run: `uv run pytest tests/test_characterization.py --adapter new -q -k "art2-"`
Expected: PASS — `5 passed`

Run: `uv run python src/taxlation/nl/wbrv/article_2/example.py`
Expected: `Belastbaar feit: True`

- [ ] **Step 4: Commit**

```bash
git add src/taxlation/nl/wbrv/article_2/
git commit -m ":recycle: Convert wbrv artikel 2 to nested Lid1 + Casus"
```

---

## Task 14: Convert wbrv article 15 v2025

**Files:**
- Modify: `src/taxlation/nl/wbrv/article_15/v2025_01_01/translation.py`, `v2025_01_01/__init__.py`

- [ ] **Step 1: Convert the version**

Replace `src/taxlation/nl/wbrv/article_15/v2025_01_01/translation.py`:

```python
# import dataclasses module
from dataclasses import dataclass

# import casus
from taxlation.nl.feiten import Casus

WAARDEGRENS = 525_000
LEEFTIJD_MINIMUM = 18
LEEFTIJD_MAXIMUM = 35  # exclusief: de verkrijger moet jonger dan 35 zijn


@dataclass
class Artikel15:
  """
  Dataclass voor artikel 15 WBRV
  """
  casus: Casus

  @dataclass
  class Lid1:
    """
    Dataclass voor artikel 15, lid 1 WBRV
    """
    casus: Casus

    @dataclass
    class OnderdeelP:
      """
      Dataclass voor artikel 15, lid 1, onderdeel p, WBRV
      """
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
        """
        Stelt vast of de startersvrijstelling van toepassing is.

        Geeft terug:
          bool
        """
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
        """Een woning, of rechten daarop. Een aanhorigheid deelt in de vrijstelling
        maar kan die niet zelfstandig doen ontstaan, en telt alleen mee in de waarde."""
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
      """
      Stelt vast of artikel 15, lid 1, onderdeel p, WBRV van toepassing is.

      Geeft terug:
        bool
      """
      return Artikel15.Lid1.OnderdeelP(self.casus).startersvrijstelling

  @property
  def lid_1(self) -> bool:
    """
    Bepaalt of de verkrijging is vrijgesteld.

    Geeft terug:
      bool
    """
    return Artikel15.Lid1(self.casus).onderdeel_p
```

Replace `src/taxlation/nl/wbrv/article_15/v2025_01_01/__init__.py`:

```python
from .translation import Artikel15

__all__ = ["Artikel15"]
```

- [ ] **Step 2: Verify v2025 vectors pass under the new adapter**

The article map still points both dates at old classes, so run the v2025 vectors directly:

Run:
```bash
uv run python -c "
from datetime import date
from taxlation.nl.feiten import Casus, Hoofdverblijf, OnroerendeZaak, Verkrijger
from taxlation.nl.wbrv.article_15.v2025_01_01.translation import Artikel15
c = Casus(
    verkrijger=Verkrijger(natuurlijk_persoon=True, leeftijd=34, vrijstelling_eerder_toegepast=False, verklaring_vrijstelling=True),
    zaak=OnroerendeZaak(woning=True, waarde_woning=540000, waarde_aanhorigheden=5000),
    hoofdverblijf=Hoofdverblijf(woning_tijdelijk_hoofdverblijf=False, verklaring_hoofdverblijf=True),
)
assert Artikel15(c).lid_1 is False
assert Artikel15.Lid1(c).onderdeel_p is False
assert Artikel15.Lid1.OnderdeelP(c).startersvrijstelling is False
c.zaak.waarde_woning = 510000
assert Artikel15(c).lid_1 is True
print('v2025 boundary and all three levels OK')
"
```
Expected: `v2025 boundary and all three levels OK`

- [ ] **Step 3: Commit**

```bash
git add src/taxlation/nl/wbrv/article_15/v2025_01_01/
git commit -m ":recycle: Convert wbrv artikel 15 v2025 to nested classes + Casus"
```

---

## Task 15: Convert wbrv article 15 v2026 and delete the nested directories

**Files:**
- Modify: `src/taxlation/nl/wbrv/article_15/v2026_01_01/translation.py`, `v2026_01_01/__init__.py`, `v2026_01_01/README.md`
- Delete: `src/taxlation/nl/wbrv/article_15/v2026_01_01/paragraph_1/` (6 files)

- [ ] **Step 1: Convert the version**

The two versions differ by one constant. Per D6 they are independent implementations, so this is a **copy**, not an import: `v2026_01_01/translation.py` must never import from `v2025_01_01/`. The duplication is the point — coupling them means a later amendment silently rewrites history.

```bash
cd src/taxlation/nl/wbrv/article_15
cp v2025_01_01/translation.py v2026_01_01/translation.py
sed -i '' 's/^WAARDEGRENS = 525_000$/WAARDEGRENS = 555_000/' v2026_01_01/translation.py
cd -
```

Verify exactly one line differs:

```bash
diff src/taxlation/nl/wbrv/article_15/v2025_01_01/translation.py \
     src/taxlation/nl/wbrv/article_15/v2026_01_01/translation.py
```
Expected:
```
7c7
< WAARDEGRENS = 525_000
---
> WAARDEGRENS = 555_000
```

Replace `src/taxlation/nl/wbrv/article_15/v2026_01_01/__init__.py`:

```python
from .translation import Artikel15

__all__ = ["Artikel15"]
```

- [ ] **Step 2: Merge the nested READMEs upward**

Replace `src/taxlation/nl/wbrv/article_15/v2026_01_01/README.md`:

```markdown
# wbrv - artikel 15

## Classes

### Artikel15

**Methods**
- _lid_1_: Stelt vast of artikel 15, lid 1, WBRV van toepassing is (bool).

### Artikel15.Lid1

**Methods**
- _onderdeel_p_: Stelt vast of artikel 15, lid 1, onderdeel p, WBRV van toepassing is (bool).

### Artikel15.Lid1.OnderdeelP

**Feiten** (gelezen uit de casus)
- _zaak.woning_: Of een woning wordt verkregen (bool).
- _zaak.rechten_woning_onderworpen_: Of rechten waaraan een woning is onderworpen worden verkregen (bool).
- _zaak.rechten_lidmaatschap_woning_: Of rechten van een lidmaatschap die betrekking hebben op een woning worden verkregen (bool).
- _zaak.aanhorigheid_: Of gelijktijdig een tot de woning behorende aanhorigheid wordt verkregen (bool).
- _verkrijger.natuurlijk_persoon_: Of de verkrijger een natuurlijk persoon is (bool).
- _verkrijger.leeftijd_: Leeftijd van de verkrijger (int).
- _verkrijger.vrijstelling_eerder_toegepast_: Of de verkrijger de vrijstelling eerder heeft toegepast (bool).
- _verkrijger.verklaring_vrijstelling_: Of de verkrijger voorafgaand aan de verkrijging heeft verklaard de vrijstelling niet eerder te hebben toegepast (bool).
- _hoofdverblijf.woning_tijdelijk_hoofdverblijf_: Of de verkrijger de woning slechts tijdelijk als hoofdverblijf gaat gebruiken (bool).
- _hoofdverblijf.verklaring_hoofdverblijf_: Of de verkrijger voorafgaand aan de verkrijging heeft verklaard de woning anders dan tijdelijk als hoofdverblijf te gaan gebruiken (bool).
- _zaak.waarde_woning_: De waarde van de woning (int).
- _zaak.waarde_aanhorigheden_: De waarde van de bij de woning behorende aanhorigheden (int, standaard 0).

**Methods**
- _startersvrijstelling_: Stelt vast of de startersvrijstelling van toepassing is (bool).
```

- [ ] **Step 3: Delete the nested directories**

```bash
git rm -r src/taxlation/nl/wbrv/article_15/v2026_01_01/paragraph_1
```
Expected: 6 files removed.

- [ ] **Step 4: Verify the 2026 waardegrens**

Run:
```bash
uv run python -c "
from taxlation.nl.feiten import Casus, Hoofdverblijf, OnroerendeZaak, Verkrijger
from taxlation.nl.wbrv.article_15.v2026_01_01.translation import Artikel15, WAARDEGRENS
assert WAARDEGRENS == 555_000
c = Casus(
    verkrijger=Verkrijger(natuurlijk_persoon=True, leeftijd=34, vrijstelling_eerder_toegepast=False, verklaring_vrijstelling=True),
    zaak=OnroerendeZaak(woning=True, waarde_woning=540000, waarde_aanhorigheden=5000),
    hoofdverblijf=Hoofdverblijf(woning_tijdelijk_hoofdverblijf=False, verklaring_hoofdverblijf=True),
)
assert Artikel15(c).lid_1 is True
c.zaak.waarde_woning = 555001
c.zaak.waarde_aanhorigheden = 0
assert Artikel15(c).lid_1 is False
print('v2026 waardegrens OK')
"
```
Expected: `v2026 waardegrens OK`

- [ ] **Step 5: Commit**

```bash
git add -A src/taxlation/nl/wbrv/article_15/v2026_01_01/
git commit -m ":recycle: Convert wbrv artikel 15 v2026 and remove the nested directories"
```

---

## Task 16: Wire up the article and law exports

**Files:**
- Modify: `src/taxlation/nl/wbrv/article_15/__init__.py`, `src/taxlation/nl/wbrv/__init__.py`, `src/taxlation/nl/wbrv/article_15/example.py`

- [ ] **Step 1: Declare the versions once**

Replace `src/taxlation/nl/wbrv/article_15/__init__.py`:

```python
# make correct version of article available
from datetime import date

from taxlation.nl.versioning import VersieArtikel

from .v2025_01_01.translation import Artikel15 as v2025_01_01
from .v2026_01_01.translation import Artikel15 as v2026_01_01

# Geneste niveaus worden hieruit afgeleid: wbrv.Artikel15.Lid1.OnderdeelP kiest
# dezelfde versie als wbrv.Artikel15. Er is dus maar één map per artikel.
Artikel15 = VersieArtikel(name="Artikel15", versions={
  date(2025, 1, 1): v2025_01_01,
  date(2026, 1, 1): v2026_01_01,
})

__all__ = ["Artikel15"]
```

- [ ] **Step 2: Reduce the law-level exports**

Replace `src/taxlation/nl/wbrv/__init__.py`:

```python
# make dataclasses directly available for wbrv
from .article_1 import Artikel1
from .article_2 import Artikel2
from .article_15 import Artikel15

__all__ = ["Artikel1", "Artikel2", "Artikel15"]
```

- [ ] **Step 3: Rewrite the example**

Replace `src/taxlation/nl/wbrv/article_15/example.py`:

```python
# import package
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

- [ ] **Step 4: Run the whole suite under the new adapter**

Run: `uv run pytest tests/test_characterization.py --adapter new -q -k "art1- or art2- or art15-"`
Expected: FAIL — exactly one failure, `art15-geen-enkel-woningfeit`, which now raises where the golden says `False`. Every other WBRV vector passes.

This is the sanctioned divergence from the spec. Task 17 records it.

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

## Task 17: Record the disjunctive-group divergence

**Files:**
- Modify: `tests/divergences.py`
- Create: `tests/test_divergentie_boodschappen.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_divergentie_boodschappen.py`:

```python
"""The exception TYPE and MESSAGE are asserted here rather than in the golden
harness, because render() deliberately collapses every exception to "raises".
"""

import pytest

from taxlation.nl import wbrv
from taxlation.nl.feiten import Casus, Hoofdverblijf, OnroerendeZaak, Verkrijger


def _casus_zonder_woningfeit() -> Casus:
    from datetime import date

    return Casus(
        datum_toepassing=date(2025, 6, 1),
        verkrijger=Verkrijger(
            natuurlijk_persoon=True,
            leeftijd=34,
            vrijstelling_eerder_toegepast=False,
            verklaring_vrijstelling=True,
        ),
        zaak=OnroerendeZaak(waarde_woning=400000, waarde_aanhorigheden=0),
        hoofdverblijf=Hoofdverblijf(
            woning_tijdelijk_hoofdverblijf=False,
            verklaring_hoofdverblijf=True,
        ),
    )


def test_geen_enkel_woningfeit_werpt_en_noemt_de_disjunctie():
    with pytest.raises(ValueError) as exc:
        wbrv.Artikel15(casus=_casus_zonder_woningfeit()).lid_1
    boodschap = str(exc.value)
    assert "Artikel15.Lid1.OnderdeelP" in boodschap
    assert "zaak.woning of zaak.rechten_woning_onderworpen of zaak.rechten_lidmaatschap_woning" in boodschap


def test_een_waar_woningfeit_is_genoeg():
    casus = _casus_zonder_woningfeit()
    casus.zaak.rechten_lidmaatschap_woning = True
    assert wbrv.Artikel15(casus=casus).lid_1 is True


def test_alle_woningfeiten_expliciet_onwaar_is_bepaald():
    casus = _casus_zonder_woningfeit()
    casus.zaak.woning = False
    casus.zaak.rechten_woning_onderworpen = False
    casus.zaak.rechten_lidmaatschap_woning = False
    assert wbrv.Artikel15(casus=casus).lid_1 is False
```

- [ ] **Step 2: Run it to verify it passes**

Run: `uv run pytest tests/test_divergentie_boodschappen.py -q`
Expected: PASS — `3 passed`. The behaviour already exists from Task 14; this pins the message and the determinacy rule.

- [ ] **Step 3: Record the divergence**

Replace the `AFWIJKINGEN` assignment in `tests/divergences.py`:

```python
AFWIJKINGEN: dict[tuple[str, str], tuple[str, str, str]] = {
    ("art15-geen-enkel-woningfeit", "lid_1"): (
        "False",
        "raises",
        "Spec D5: VEREIST wordt afgeleid uit de juridische voorwaarde, niet uit de oude "
        "dataclass-standaardwaarden. Zonder enig woningfeit is de disjunctie onbepaald. "
        "Voorheen leverde dat stil False op, wat 'niet vrijgesteld' en 'onvoldoende "
        "gegevens' op één hoop gooide.",
    ),
}
```

- [ ] **Step 4: Verify both adapters are green**

Run: `uv run pytest tests/test_characterization.py --adapter old -q`
Expected: PASS — `619 passed`. The divergence entry asserts the old value, so the old adapter still matches the golden.

Run: `uv run pytest tests/test_characterization.py --adapter new -q -k "art1- or art2- or art15-"`
Expected: PASS — `32 passed`

- [ ] **Step 5: Commit**

```bash
git add tests/divergences.py tests/test_divergentie_boodschappen.py
git commit -m ":white_check_mark: Record the disjunctive-group divergence for artikel 15"
```

---

## Task 18: Full suite and the D9 removed-members record

**Files:**
- Modify: none (verification and record only)

- [ ] **Step 1: Run everything**

Run: `uv run pytest -q`
Expected: PASS — all tests green, with `3 xfailed` from the quarantined defects. The characterization run defaults to `--adapter old`, which still passes because `awb` and `atw` are untouched by this plan and WBRV's single divergence is recorded.

- [ ] **Step 2: Run the new adapter over WBRV**

Run: `uv run pytest tests/test_characterization.py --adapter new -q -k "art1- or art2- or art15-"`
Expected: PASS — `32 passed`

- [ ] **Step 3: Run every example**

Run:
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

- [ ] **Step 4: Confirm atw and awb still import and behave**

Run: `uv run pytest tests/test_characterization.py -q -k "atw- or awb"`
Expected: PASS — `587 passed`

- [ ] **Step 5: Commit the D9 record**

```bash
git commit --allow-empty -m ":memo: D9 record: members removed by the wbrv conversion

Removed by nesting + delegation (spec D9, no customers so no shims):

  wbrv.Artikel15Lid1              -> wbrv.Artikel15.Lid1
  wbrv.Artikel15Lid1OnderdeelP    -> wbrv.Artikel15.Lid1.OnderdeelP
  Artikel15.onderdeel_p()         -> Artikel15.Lid1(casus).onderdeel_p
  Artikel15.startersvrijstelling() -> Artikel15.Lid1.OnderdeelP(casus).startersvrijstelling
  Artikel15Lid1.startersvrijstelling() -> as above
  Artikel2.lid_1()                -> Artikel2.lid_1 (property)

All flat-kwargs constructors are replaced by casus=.
Inherited members disappear because levels no longer inherit; each exposes only
its own provision. startersvrijstelling and lid_1 became properties.

No wbrv consumer exists: it is absent from taxlation-api's vendored copy and no
route imports it."
```

---

## Definition of done

- [ ] `uv run pytest -q` green
- [ ] `uv run pytest tests/test_characterization.py --adapter new -q -k "art1- or art2- or art15-"` green
- [ ] `tests/golden/*.json` unchanged since Task 7 — verify with `git log --oneline -- tests/golden/` showing only the two generation commits
- [ ] `tests/divergences.py` holds exactly one entry
- [ ] `uv run pytest tests/test_gequarantainede_gebreken.py -q` reports `3 xfailed`, never `xpassed`
- [ ] `src/taxlation/nl/wbrv/article_15/v2026_01_01/paragraph_1/` gone
- [ ] `awb` and `atw` untouched under `src/` — verify with `git diff --stat wbrv..HEAD -- src/taxlation/nl/atw src/taxlation/nl/awb` showing only the Task 7-era legislation swap already committed

## Handover to Plan 2

Plan 2 converts `awb` and `atw`. It inherits a complete oracle: 587 frozen `awb`/`atw` vectors with goldens generated from pre-change code, including `atw-route-beslistermijn-2025-12-29`, which is the assertion `taxlation-api`'s passing route test depends on.

Plan 2's first job is the `atw` delegation chain (D11), the highest-risk item in the whole spec. `tests/adapters/old.py::_atw_verlenging` is a deliberate mirror of `taxlation-api`'s service function and is the thing the delegated implementation must reproduce exactly.
