# Casus + article structure — design

**Date:** 2026-08-09
**Branch:** `wbrv-article`, branched from `wbrv`
**Status:** revised after adversarial review — see Review history
**Companion change:** a follow-up PR in `taxlation-api` (see Consumers)

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

**The service has no customers.** Breaking its API is therefore acceptable and needs no
migration window, no deprecation period and no compatibility shims. What it does *not* excuse
is leaving the Worker broken indefinitely: the vendor step will ship whatever is on this repo's
`develop`/`main`, so `taxlation-api` gets a follow-up PR that migrates its routes, service and
tests. That PR does not have to land in the same moment as this one.

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
| D2 | The article tree is expressed as **nested class namespaces** — `Artikel15.Lid1.OnderdeelP` — written outer-first, so the file reads in law order and the dotted path is the legal citation. Each level delegates downward by passing the same `casus`. |
| D3 | Facts live in entity objects under `nl/feiten/`, collected in a `Casus` envelope. Not per-law, not per-article. |
| D4 | Every case-evaluating article takes exactly one constructor parameter: `casus`. |
| D5 | `VEREIST` is derived from each **legal predicate**, not from legacy dataclass defaults, and supports disjunctive groups. Evaluating without determinate facts raises `ValueError`. |
| D6 | Each version's `translation.py` is a **complete, independent implementation**. Versions may differ in logic, class set and required facts, not only in constants. No inheritance or imports between versions. |
| D7 | `Casus` slots hold one entity each. This is a documented limitation of the current scope, not a permanent contract. |
| D8 | All ten articles convert (`wbrv` 1, 2, 15; `awb` 6:7, 6:8, 7:10; `atw` 1, 2, 3, 4). |
| D9 | This is a **breaking API change**, declared as such. No compatibility shims, no deprecation window — the service has no customers. A follow-up `taxlation-api` PR migrates its routes, service and tests, and must be green before this work merges to `develop`/`main`. |
| D10 | Frozen, implementation-independent **case vectors plus golden results generated from the pre-change code** are committed before any refactoring begins. They are the oracle; both old and new implementations run the same vectors. |
| D11 | The `atw` chain is expressed as **article-to-article delegation** (art. 4 → art. 2 → art. 1), not as caller-threaded accumulation. |
| D12 | `Casus` carries `datum_toepassing`, the date the case is assessed as of. It is the single source for version selection and is what makes delegated version lookups correct. |
| D13 | `VersieArtikel` gains `__getattr__`, deriving a version map for nested classes from the article's single map. Per-class version maps are no longer hand-written. |

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

Entity fields default to `None`, meaning *unknown*, because no single article reads all of them.

**Exception: a field whose default the law itself supplies keeps that default, and must carry a
comment saying so.** `waarde_aanhorigheden` is the only such case in scope — it is
`int = 0` today, because acquiring no aanhorigheden means a value of zero, which is a legal fact
rather than an absence of one. Defaulting it to `None` would make
`waarde_woning + waarde_aanhorigheden` raise `TypeError`, and adding it to `VEREIST` would force
callers to state a zero the law already implies. The same reasoning applies to
`termijn_verdagen_verzocht` and `termijn_verder_uitstel_verzocht`, which are
`timedelta(days=0)` today, and to `WettelijkeTermijn.verlenging_termijn`.

The rule is therefore: `None` means unknown and belongs in `VEREIST`; a law-supplied default
means known-by-default and does not. Any field given a non-`None` default without a legal
justification in its comment is a bug.

#### Why one `Casus` file is not the object we rejected

Entities get a module each; `Casus` is a single class in a single file for the whole of
`taxlation.nl`. That is deliberate, and it is not the per-law `Feiten` problem returning at the
envelope level.

`Casus` holds **no facts and no semantics** — one line per entity, plus the `vereist()` helper.
It grows in length, never in complexity: at 50 entities it is roughly 70 lines of slot
declarations. The rejected `Feiten` grew in *fields*, each carrying a legal comment, a definition
and a semantic claim about what the law means. A manifest of slots and a bag of facts are
different kinds of object that merely share the property of getting longer.

Real cost, named rather than waved away: one shared file that every new law appends to is a
merge-conflict hotspot. At this team size a one-line append rarely conflicts, and no mechanism is
proposed for it until it actually hurts.

Scope is per jurisdiction. This repo is `taxlation-nl`, so `nl/feiten/casus.py`. Another
jurisdiction gets its own `Casus`; nothing is shared across them.

#### Keeping entities from sprawling

Current size: **35 fields across 8 entities for 10 articles**, averaging 4.4 fields each, the
largest being `Bezwaar` at 12. The concern is what this looks like at 200 articles, and three
rules bound it:

- **Prefer more small entities over fewer large ones.** Adding an entity costs one optional
  `Casus` slot and affects no existing article. Adding a field to an existing entity is what
  makes it unwieldy. When an entity passes roughly 15 fields, split it or nest a sub-object
  (`Bezwaar.termijnen`) rather than letting the flat list grow.
- **Entities need not be universal.** "One entity per real-world thing" is scoped to *a case*. If
  WBRV's onroerende zaak and another law's genuinely differ as legal concepts, they are different
  things and become different entities. Nothing requires one `OnroerendeZaak` for all of Dutch
  tax law.
- **Size costs browsing, not usage.** Every field is optional and `VEREIST` names each
  provision's inputs, so evaluating art. 15 touches ~12 facts whether its entities hold 12 fields
  or 120.

**The larger risk is not size but definitional drift.** A big entity is visible and merely
annoying. Two laws quietly reusing one field name for subtly different legal notions — "woning"
in WBRV versus "eigen woning" in Wet IB — produces wrong answers with nothing to notice. So:

> A field carries exactly one legal concept. Its comment states that concept and where the law
> defines it. A second law needing a different notion gets its own field with a name that
> distinguishes them — never a reused one, and never a widened definition.

Reusing a field is a legal claim that two provisions mean the same thing, and it must be made
deliberately.

This is an assumption, not a proof: entity size is expected to level off because the tenth law
reading `Bezwaar` mostly reuses facts the first nine declared. Revisit trigger — an entity
passing 15 fields, or any field whose comment needs two definitions to describe it.

`Casus` holds one optional slot per entity, and the slot name is what `VEREIST` dotted paths
address:

```python
@dataclass
class Casus:
    datum_toepassing: date | None = None      # the date the case is assessed as of (D12)
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

The article tree is the class namespace (D2). Nested classes are written outer-first, so the
file reads in the order the law reads, and the dotted path *is* the citation —
`Artikel15.Lid1.OnderdeelP` rather than a mangled `Artikel15Lid1OnderdeelP` that has to be
parsed back into a legal reference.

```python
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
            """Artikel 15, lid 1, onderdeel p WBRV — startersvrijstelling."""
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
                self.casus.vereist(self.VEREIST, "Artikel15.Lid1.OnderdeelP")
                return (
                    self._verkrijging_woning
                    and self._verkrijger_kwalificeert
                    and self._eenmalig_beroep
                    and self._hoofdverblijfeis
                    and self._binnen_waardegrens
                )

            # one private property per legal condition

        @property
        def onderdeel_p(self) -> bool:
            return Artikel15.Lid1.OnderdeelP(self.casus).startersvrijstelling

    @property
    def lid_1(self) -> bool:
        return Artikel15.Lid1(self.casus).onderdeel_p
```

Every level stays independently constructible, and each takes the same single argument:

```python
Artikel15(casus).lid_1
Artikel15.Lid1(casus).onderdeel_p
Artikel15.Lid1.OnderdeelP(casus).startersvrijstelling
```

Delegation passes the `casus` rather than the child object, so a caller never assembles the
article's internal shape — it supplies the case and asks a question at whichever level it cares
about.

Outer-class references inside method bodies (`Artikel15.Lid1.OnderdeelP`) resolve at call time,
by which point the module-level name is bound. Nesting is what gives law-order reading; call-time
resolution is only what permits the downward reference.

**Known cost: indentation grows with the depth of the article.** Measured on a full `wbrv`
article 15 written this way — 74 lines — leaf method bodies sit at column 16, the deepest wrapped
continuation at 28, and the longest line is 97 characters. Comfortable at three levels; an
article nesting artikel → lid → onderdeel → subonderdeel would add four columns per level. No
article in scope reaches that. If one later does, reconsider nesting *for that article* rather
than flattening the convention repo-wide.

What keeps this tolerable is that the bulk does not nest. Because every level holds only
`casus: Casus`, the fact declarations — a dozen fields whose trailing legal comments run past 140
characters — live in `nl/feiten/` at column 0, written once for every article that reads them.
Only the delegating properties and the leaf's condition properties are nested, and those are
short. A design keeping facts on the leaf pays the indentation cost on precisely the longest,
comment-heaviest block in the file.

**Interface change.** Today's inheritance chain means `Artikel15` also exposes `onderdeel_p()`
and `startersvrijstelling()`, and `Artikel15Lid1` exposes `startersvrijstelling()`. Nesting plus
delegation removes those inherited members — each level exposes only its own provision — and
`startersvrijstelling` becomes a property rather than a method. Per D9 this is declared, not
hidden, and the removed members are listed in that commit.

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

#### Validation is eager, and deliberately over-requires

`VEREIST` is checked in full before evaluation, so a case is rejected for a missing fact even
when an earlier conjunct already settles the outcome — `natuurlijk_persoon=False` makes the
startersvrijstelling determinately `False`, yet an unknown `waarde_woning` still raises.

This is accepted, not overlooked. The alternative — validating lazily against the predicate's
short-circuit structure, or modelling it as a three-valued expression tree — answers strictly
more cases, at three costs:

- **The error surface becomes evaluation-order dependent.** Which fact a user is told to supply
  would depend on the order conjuncts happen to be written in, and reordering a condition for
  readability would change the API's errors. For a legal engine whose source of truth is the
  statute's wording, that couples an implementation detail to the answer.
- **It reintroduces three-valued logic through the back door.** Determinacy-aware short-circuit
  evaluation *is* Kleene logic; every caller and every delegating article would have to handle
  unknown as a third state. That model was considered and rejected in favour of raising.
- **Eager validation is closer to today's behaviour**, where required constructor fields must be
  supplied regardless of whether an earlier field already decides the outcome.

The semantics adopted are determinacy **of the inputs an article declares it needs**, not
determinacy of the outcome. `VEREIST` answers "what must I know to apply this provision", which
is the question the API asks, and it answers it identically no matter how the condition is
written.

The trade-off is real and worth revisiting if callers hit it in practice: an article that could
have answered will instead demand facts. Revisit trigger — a consumer legitimately unable to
supply a fact for a case that is already determinate.

### Versioning

**Each version directory holds a complete, independent implementation of the article** (D6).
Versions of a provision do not merely retune constants — a later version can restructure the
lidden, add or repeal an onderdeel, change how a condition is composed, or require facts no
earlier version needed. The design must not assume otherwise.

Consequences:

- **No inheritance or imports between version directories.** `v2026_01_01/translation.py` never
  imports from `v2025_01_01/`. Duplication between versions is correct and intended: two
  versions of a provision are two different laws that happen to share a name, and coupling them
  means a later amendment silently rewrites history.
- **The class set may *grow* per version. Removal is not yet supported.** `VersieArtikel` maps
  one class name at a time, so a version introducing a new `Artikel15Lid3` just adds a map for
  it, and nothing forces versions to expose the same classes. But a class *removed* in a later
  version cannot be expressed by omitting the date: `VersionedClass` selects the last mapping
  at or before the reference date, so omission keeps returning the pre-repeal class forever —
  see the repeal gap below. Until repeal semantics exist, a provision that disappears must be
  treated as an open question rather than modelled by omission.
- **`VEREIST` is per class, therefore already per version.** A version needing a fact no other
  version needs declares it, and no other version is affected.
- **`Casus` entity fields are the union across all versions of all articles.** Every field is
  optional, so a fact introduced by one version costs nothing to the others. This is why `Casus`
  is unversioned, and why versioning it would have been wrong.

Constants at module level are therefore a *convenience for the versions that happen to differ
only by a number*, not the mechanism of versioning:

```python
WAARDEGRENS = 525_000        # v2025_01_01
WAARDEGRENS = 555_000        # v2026_01_01
LEEFTIJD_MINIMUM = 18
LEEFTIJD_MAXIMUM = 35        # exclusief
```

For `wbrv` article 15 this makes the v2025↔v2026 difference a one-line read. That is a pleasant
property of this particular pair, not a goal to preserve for future versions.

`Casus` is unversioned, so a version is stated exactly once, by `VersieArtikel`:

```python
wbrv.Artikel15(datum_toepassing=date(2026, 1, 1), casus=c)
```

`VersionedClass.__call__` is keyword-only for forwarded arguments, so `casus` passes as a
keyword. Had `Casus` lived inside a version directory, the caller would name the version twice —
once on the import, once on `datum_toepassing` — with nothing keeping them in agreement.

#### Open question: repeal has no representation

Accepting that versions differ arbitrarily exposes a gap in `core/versioning.py`. Versions carry
a start date but no end date, and `VersionedClass.__call__` selects the last version whose date
is `<= reference_date`, with no upper bound. A repealed provision therefore keeps answering
forever:

```python
versions={date(2025,1,1): V2025, date(2026,1,1): V2026}
# onderdeel p repealed per 2030-01-01 — unrepresentable
wbrv.Artikel15.Lid1.OnderdeelP(casus=Casus(datum_toepassing=date(2035,1,1)))  # still V2026
```

There is an undocumented escape hatch — `if not callable(apply_dataclass): return
apply_dataclass` means a date can map to a non-callable, so `date(2030,1,1): None` yields `None`.
That fails silently rather than raising, which is the wrong default for a legal answer.

No article in scope is repealed, so this blocks nothing now. It is recorded because D6 makes it
inevitable, and because "no change to `core/versioning.py`" is an assumption with a shelf life.
Resolving it properly means either end-dated version ranges or an explicit repeal sentinel that
raises.

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

### The `atw` accumulation chain — contract (D11)

`atw_verlenging` currently threads `verlenging_termijn` through three articles, each receiving
the previous one's mutated output as its own input:

```
Artikel1(...)                                               -> .verlenging_termijn
Artikel2(..., verlenging_termijn=art_1.verlenging_termijn)  -> .verlenging_termijn
Artikel4(..., verlenging_termijn=art_2.verlenging_termijn)  -> .datum_einde_verlengde_termijn
```

Reading the actual implementations, every step is **carry-in sensitive**, so the accumulation
model is not a free choice:

| Article | Effect on the running extension |
|---|---|
| art. 1 lid 1 | adds a day while `datum_einde + running` lands on a weekend or an `Artikel3` holiday — the loop condition reads the running total |
| art. 1 lid 2 | **resets to zero** when `wettelijke_termijn < 0` |
| art. 2 | when the term is ≥ 3 days, adds days until two workdays fall within it — again re-evaluating the running total each iteration |
| art. 4 `onderdeel_a` | **resets to zero** for specifically-formulated terms (`uur`, > 90 dagen, > 12 weken, > 3 maanden, ≥ 1 jaar) |

Two adds that depend on the carry-in and two resets that discard it. "Each article returns its
own additional extension and the caller sums them" is therefore **wrong**: it cannot express the
resets, and the adds would compute against the wrong base.

**Adopted contract — each article's `verlenging_termijn` is a pure function of the case, and
delegates to the article it builds on:**

```python
Artikel1(casus).verlenging_termijn   # base; carry-in is casus.termijn.verlenging_termijn
Artikel2(casus).verlenging_termijn   # starts from Artikel1(casus).verlenging_termijn
Artikel4(casus).verlenging_termijn   # 0 if onderdeel_a else Artikel2(casus).verlenging_termijn
```

The chain collapses to one call and `atw_verlenging`'s manual threading is deleted outright:

```python
atw.Artikel4(casus).datum_einde_verlengde_termijn
```

This is the article-to-article delegation listed under Deferred; the `atw` chain forces it, as
that entry anticipated. The composition order belongs to the legislation, not to the caller,
which is why `atw_verlenging` was the wrong home for it.

**That is a legal reading, and it was checked rather than assumed.** Both provisions speak of
*een in een wet gestelde termijn* — the statutory term — and neither says "de op grond van het
vorige artikel verlengde termijn":

> Art. 1 lid 1: "Een in een wet gestelde termijn die op een zaterdag, zondag of algemeen erkende
> feestdag eindigt, wordt verlengd tot en met de eerstvolgende dag die niet een zaterdag, zondag
> of algemeen erkende feestdag is."
>
> Art. 2: "Een in een wet gestelde termijn van ten minste drie dagen wordt, zo nodig, zoveel
> verlengd, dat daarin ten minste twee dagen voorkomen die niet een zaterdag, zondag of algemeen
> erkende feestdag zijn."

Read literally, they could be two independent rules over the same statutory term, in which case
the compounding in `atw_verlenging` would be a caller's convention and encoding it in the
articles would misrepresent the law. **Confirmed by the author (2026-08-09): art. 2 operates on
the term as art. 1 leaves it, and art. 4 disapplies the ATW as a whole.** Compounding is
therefore the legislation's own composition, and D11 records it rather than inventing it.

Consequence to accept knowingly: `Artikel2(casus)` always includes art. 1, so "artikel 2 alone"
becomes unaskable. Note the current code is already a hybrid on this point — art. 2 counts
workdays over the *original* term window, while extending from the *accumulated* end date. That
asymmetry is preserved.

Also resolved by this: `Artikel4.wet_geldt_niet` is currently a **property with a side effect**
— it assigns `self.verlenging_termijn = timedelta(days=0)` and `__post_init__` reads it purely
for that effect. It becomes an ordinary predicate, with the reset expressed inside
`verlenging_termijn`.

Preserved as-is: art. 2 computes its start date as `einde - termijn + 1 dag` while art. 4 uses
`einde - termijn`. That one-day inconsistency is reproduced, not corrected.

#### Why delegation forces `Casus.datum_toepassing` (D12)

`Artikel1.lid_1` constructs `Artikel3(jaar=...)` for the holiday list, and `Artikel3` is a
`VersieArtikel`. Today that construction happens inside `__post_init__`, which runs **within**
`VersionedClass.__call__`'s `context_reference_date` token scope, so the nested lookup inherits
the caller's reference date.

Lazily-evaluated properties break that. `Artikel1(casus).verlenging_termijn` is read *after*
`__call__` returned and reset the token, so the nested `Artikel3` lookup falls back to
`date.today()` — silently selecting a version by wall-clock time rather than by the case. Every
delegated call in D11 has the same exposure.

The reference date must therefore travel with the case rather than with a context variable:

```python
@dataclass
class Casus:
    datum_toepassing: date | None = None
    ...

# nl/versioning.py — VersieArtikel prefers the explicit argument, falls back to the case
reference_date = datum_toepassing or (casus.datum_toepassing if casus else None)
```

This also closes the last place a version could be stated twice: `wbrv.Artikel15(casus=c)`
selects its version from `c.datum_toepassing`, and delegated articles receive the same `casus`,
so an entire evaluation is pinned to one date by construction.

`nl/versioning.py` is therefore in scope. `core/versioning.py` remains untouched.

#### Nested version selection (D13)

`wbrv.Artikel15` is a `VersieArtikel` wrapper, not a class, so `wbrv.Artikel15.Lid1.OnderdeelP`
needs the wrapper to proxy attribute access. It cannot resolve eagerly — which version's nested
class to return is unknown until a `casus` supplies the date. So the proxy returns *another
`VersieArtikel`*, mapping each date to that version's nested class, and selection still happens
at call time:

```python
def __getattr__(self, item):
    if item.startswith("_"):
        raise AttributeError(item)
    return VersieArtikel(
        f"{self._name}.{item}",
        {d: getattr(cls, item) for d, cls in self._versions.items() if hasattr(cls, item)},
    )
```

Versions lacking the attribute are skipped rather than raising, which makes D6's **class-set
growth** work by construction: a `Lid3` introduced in v2030 simply has a map starting at 2030,
and asking for it earlier raises the existing `No version from ... on ...`. Removal remains
unsupported for the reason recorded under the repeal gap.

This replaces the current hand-written pattern, where `article_15/__init__.py` builds one
`VersieArtikel` per class over the same dates. That duplication is exactly where both existing
bugs live — one map points at the wrong class, and `__all__` disagrees with what is used. Under
D13 the article declares its versions **once**:

```python
Artikel15 = VersieArtikel(name="Artikel15", versions={
    date(2025, 1, 1): v2025_01_01.Artikel15,
    date(2026, 1, 1): v2026_01_01.Artikel15,
})
```

and every nested level is derived from it. Both bugs become unrepresentable rather than fixed,
and `wbrv/__init__.py` exports one name per article instead of one per class, so `__all__` can no
longer drift out of step with what callers use.

Constraint: `atw_verlenging`'s result must be unchanged, and the delegated chain must be verified
across a cross-product of branches rather than a single path — see Verification.

## Verification

The earlier draft proposed comparing `example.py` stdout before and after. That is not an
adequate oracle: each example is a single happy path, both the inputs and the implementation get
rewritten together, and identical output would certify nothing about false branches, boundaries,
version selection, exceptions or removed members.

### Phase 0 — build the oracle first (D10)

A characterization suite written against today's flat constructors would have to be rewritten in
Phase 1, since those constructors cease to exist — which recreates the exact weakness that
disqualified the `example.py` comparison: inputs and implementation moving together, with
green tests proving only that both were changed consistently. Facts could be mapped onto the
wrong entity fields and the expected outputs would still match.

The oracle is therefore **data, not test code**:

```
tests/
  vectors/<article>.json     frozen cases: facts + reference date, implementation-independent
  golden/<article>.json      expected observations, GENERATED from the pre-change code
  adapters/old.py            builds today's flat constructors from a vector
  adapters/new.py            builds a Casus from the same vector
  test_characterization.py   runs every vector through the active adapter vs golden
  divergences.py             machine-checked allowlist of intentional differences
```

Vectors name facts in domain terms (`leeftijd`, `waarde_woning`), never in constructor terms, so
the same file feeds both adapters. Golden results are generated once against unmodified code and
**committed, never regenerated** — regenerating them is how a refactor certifies its own
regression, so the plan treats any diff to `golden/` as a review-blocking change requiring a
matching entry in `divergences.py`.

Steps, before any production file is touched, on a branch off `wbrv`:

1. Add `pytest` to a `dev` dependency group, matching `taxlation-api`, which already uses it.
2. Write the vectors, then generate and commit the golden results from the **current**
   implementation, recording what it does rather than what it should do. Coverage required:
   - every legal branch of every article, true and false;
   - boundary values — `leeftijd` at 17/18/34/35, waarde at `WAARDEGRENS` and ±1, dates either
     side of each termijn;
   - version selection at, before and after each effective date, including the `ValueError`
     when no version applies, and **each version's logic exercised independently** — per D6 a
     version is its own implementation, so passing tests for v2025 say nothing about v2026;
   - `None`/missing combinations for every nullable field;
   - repeated evaluation and re-reads of the same instance, which pins the behaviour that
     removing `__post_init__` mutation must preserve;
   - each delegated entry point invoked directly, not only through its parent;
   - **the `atw` chain as a cross-product, not a path.** The single passing route assertion
     (`2025-12-29`) covers one composition only. Required: zero and non-zero carry-in; negative
     `wettelijke_termijn` triggering the art. 1 lid 2 reset; terms below and at art. 2's
     three-day threshold; each `wettelijke_termijn_eenheid` either side of every art. 4
     `onderdeel_a` boundary (90 dagen, 12 weken, 3 maanden, 1 jaar); end dates on a Saturday, a
     Sunday, a fixed holiday, a computed holiday (Pasen, Koningsdag) and their adjacent days;
     and year boundaries where the `Artikel3` holiday lookup changes year.

   Not required: enumerating every reachable public member. That was justified by consumer
   breakage, and with no customers the removed inherited members (`Artikel15.onderdeel_p`,
   `Artikel15Lid1.startersvrijstelling`) can simply be listed in the D9 commit message.
3. Commit vectors, golden results and both adapters. The suite must be green against unmodified
   code through the old adapter.

### Phase 1 — refactor

The same vectors now run through the new adapter against the **unchanged** golden file. Every
production commit keeps that green. `golden/` is never regenerated; the only sanctioned
differences are entries in `divergences.py`, each naming the old value, the new value and the
decision that authorised it:

- the disjunctive-group validation change described above (was `False`, now raises);
- the members removed by D9.

A diff to `golden/` without a matching divergence entry fails the suite.

### Phase 2 — follow-up in `taxlation-api`

Migrate both routes and `atw_verlenging` to build a `Casus`, repair the already-failing
`Art_7_10` test, and run its suite green against this branch vendored in.
`test_beslistermijn_uses_dag_unit_and_extends_over_weekend` must still return `2025-12-29`.

**Merge gate.** This PR does not merge to `develop` or `main` until that migration is green
against this branch. Having no customers removes the need for a deprecation window; it does not
make shipping a Worker that cannot import its own library acceptable, and the already-broken
`Art_7_10` test is evidence that an informal follow-up is not a reliable control. The two PRs
need not merge in the same instant — the API PR must merely exist and pass first. Work on
`wbrv-article` itself is unaffected.

## Quarantined defects

Both are behaviour-changing legal questions, deliberately kept out of a restructuring branch so
they get proper attention rather than riding along with a refactor. Each is reproduced unchanged
and encoded as an `xfail` naming the legally correct result, so parity with a known-wrong
conclusion stays visible rather than being silently certified.

**`awb` 7:10 lid 4** — [issue #17](https://github.com/taxlation/taxlation-nl/issues/17).
`onderdeel_b` is `instemming_indiener and andere_belanghebbende_niet_geschaad`; when those are
`None` it evaluates to `None`, not `False`. The `elif onderdeel_a is False and onderdeel_b is
False and onderdeel_c is False` branch therefore almost never fires, so a requested
`termijn_verder_uitstel` is granted with no consent recorded. The open question is what an
unknown consent should mean: refuse the uitstel, or refuse to answer via `VEREIST`.

**`atw` artikel 4 onderdelen b and c** — [issue #16](https://github.com/taxlation/taxlation-nl/issues/16).
The statute excludes three categories of termijn from the ATW; `wet_geldt_niet` consults only
`onderdeel_a()`. Terms concerning bekendmaking, inwerkingtreding or buitenwerkingtreding van
wettelijke voorschriften (b) and vrijheidsbeneming (c) are therefore extended when the law does
not apply to them at all.

This one was **found by fixing the swapped `legislation.md` files**: anyone checking artikel 4's
implementation against its source was shown the feestdagen bepaling instead. It is the clearest
argument for treating legal traceability as load-bearing rather than decorative.

## Defect policy

Fixes are allowed. The rule is that no behaviour moves *silently*:

- **Behaviour-neutral cleanups** are applied inline, no ceremony. Example: `startersvrijstelling`'s
  first clause, `(A or B or C) or ((A or B or C) and aanhorigheid)`, reduces to `(A or B or C)`.
- **Documentation and traceability fixes** are applied inline. Done already: `atw` artikel 3 and
  artikel 4 had each other's `legislation.md` bodies (frontmatter was correct in both).
- **Behaviour-changing fixes** need an explicit decision, their own commit separate from the
  restructuring, and a `divergences.py` entry recording old value, new value and the authority
  for the change. Both currently known ones are quarantined; see Quarantined defects.

## Defects that disappear without being fixed

Two wiring defects in `wbrv/article_15/__init__.py` cease to exist, because the structure that
expresses them is gone:

- Line 19: `Artikel15Lid1OnderdeelP` maps `date(2025,1,1)` to `v2025_01_01.Artikel15Lid1` — the
  wrong class. Its `name=` argument is also a copy-paste leftover reading `"Artikel15Lid1"`.
- Line 23: `__all__` omits `Artikel15Lid1OnderdeelP`, although `example.py` and
  `wbrv/__init__.py` both use it.

Both come from hand-writing one version map per class. D13 removes that duplication — the article
declares its versions once and nested levels derive from it — so neither is expressible
afterwards. This is the *absence* of the wiring, not a correction applied to it.

**No golden diff results.** In v2025's file `Artikel15Lid1` inherits from
`Artikel15Lid1OnderdeelP`, so the wrong mapping still returns an object whose
`startersvrijstelling()` gives the identical value. The defect is in which class you receive, not
in the legal answer. Since vectors record legal outcomes rather than class identity, the golden
results are unchanged and no `divergences.py` entry is required.

Preserving the defect deliberately would mean writing a knowingly incorrect map — adding a bug
rather than declining to fix one — so it is not offered as an option.

Noted but left alone, being behaviour-neutral: `startersvrijstelling`'s first clause,
`(A or B or C) or ((A or B or C) and aanhorigheid)`, reduces to `(A or B or C)`.

## Conventions established

- Articles that evaluate a case take `casus`. Purely definitional articles keep their own
  parameters — `atw` article 3 computes public holidays from `jaar: int`, a calendar function
  rather than a question about a case. Wrapping it in `Casus` would add indirection and share
  nothing.
- Entities are named after the real-world thing they describe, never after a law or an article.
- Facts only. Derived results never enter `Casus`.
- Prefer more small entities over fewer large ones; split or nest past ~15 fields.
- One field, one legal concept, with its definition and source in the comment. Reusing a field
  across laws asserts they mean the same thing.

## Deferred

**Cross-article inputs stay facts, except where `atw` forces otherwise.** The `atw` chain is now
article-to-article delegation (D11) — that entry's warning that it might force the question
early proved correct. The remaining cases stay facts for now: `awb` 6:7 needs
`datum_aanvang_indieningstermijn`, which is 6:8's output, and `wbrv` article 1 needs
`overdrachtsbelasting`, which is article 2's output. They are kept on `Bezwaar` and
`Belastingmiddel` with the seam marked.

The distinction is deliberate rather than arbitrary: in `atw`, the composition order is stated by
the legislation itself (art. 4 disapplies arts. 1–3), so encoding it in the articles is
recording the law. For 6:7 and 6:8 the chaining is currently the *caller's* choice, and
promoting it to delegation would assert a legal relationship this design has not verified.
Adopt it there only after confirming the statute composes them that way.

**Collections in `Casus`.** See Cardinality above for the limitation and its revisit trigger.

**`atw` and `awb` entity cuts** are proposed here but not legally reviewed. The split of the four
`verklaring`/history facts across `Verkrijger` and `Hoofdverblijf` — history *of the person*
versus intent *about the woning* — is the one most worth a second look.

## Out of scope

- The two quarantined legal defects (issues #16 and #17). Fixes are permitted in general, per
  Defect policy; these two are held back deliberately so the legal decisions get their own
  attention instead of riding along with a refactor.
- Article-to-article delegation beyond what the `atw` chain forces (D11).
- Any change to `taxlation/core/versioning.py`, including the repeal gap recorded above.
  `nl/versioning.py` **is** in scope, for the `Casus.datum_toepassing` fallback (D12).
- Modelling `Casus` cardinality.
- Lazy or three-valued predicate evaluation — see "Validation is eager".

## Review history

**2026-08-09 — Codex adversarial review, verdict `needs-attention`, 4 high findings.** All four
accepted; three changed decisions and one was confirmed as larger than reported.

| Finding | Resolution |
|---|---|
| `VEREIST` derived from legacy defaults lets incomplete disjunctions become a legal `False` | D5 rewritten: membership derived from the legal predicate, disjunctive groups added, divergence from current behaviour made explicit and tested |
| Single entity slots cannot encode multi-entity cases the design itself admits | D7 kept but downgraded — scoped to the ten articles, with the limitation and a revisit trigger documented rather than the contract generalised |
| Call-time composition silently removes existing public behaviour | Confirmed and found to be larger: `taxlation-api` routes read `.termijn_beslissing_bezwaar` and construct with flat kwargs, and the Cloudflare build auto-vendors this repo. D9 declares the break; a lockstep API PR was required at the time, relaxed by the correction below. Verified empirically — an identical break from an earlier rename has been sitting broken in `test_beslistermijn.py` |
| `example.py` stdout comparison is not an adequate preservation oracle | Verification rewritten around a pre-change pytest characterization suite (D10), with the `awb` 7:10 defect quarantined as `xfail` instead of silently preserved |

**2026-08-09 — corrections from the author, after the review.**

- *The API has no customers.* D9's lockstep requirement is relaxed to a follow-up PR, and the
  characterization suite no longer enumerates every reachable public member. The finding itself
  stands: the break is real and `taxlation-api` still has to be migrated, just not
  simultaneously.
- *Versions can differ in logic, not only in constants.* D6 rewritten. Version directories are
  independent implementations with no cross-version inheritance, the class set may vary per
  version, and per-version logic must be tested independently. This also surfaced the repeal gap
  in `core/versioning.py` recorded under Versioning.

**2026-08-09 — Codex adversarial review, round 2, verdict `needs-attention`, 3 high + 2 medium.**
Four accepted, one accepted in part.

| Finding | Resolution |
|---|---|
| D5 omits `waarde_aanhorigheden`, and flat validation over-requires conjuncts | Accepted in part. The omission was a real defect and is fixed by a stated optionality rule: `None` means unknown and belongs in `VEREIST`; a law-supplied default (`waarde_aanhorigheden = 0`) does not, and must justify itself in a comment. The over-requiring is **rejected as a change and adopted as a documented trade-off** — lazy/three-valued evaluation makes the error surface depend on the order conjuncts are written, and reintroduces the three-valued model already rejected. Revisit trigger recorded. |
| The `atw` accumulation contract was never chosen | Accepted. D11 chooses it: article-to-article delegation, justified against the four carry-in-sensitive behaviours read out of the source. "Sum the per-article extensions" is shown to be unable to express the two resets. Verification now requires a cross-product rather than the single `2025-12-29` path. |
| D9 lets the incompatible library deploy before its consumer migrates | Accepted. A green `taxlation-api` migration is now a merge gate for `develop`/`main`. Not simultaneous merge — the API PR must exist and pass first. |
| D6 claims class removal works while `VersionedClass` perpetuates it | Accepted. D6 narrowed: the class set may grow; removal is unsupported until repeal semantics exist, rather than modelled by omission. |
| D10 has no stable old-to-new comparison harness | Accepted. The oracle becomes data rather than test code: frozen implementation-independent vectors, golden results generated once from pre-change code and never regenerated, separate old/new adapters, and a machine-checked divergence allowlist. |

**2026-08-09 — Jelle Wallenburg's counter-proposal, adopted in part.**

Jelle proposed expressing the article tree as nested class namespaces
(`Artikel15.Lid1.OnderdeelP`), with each level composed of the one below. Three things it does
better than the flat-sibling structure this spec had, all adopted as D2 and D13:

- the dotted path is the legal citation, where `Artikel15Lid1OnderdeelP` was a mangled
  identifier needing translation back into a reference;
- law-order reading comes from nesting itself, rather than from an argument about when names
  resolve — a simpler mechanism defended by a simpler claim;
- one version map per article instead of one per class, which is what makes both
  `article_15/__init__.py` bugs unrepresentable.

Jelle raised two costs of his own sketch: having to declare the `onderdeel_p` attribute after the
nested dataclass and shape `vrijstelling()`, and the indentation. The first is an artifact of
composition and does not arise here — every level holds only `casus: Casus`, so `onderdeel_p` is
a two-line delegating property with no field to declare or keep in sync. The second is real and
recorded under Article classes with measured figures; it is smaller than in his version, because
the fact declarations that dominate the file do not nest.

Not adopted: his composition, where a level holds the level below and facts live on the leaf.
That would leave `atw` 1, 2 and 4 each redeclaring the same three fields — the duplication
`Casus` exists to remove — and it makes the caller assemble the article's internal shape. Levels
therefore hold `casus` and delegate by passing it. His sketch also left `Artikel15` fieldless
with no entry point; under D4 every level takes `casus` and is callable.

Mechanics verified before adopting: full chain, both standalone levels, and nested version
selection through the `__getattr__` proxy all behave correctly.

**Discovered while resolving D11:** lazily-evaluated properties break nested version selection.
`Artikel1.lid_1` constructs `Artikel3` inside `__post_init__` today, within
`context_reference_date`'s token scope; as a property it would run after the token resets and
silently fall back to `date.today()`. D12 (`Casus.datum_toepassing`) fixes this and brings
`nl/versioning.py` into scope.
