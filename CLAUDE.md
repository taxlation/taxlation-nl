# CLAUDE.md — taxlation-nl

Pure-Python translation of Dutch law ("law-as-code"), packaged as `taxlation` (import root `taxlation.nl`). Managed with **uv**. Consumed by `taxlation-api` two ways: as a uv git dependency (local dev / Docker / tests) and as **vendored source files** on the Cloudflare Python Worker (its build clones this repo's matching branch and copies `src/taxlation/` in — develop feeds the dev Worker, main feeds prod, picked up on the next taxlation-api build).

## Layout

```
src/taxlation/nl/<law>/<articleN>/vYYYY_MM_DD/{translation.py, legislation.md, README.md}
```

One `@dataclass` per article version (e.g. `Artikel3`), fields/methods use the Dutch legal terms, method names follow the article's subdivisions (`lid_1` = paragraph 1). The article package `__init__.py` re-exports the current version; see an existing article for the pattern. Keep faithful law translations here; orchestration/extension logic belongs in taxlation-api's `services/`.

## Gotchas

- **New third-party import = TWO pyproject entries.** Declare it in `[project.dependencies]` here (so `uv` installs of this package work) **and** in taxlation-api's `[project.dependencies]` (only that list is vendored into the Worker bundle — this repo reaches the Worker as source files, so its declared deps are invisible to pywrangler). Missing the api entry fails the api deploy at validation with `ModuleNotFoundError` (see the 2026-07-11 `holidays` break).
- **Everything must run on Pyodide** (Cloudflare Python Workers): pure-Python dependencies only, unless Pyodide ships a wheel for it.
- `main` feeds the prod Worker — keep it stable; land work on `develop` first.
