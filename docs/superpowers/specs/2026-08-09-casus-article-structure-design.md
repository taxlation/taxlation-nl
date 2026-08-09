# Casus + article structure — design

**Date:** 2026-08-09
**Branch:** `wbrv-article`, branched from `wbrv`
**Status:** revised after adversarial review — see Review history
**Companion change:** a lockstep PR in `taxlation-api` (required, see Consumers)

## Problem

Branch `wbrv` introduced a nested directory layout for one article version:

```
wbrv/article_15/v2026_01_01/
  translation.py                              Artikel15
  paragraph_1/translation.py                  Artikel15Lid1
  paragraph_1/subparagraph_p/translation.py   Artikel15Lid1OnderdeelP
```

Nine files where the sibling version `v2025_01_01` uses two, for classes that differ by a
single constant (`525_000` vs `555_000`). No other article nests, but only because no other
article has had its paragraph structure implemented yet — the nesting is a deliberate choice,
not an accident.

The goal is one `translation.py` per article version, whose contents still mirror the structure
of the article (artikel → lid → onderdeel).

Two further problems surfaced while designing this and are in scope:

1. **Duplicated facts.** `atw` articles 1, 2 and 4 each declare the same three fields
   (`datum_einde_wettelijke_termijn`, `wettelijke_termijn`, `verlenging_termijn`). Nothing keeps
   the three copies in step.
2. **Mutation in `__post_init__`.** `atw` 1, 2, 4 and `awb` 7:10 compute results by mutating
   their own input fields. Several fields are both input and output, and one attribute
   (`termijn_opschorten`) is not declared at all — `lid_2()` creates it at runtime.

## Constraints

### Consumers

`taxlation-api` is a live FastAPI service that consumes these classes. It does not depend on
`taxlation-nl` as a package at deploy time — `scripts/vendor-taxlation-nl.sh` **clones this repo
and overwrites `src/taxlation/` on every Cloudflare build**:

```
taxlation-api develop  ->  taxlation-nl develop
taxlation-api main     ->  taxlation-nl main
```

**Merging this work to `develop` or `main` deploys it.** There is no separate release step.

The exact surface in use today:

| Consumer | Constructs | Reads |
|---|---|---|
| `routes/nl/bezwaar/indieningstermijn_route.py` | `awb.Artikel6_8(datum_toepassing, datum_bekendmaking_besluit)`, `awb.Artikel6_7(datum_toepassing, datum_aanvang_indieningstermijn)` | `.datum_aanvang_indieningstermijn`, `.datum_einde_indieningstermijn`, `.indieningstermijn` |
| `routes/nl/bezwaar/beslistermijn_route.py` | `awb.Artikel7_10(datum_einde_bezwaartermijn, commissie_ingesteld)` | `.datum_einde_beslistermijn`, `.termijn_beslissing_bezwaar`, `.datum_einde_bezwaartermijn` |
| `services/nl/atw_verlenging.py` | `atw.Artikel1`, `atw.Artikel2`, `atw.Artikel4`, each with `datum_toepassing`, `datum_einde_wettelijke_termijn`, `wettelijke_termijn`, plus `verlenging_termijn` threaded from the previous article | `.verlenging_termijn`, `.datum_einde_verlengde_termijn` |

`wbrv` has **no consumer** — it is not present in the vendored copy and no route imports it.

### Evidence that silent API breaks already happen here

`taxlation-api/tests/test_beslistermijn.py::test_atw_verlenging_dag_unit_matches_library`
currently fails:

```
E   AttributeError: module 'taxlation.nl.awb' has no attribute 'Art_7_10'
1 failed, 1 passed
```

An earlier `Art_7_10` → `Artikel7_10` rename broke it and nobody noticed. The stale
`atw/art_1`…`art_4` and `awb/art_6_7`…`art_7_10` directories in the vendored copy are orphaned
`__pycache__` from that same rename. This is not a hypothetical risk; it is the repeat of one.

Repairing that test is part of the companion PR.

## Decisions

| # | Decision |
|---|---|
| D1 | One `translation.py` per version directory. Article structure is expressed in the file, not the filesystem. |
| D2 | Classes are defined in law order (artikel, then lid, then onderdeel) and delegate downward. |
| D3 | Facts live in entity objects under `nl/feiten/`, collected in a `Casus` envelope. Not per-law, not per-article. |
| D4 | Every case-evaluating article takes exactly one constructor parameter: `casus`. |
| D5 | `VEREIST` is derived from each **legal predicate**, not from legacy dataclass defaults, and supports disjunctive groups. Evaluating without determinate facts raises `ValueError`. |
| D6 | Version-specific constants live at module level in each version's `translation.py`. |
| D7 | `Casus` slots hold one entity each. This is a documented limitation of the current scope, not a permanent contract. |
| D8 | All ten articles convert (`wbrv` 1, 2, 15; `awb` 6:7, 6:8, 7:10; `atw` 1, 2, 3, 4). |
| D9 | This is a **breaking API change**, declared as such. No compatibility shims. A lockstep `taxlation-api` PR migrates both routes, the service and the tests, and must merge together with this one. |
| D10 | A pytest characterization suite is written against the **pre-change** code and committed before any refactoring begins. It is the oracle. |

### Why `Casus` and not a per-law `Feiten`

A per-law `Feiten` grows with the number of *articles* in the law, which has no ceiling — WBRV
has 50+ articles, Wet IB 2001 has hundreds. A `Casus` of entities grows with the number of
*entities*, which is bounded by the domain: there are only so many true facts about a bezwaar,
regardless of how many laws read it. The tenth law to read `Bezwaar` mostly reuses facts the
first nine already declared.

The same rule resolves "what if another law needs different facts about a bezwaar":

- **Same real-world thing, more facts** — one entity holding the superset, all fields optional,
  each article declaring its own `VEREIST` subset. In a real case there is only *one* bezwaar;
  splitting it per law would let two copies of the same objection disagree.
- **Different things sharing a word** — separate entities with distinct names and separate
  `Casus` slots. A naming problem, not a structural one.

### Why the article signature is uniform

`Artikel15(casus)` never changes, regardless of which facts the article later reads. Approaches
where the constructor names the entities it needs (`Artikel15(verkrijger=..., zaak=...)`) tie the
signature to the fact set, making every added fact a breaking change.

### Cardinality — an explicit limitation

`Casus` slots are singular, which is sufficient for all ten articles in scope and for every
`example.py` and route in existence today. It is **not** sufficient in general: identity and
relationships between multiple properties, acquisitions, acquirers or objections cannot be
expressed, and adding scalar fields cannot recover which value belongs to which object.
`wbrv` article 15 already flattens what looks like a second object (`aanhorigheid`,
`waarde_aanhorigheden`) into scalars for exactly this reason.

Therefore `Casus` is adopted **for the ten articles in scope**. Establishing it as the
repository-wide contract for whole laws requires modelling cardinality and relationships first —
identified collections and associations under an aggregate root. The trigger to revisit is the
first article that must distinguish two instances of one entity type. Until then, no design
decision may assume the singular form is permanent.

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
tests/                    characterization suite (new)
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
| `Bezwaar` | `datum_aanvang_indieningstermijn`, `datum_einde_bezwaartermijn`, `commissie_ingesteld`, `datum_verzoek_verzuim`, `termijn_verzoek_verzuim`, `datum_herstel_verzuim`, `termijn_verdagen_verzocht`, `termijn_verder_uitstel_verzocht`, `instemming_alle_belanghebbenden`, `instemming_indiener`, `andere_belanghebbende_niet_geschaad`, `naleving_wettelijke_procedurevoorschriften` | awb 6:7, 7:10 |

Every entity field is optional (`None` default), because no single article reads all of them.
`Casus` holds one optional slot per entity, and the slot name is what `VEREIST` dotted paths
address:

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
        ("zaak.woning", "zaak.rechten_woning_onderworpen",
         "zaak.rechten_lidmaatschap_woning"),          # disjunctive group
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

**Interface change.** Today's inheritance chain means `Artikel15` also exposes `onderdeel_p()`
and `startersvrijstelling()`, and `Artikel15Lid1` exposes `startersvrijstelling()`. Delegation
removes those inherited members, and `startersvrijstelling` becomes a property rather than a
method. Per D9 this is declared, not hidden; the characterization suite enumerates every
currently reachable member so the removals are deliberate and listed.

### Missing-fact validation

```python
def vereist(self, namen, door: str) -> None:
    ontbreekt = []
    for naam in namen:
        if isinstance(naam, tuple):                      # disjunctive group
            waarden = [self._lees(p) for p in naam]
            if not any(w is True for w in waarden) and any(w is None for w in waarden):
                ontbreekt.append(" of ".join(naam))
        elif self._lees(naam) is None:
            ontbreekt.append(naam)
    if ontbreekt:
        raise ValueError(f"ontbrekende feiten voor {door}: {', '.join(ontbreekt)}")
```

`_lees` walks a dotted path and treats a missing entity slot as a missing fact.

**Membership is derived from the legal predicate, never from legacy defaults.** A single path
must be known. A tuple is a disjunction, and a disjunction is determinate when *any* operand is
`True` (the alternative is satisfied, the rest cannot change the outcome) or when *all* operands
are known (the alternative is genuinely unsatisfied).

The earlier draft of this spec copied requiredness from today's dataclass defaults. That was
wrong and self-defeating: the three dwelling predicates all default to `None`, so they would
have been excluded, and a `Casus` with no dwelling fact at all would pass validation and return
"not exempt" — the precise conflation of *unknown* with *false* that `VEREIST` exists to
prevent, and the same nullable-Boolean flaw that causes the `awb` 7:10 defect below.

**This is the one place the refactor deliberately changes behaviour.** Today, omitting all three
dwelling facts silently yields `False`. After this change it raises. The characterization suite
records the old result and asserts the new one, with the divergence listed explicitly.

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
once on the import, once on `datum_toepassing` — with nothing keeping them in agreement.

### Replacing `__post_init__`

The rewrite splits *requested* facts from *granted* results:

```python
# fact:   bezwaar.termijn_verdagen_verzocht
# result: Artikel7_10Lid3(casus).termijn_verdagen   →  min(verzocht, timedelta(weeks=6))
```

For `awb` 7:10 specifically:

- `termijn_beslissing_bezwaar` stops being a constructor field. It was an input `lid_1()`
  unconditionally overwrote, so no caller could ever influence it. It becomes a property of
  lid 1, which is where the route must now read it.
- `termijn_opschorten` becomes a declared property on lid 2 rather than an attribute created at
  runtime. Today `datum_einde_beslistermijn` raises `AttributeError` unless `__post_init__` ran.
- `datum_einde_beslistermijn` sums the four lid properties.
- `__post_init__` is removed.

### The `atw` accumulation chain — known risk

`atw_verlenging` threads `verlenging_termijn` through three articles, each receiving the
previous one's mutated output as its own input:

```
Artikel1(...)                                     -> .verlenging_termijn
Artikel2(..., verlenging_termijn=art_1.verlenging_termijn)  -> .verlenging_termijn
Artikel4(..., verlenging_termijn=art_2.verlenging_termijn)  -> .datum_einde_verlengde_termijn
```

The accumulation is built on the very mutation being removed, so this is **not** a mechanical
conversion and it is the highest-risk part of the work. The implementation plan must choose and
justify an explicit accumulation model — candidates: each article exposing its own *additional*
extension with the caller summing, or an article-to-article delegation chain (see Deferred).

Constraint: `atw_verlenging`'s result must be unchanged. The passing route test
(`test_beslistermijn_uses_dag_unit_and_extends_over_weekend`, asserting `2025-12-29`) exercises
this whole chain end to end and is the oracle for it.

## Verification

The earlier draft proposed comparing `example.py` stdout before and after. That is not an
adequate oracle: each example is a single happy path, both the inputs and the implementation get
rewritten together, and identical output would certify nothing about false branches, boundaries,
version selection, exceptions or removed members.

### Phase 0 — build the oracle first (D10)

Before any production file is touched, on a branch off `wbrv`:

1. Add `pytest` to a `dev` dependency group, matching `taxlation-api`, which already uses it.
2. Write `tests/` characterization tests against the **current** implementation, recording what
   it does rather than what it should do. Coverage required:
   - every legal branch of every article, true and false;
   - boundary values — `leeftijd` at 17/18/34/35, waarde at `WAARDEGRENS` and ±1, dates either
     side of each termijn;
   - version selection at, before and after each effective date, including the `ValueError`
     when no version applies;
   - `None`/missing combinations for every nullable field;
   - repeated evaluation and re-reads of the same instance, which pins the behaviour that
     removing `__post_init__` mutation must preserve;
   - each delegated entry point invoked directly, not only through its parent;
   - a full enumeration of every currently reachable public member per class, so D9's removals
     are an explicit diff rather than a discovery.
3. Commit this suite. It must be green against unmodified code.

### Phase 1 — refactor

The suite stays green throughout, with exactly two sanctioned diffs, each its own commit with
the old and new behaviour asserted side by side:

- the disjunctive-group validation change described above;
- the members removed by D9.

### Phase 2 — lockstep

`taxlation-api`: migrate both routes and `atw_verlenging` to build a `Casus`, repair the
already-failing `Art_7_10` test, and run its suite green against this branch vendored in.
`test_beslistermijn_uses_dag_unit_and_extends_over_weekend` must still return `2025-12-29`.

Neither PR merges alone.

## Quarantined defect

**`awb` 7:10 lid 4** (`article7_10/v2009_10_01/translation.py:118`). `onderdeel_b` is
`instemming_indiener and andere_belanghebbende_niet_geschaad`; when those are `None` it
evaluates to `None`, not `False`. The `elif onderdeel_a is False and onderdeel_b is False and
onderdeel_c is False` branch therefore almost never fires, so a requested
`termijn_verder_uitstel` is silently granted with no consent recorded.

Behaviour is reproduced unchanged, but it is **not** accepted silently. The characterization
suite encodes it as an `xfail` naming the legally correct result, so parity with a known-wrong
conclusion is visible rather than certified. Fixing it is a separate decision.

## Fixed defects

`wbrv/article_15/__init__.py` is rewritten by this work, so two existing bugs are corrected:

- Line 19: `Artikel15Lid1OnderdeelP` maps `date(2025,1,1)` to `v2025_01_01.Artikel15Lid1` — the
  wrong class. Its `name=` argument is also a copy-paste leftover reading `"Artikel15Lid1"`.
- Line 23: `__all__` omits `Artikel15Lid1OnderdeelP`, although `example.py` and
  `wbrv/__init__.py` both use it.

Noted but left alone, being behaviour-neutral: `startersvrijstelling`'s first clause,
`(A or B or C) or ((A or B or C) and aanhorigheid)`, reduces to `(A or B or C)`.

## Conventions established

- Articles that evaluate a case take `casus`. Purely definitional articles keep their own
  parameters — `atw` article 3 computes public holidays from `jaar: int`, a calendar function
  rather than a question about a case. Wrapping it in `Casus` would add indirection and share
  nothing.
- Entities are named after the real-world thing they describe, never after a law or an article.
- Facts only. Derived results never enter `Casus`.

## Deferred

**Cross-article inputs stay facts.** `awb` 6:7 needs `datum_aanvang_indieningstermijn`, which is
6:8's output; `wbrv` article 1 needs `overdrachtsbelasting`, which is article 2's output. Having
articles ask each other would mirror the law's own cross-reference graph and remove the
duplication at its root, but it is a separate concern. This branch keeps them as facts on
`Bezwaar` and `Belastingmiddel` and marks the seam. Note the `atw` accumulation chain may force
this question earlier than planned.

**Collections in `Casus`.** See Cardinality above for the limitation and its revisit trigger.

**`atw` and `awb` entity cuts** are proposed here but not legally reviewed. The split of the four
`verklaring`/history facts across `Verkrijger` and `Hoofdverblijf` — history *of the person*
versus intent *about the woning* — is the one most worth a second look.

## Out of scope

- Fixing the `awb` 7:10 lid 4 consent logic.
- Article-to-article delegation beyond what the `atw` chain forces.
- Any change to `taxlation/core/versioning.py`.
- Modelling `Casus` cardinality.

## Review history

**2026-08-09 — Codex adversarial review, verdict `needs-attention`, 4 high findings.** All four
accepted; three changed decisions and one was confirmed as larger than reported.

| Finding | Resolution |
|---|---|
| `VEREIST` derived from legacy defaults lets incomplete disjunctions become a legal `False` | D5 rewritten: membership derived from the legal predicate, disjunctive groups added, divergence from current behaviour made explicit and tested |
| Single entity slots cannot encode multi-entity cases the design itself admits | D7 kept but downgraded — scoped to the ten articles, with the limitation and a revisit trigger documented rather than the contract generalised |
| Call-time composition silently removes existing public behaviour | Confirmed and found to be larger: `taxlation-api` routes read `.termijn_beslissing_bezwaar` and construct with flat kwargs, and the Cloudflare build auto-vendors this repo. D9 declares the break; a lockstep API PR is now required. Verified empirically — an identical break from an earlier rename has been sitting broken in `test_beslistermijn.py` |
| `example.py` stdout comparison is not an adequate preservation oracle | Verification rewritten around a pre-change pytest characterization suite (D10), with the `awb` 7:10 defect quarantined as `xfail` instead of silently preserved |
