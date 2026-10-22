# Source and license record

## Included source

- `modules/bazi` is derived from `jinchenma94/bazi-skill` at commit `112a5d84cd1a001a0038cafca3be68d93e4c0cc9`.
- That repository declares the MIT License. Preserve `modules/bazi/LICENSE` and its copyright notice.

## Runtime-fetched source

- `FANzR-arch/Numerologist_skills` is pinned at commit `53ab46e7856e8e07a8de8ea96a2d93ed6694bedf`.
- `voidforall/fengshui.skill` is pinned at commit `91762ccda4ea106260ff43f336df14adf08ae57d`.
- Neither reviewed repository contained a license file at the pinned commit. Do not copy their code, prompts, examples, or reference text into this repository without the copyright holder's permission or a later explicit license.
- `scripts/bootstrap_upstreams.py` fetches those repositories into the ignored `.upstream/` directory for local use and verifies the exact commit. This repository distributes only the adapter and source metadata.
- The Qimen snapshot's mainline-cn-v1 label overstates its scheduling coverage. The
  effective profile and a three-way divergence vector are recorded in
  qimen-profile-audit.md.
- The Ziwei snapshot is exposed only through a strict Tier C profile gate. It has no
  timezone, historical DST, longitude, or true-solar-time correction and has not been
  independently validated; read ziwei-runtime-audit.md before using it.
- The Feng Shui snapshot has confirmed annual-star, flight-rule, life-gua,
  date-selection, and provenance defects. Its affected sections and invented lineage
  persona are blocked by fengshui-audit.md.

## Optional external audit source

- `Renhuai123/ziwei-doushu` release `v4.0-13d` is pinned at public commit `0e39b5c9a17e707291f20ef3cc125b3e885351d4` as `ziwei-doushu-audit`.
- It is an **audit-only comparison implementation**, not a primary calculator, authority, or source of truth. It is skipped unless bootstrap is run with `--include-audit`.
- The repository's root code is MIT-licensed. Its release data is labelled CC BY 4.0, but that licence explicitly excludes embedded quotations from Ni Haixia's *Tian Ji*. The `docs/tianji-ziwei` material is separately labelled CC BY-NC-SA 4.0 while acknowledging that the underlying course copyright belongs to Ni Haixia and his successors.
- The ignored runtime checkout contains its full public tree for code review. Do not persist, vendor, commit, quote, index for retrieval, or use its interpretation text, `docs/tianji-ziwei`, `lib/nihai`, or `lib/classics` in this skill, training, evaluation, RAG, or responses. A transient non-exporting aggregate audit is the sole text-access exception. The files presented as classical text contain modern paraphrase and must not be cited as primary editions.
- The v4 data terms and quotation exclusion were added after the release commit. Their evidence is therefore pinned separately to repository commit `1059c347231c636bd86ddb78fd8ed430d5de8d2a`, with both licence-file hashes recorded in `upstreams.json`; the release page is also part of the review record.
- Code comparisons may inspect normalized chart fields only. Preserve the upstream MIT notice before copying any substantial code; prefer independent implementation from traceable rules.
- Read `references/ziwei-audit.md` before using this source or its v4 dataset.

## Calendar dependency and validation authorities

- `lunar_python==1.4.8` is an MIT-licensed runtime dependency used for lunar-date conversion and exact solar-term boundaries. It is not treated as an authority by itself; version pinning only makes calculations reproducible.
- The reviewed upstream revision for lunar_python 1.4.8 is
  000c8a3d74eed098d6256a28fdd51b869324c559. Its passing upstream tests support
  reproducibility, not normative authority.
- Modern calendar rules follow `GB/T 33661-2017 农历的编算和颁行`, published through
  China's national standards system with Purple Mountain Observatory/CAS technical
  participation; do not misattribute the issuing authority to CAS alone.
- Public Gregorian-lunar conversion goldens within 1901–2100 use Hong Kong Observatory
  tables. The registry also contains a GB/T sexagenary-day anchor and a PMO 2026
  solar-term minute. Dates explicitly marked by HKO as uncertain remain warning cases,
  not false-precision goldens.

## Evidence registries

- evidence-policy.md defines tiers, rights gates, dependency-lineage checks, and
  evaluation layers.
- authority-sources.json records official standards, observatory tables, tzdb,
  ephemeris inputs, and versioned classical editions with permitted and blocked uses.
- candidate-audits.json records the exact commits, rights, reproducibility,
  independence, and decisions for public projects found through X and repository
  tracing. It is a review ledger, not a vendoring list.
- calendar-goldens.json can distinguish historical issued calendars from proleptic
  modern calculation; the current 12-case set contains only modern-profile cases. It
  requires jurisdiction, timezone, time scale, precision, uncertainty, system scope,
  source linkage, and an executable-or-manual route on every case.
- Run python3 scripts/validate_evidence.py after changing any registry. The doctor runs
  the same gate.

## Review rule

Before updating a pin, inspect the new tree, licence scopes, dependencies, portable
fixtures, and tests. Record the new commit, run the upstream suites and this
repository's validators, and preserve the source lineage. Never promote an audit-only
source because implementations agree, a repository has many stars, or one engine
generated a large corpus.
