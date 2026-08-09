# Casus + article structure — design

**Date:** 2026-08-09
**Branch:** `wbrv-article`, branched from `wbrv`
**Status:** approved, ready for implementation planning

## Problem

Branch `wbrv` introduced a nested directory layout for one article version:

```
wbrv/article_15/v2026_01_01/
  translation.py                              Artikel15
  paragraph_1/translation.py                  Artikel15Lid1
  paragraph_1/subparagraph_p/translation.py   Artikel15Lid1OnderdeelP
```

Nine files where the sibling version `v2025_01_01` uses two, for classes that differ by a
single constant (`525_000` vs `555_000`). No other article in the repo nests, but that is
because no other article has had its paragraph structure implemented yet — the nesting is a
deliberate choice, not an accident.

The goal is one `translation.py` per article version, whose contents still mirror the
structure of the article (artikel → lid → onderdeel).

Two further problems surfaced while designing this and are in scope:

1. **Duplicated facts.** `atw` articles 1, 2 and 4 each declare the same three fields
   (`datum_einde_wettelijke_termijn`, `wettelijke_termijn`, `verlenging_termijn`). Nothing
   keeps the three copies in step.
2. **Mutation in `__post_init__`.** `atw` 1, 2, 4 and `awb` 7:10 compute results by mutating
   their own input fields. Several fields are both input and output, and one attribute
   (`termijn_opschorten`) is not declared at all — it is created at runtime by `lid_2()`.

## Decisions

| # | Decision |
|---|---|
| D1 | One `translation.py` per version directory. Article structure is expressed in the file, not the filesystem. |
| D2 | Classes are defined in law order (artikel, then lid, then onderdeel) and delegate downward. |
| D3 | Facts live in entity objects under `nl/feiten/`, collected in a `Casus` envelope. Not per-law, not per-article. |
| D4 | Every case-evaluating article takes exactly one constructor parameter: `casus`. |
| D5 | Each class declares `VEREIST`; evaluating without those facts raises `ValueError`. |
| D6 | Version-specific constants live at module level in each version's `translation.py`. |
| D7 | `Casus` slots hold one entity each, not collections. |
| D8 | All ten articles convert (`wbrv` 1, 2, 15; `awb` 6:7, 6:8, 7:10; `atw` 1, 2, 3, 4). |

### Why `Casus` and not a per-law `Feiten`

A per-law `Feiten` grows with the number of *articles* in the law, which has no ceiling — WBRV
has 50+ articles and Wet IB 2001 has hundreds. A `Casus` of entities grows with the number of
*entities*, which is bounded by the domain: there are only so many true facts about a bezwaar,
regardless of how many laws read it. The tenth law to read `Bezwaar` mostly reuses facts the
first nine already declared.

The same rule resolves "what if another law needs different facts about a bezwaar":

- **Same real-world thing, more facts** — one entity holding the superset, all fields optional,
  each article declaring its own `VEREIST` subset. In a real case there is only *one* bezwaar;
  splitting it per law would let two copies of the same objection disagree.
- **Different things sharing a word** — separate entities with distinct names and separate
  `Casus` slots. A naming problem, not a structural one.

If an entity ever does grow unwieldy, it nests further (`Bezwaar.termijnen`) without touching
any article.

### Why the article signature is uniform

`Artikel15(casus)` never changes, no matter which facts the article later reads. Approaches
where the constructor names the entities it needs (`Artikel15(verkrijger=..., zaak=...)`) tie
the signature to the fact set, so adding a fact is a breaking change.

## Architecture

### Layout

```
nl/
  feiten/
    __init__.py
    casus.py              Casus + the vereist() helper
    <entity>.py           one module per entity
  atw/  awb/  wbrv/
    <article>/
      __init__.py         version map (VersieArtikel)
      example.py
      vYYYY_MM_DD/
        translation.py    constants + all classes for that version
        legislation.md
        README.md
```

Deleted: `wbrv/article_15/v2026_01_01/paragraph_1/` and everything under it (6 files). The two
`README.md` bodies merge into `v2026_01_01/README.md`, so the per-level prose survives without
being a directory.

### Entities

| Entity | Facts | Read by |
|---|---|---|
| `WettelijkeTermijn` | `datum_einde_wettelijke_termijn`, `wettelijke_termijn`, `wettelijke_termijn_eenheid`, `verlenging_termijn` | atw 1, 2, 4 |
| `OnroerendeZaak` | `woning`, `rechten_woning_onderworpen`, `rechten_lidmaatschap_woning`, `aanhorigheid`, `in_nederland_gelegen`, `onroerende_zaken`, `rechten_onroerende_zaken_onderworpen`, `waarde_woning`, `waarde_aanhorigheden` | wbrv 2, 15 |
| `Verkrijger` | `natuurlijk_persoon`, `leeftijd`, `vrijstelling_eerder_toegepast`, `verklaring_vrijstelling` | wbrv 15 |
| `Hoofdverblijf` | `woning_tijdelijk_hoofdverblijf`, `verklaring_hoofdverblijf` | wbrv 15 |
| `Verkrijging` | `verkrijging` | wbrv 2 |
| `Belastingmiddel` | `overdrachtsbelasting`, `assurantiebelasting` | wbrv 1 |
| `Besluit` | `datum_bekendmaking_besluit` | awb 6:8 |
| `Bezwaar` | `datum_einde_bezwaartermijn`, `commissie_ingesteld`, `datum_verzoek_verzuim`, `termijn_verzoek_verzuim`, `datum_herstel_verzuim`, `termijn_verdagen_verzocht`, `termijn_verder_uitstel_verzocht`, `instemming_alle_belanghebbenden`, `instemming_indiener`, `andere_belanghebbende_niet_geschaad`, `naleving_wettelijke_procedurevoorschriften` | awb 7:10 |

Every entity field is optional (`None` default), because no single article reads all of them.
`Casus` holds one optional slot per entity, named after the entity in lower case, with the slot
name being what `VEREIST` dotted paths address:

```python
@dataclass
class Casus:
    termijn: WettelijkeTermijn | None = None
    zaak: OnroerendeZaak | None = None
    verkrijger: Verkrijger | None = None
    hoofdverblijf: Hoofdverblijf | None = None
    verkrijging: Verkrijging | None = None
    belastingmiddel: Belastingmiddel | None = None
    besluit: Besluit | None = None
    bezwaar: Bezwaar | None = None
```

`awb` 6:7 additionally needs `datum_aanvang_indieningstermijn` — see Deferred, below.

### Article classes

Names inside method bodies resolve at call time, not at class-definition time. That lifts
Python's base-before-subclass constraint, so classes can be written in the order the law reads.

```python
@dataclass
class Artikel15:
    casus: Casus

    @property
    def lid_1(self) -> bool:
        return Artikel15Lid1(self.casus).onderdeel_p


@dataclass
class Artikel15Lid1:
    casus: Casus

    @property
    def onderdeel_p(self) -> bool:
        return Artikel15Lid1OnderdeelP(self.casus).startersvrijstelling


@dataclass
class Artikel15Lid1OnderdeelP:
    casus: Casus
    VEREIST = (
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
        self.casus.vereist(self.VEREIST, "Artikel15Lid1OnderdeelP")
        return (
            self._verkrijging_woning
            and self._verkrijger_kwalificeert
            and self._eenmalig_beroep
            and self._hoofdverblijfeis
            and self._binnen_waardegrens
        )

    # one private property per legal condition
```

Each level stays independently constructible: `Artikel15Lid1OnderdeelP(casus)` works on its own.

### Missing-fact validation

```python
def vereist(self, namen: tuple[str, ...], door: str) -> None:
    ontbreekt = [n for n in namen if self._lees(n) is None]
    if ontbreekt:
        raise ValueError(f"ontbrekende feiten voor {door}: {', '.join(ontbreekt)}")
```

`_lees` walks a dotted path and treats a missing entity slot as a missing fact.

**Membership rule for `VEREIST`: exactly the fields that have no default in today's
dataclasses.** Fields that already default to `None` are OR'd together in the legal test
(`woning or rechten_woning_onderworpen or rechten_lidmaatschap_woning`), so requiring all of
them would be wrong. Following this rule keeps behaviour identical to the current code — the
same inputs raise, and the same inputs read as false.

Without this, the shared-`Casus` design would be a regression: today `natuurlijk_persoon: bool`
has no default, so omitting it fails loudly at construction. Once every field is optional,
omitting it would make "not exempt" and "facts incomplete" return the same answer, which are
legally different conclusions.

### Versioning

Constants sit at module level in each version's `translation.py`:

```python
WAARDEGRENS = 525_000        # v2025_01_01
WAARDEGRENS = 555_000        # v2026_01_01
LEEFTIJD_MINIMUM = 18
LEEFTIJD_MAXIMUM = 35        # exclusief
```

The v2025↔v2026 difference becomes a one-line read.

`Casus` is unversioned, so a version is stated exactly once, by `VersieArtikel`:

```python
wbrv.Artikel15(datum_toepassing=date(2026, 1, 1), casus=c)
```

`VersionedClass.__call__` is keyword-only for forwarded arguments, so `casus` passes as a
keyword. Had `Casus` lived inside a version directory, the caller would name the version twice —
once on the import and once on `datum_toepassing` — with nothing keeping the two in agreement.

### Replacing `__post_init__`

`atw` 1, 2, 4 and `awb` 7:10 currently compute by mutating their own fields. The rewrite splits
*requested* facts from *granted* results:

```python
# fact:   bezwaar.termijn_verdagen_verzocht
# result: Artikel7_10Lid3(casus).termijn_verdagen   →  min(verzocht, timedelta(weeks=6))
```

Consequences for `awb` 7:10 specifically:

- `termijn_beslissing_bezwaar` stops being a constructor field. It was an input that `lid_1()`
  unconditionally overwrote, so no caller could ever influence it.
- `termijn_opschorten` becomes a declared property on lid 2, rather than an attribute created at
  runtime by `lid_2()`. Today `datum_einde_beslistermijn` raises `AttributeError` unless
  `__post_init__` has run.
- `datum_einde_beslistermijn` sums the four lid properties.
- `__post_init__` is removed.

## Preserved defects

Reproduced as-is and marked in code. Fixing them is a separate decision.

**`awb` 7:10 lid 4** (`article7_10/v2009_10_01/translation.py:118`). `onderdeel_b` is
`instemming_indiener and andere_belanghebbende_niet_geschaad`; when those are `None` it
evaluates to `None`, not `False`. The `elif onderdeel_a is False and onderdeel_b is False and
onderdeel_c is False` branch therefore almost never fires, so a requested
`termijn_verder_uitstel` is silently granted with no consent recorded.

## Fixed defects

`wbrv/article_15/__init__.py` is rewritten by this work, so two existing bugs are corrected:

- Line 19: `Artikel15Lid1OnderdeelP` maps `date(2025,1,1)` to `v2025_01_01.Artikel15Lid1` — the
  wrong class. Its `name=` argument is also a copy-paste leftover reading `"Artikel15Lid1"`.
- Line 23: `__all__` omits `Artikel15Lid1OnderdeelP`, although `example.py` and
  `wbrv/__init__.py` both use it.

## Conventions established

- Articles that evaluate a case take `casus`. Purely definitional articles keep their own
  parameters — `atw` article 3 computes public holidays from `jaar: int`, which is a calendar
  function, not a question about a case. Wrapping it in `Casus` would add indirection and share
  nothing.
- Entities are named after the real-world thing they describe, never after a law or an article.
- Facts only. Derived results never enter `Casus`.

## Deferred

**Cross-article inputs stay facts.** `awb` 6:7 needs `datum_aanvang_indieningstermijn`, which is
6:8's output; `wbrv` article 1 needs `overdrachtsbelasting`, which is article 2's output. Having
articles ask each other instead would mirror the law's own cross-reference graph and remove the
duplication at its root, but it is a separate concern from this restructuring. This branch keeps
them as facts and marks the seam.

**Collections in `Casus`.** Slots hold one entity. `wbrv` article 15 already flattens what looks
like a second object (`aanhorigheid`, `waarde_aanhorigheden`) into scalar fields to avoid this.
Moving a slot to a list later touches that slot's readers and nothing else.

**`atw` and `awb` entity cuts** are proposed above but not legally reviewed. The split of the
four `verklaring`/history facts across `Verkrijger` and `Hoofdverblijf` — history *of the
person* versus intent *about the woning* — is the one most worth a second look.

## Verification

The repo has no test framework; `example.py` scripts are the de facto verification.

1. On `wbrv`, capture `python example.py` output for all ten articles.
2. On `wbrv-article`, require byte-identical output. Every `example.py` is rewritten to build a
   `Casus`, so the scripts change but their printed results must not.
3. `import taxlation.nl` succeeds, and every article is reachable from its package `__init__`.
4. New behaviour: omitting a required fact raises `ValueError` naming every missing fact, rather
   than `TypeError` or a silent `False`.

Step 2 is the load-bearing check. This is a restructuring: no legal conclusion may change.

## Out of scope

- Adding a test framework.
- Fixing the `awb` 7:10 lid 4 consent logic.
- Article-to-article delegation.
- Any change to `taxlation/core/versioning.py`.
