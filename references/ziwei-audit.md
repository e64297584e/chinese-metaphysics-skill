# Ziwei external audit profile

Use this profile only to compare implementations or inspect a downloaded annual dataset slice. It does not establish metaphysical claims as empirical facts.

## Pinned snapshots

| Item | Pin | Role |
|---|---|---|
| Public repository | `Renhuai123/ziwei-doushu@0e39b5c9a17e707291f20ef3cc125b3e885351d4` | v4 release-era comparison engine |
| Release | `v4.0-13d` (2026-10-15) | annual JSONL snapshots |
| Release manifest SHA-256 | `770c64da335edfe01f9ca6a7536cc083e416a1b481782c662b6b1dcebf4fa866` | integrity anchor |
| Current repository audited | `1059c347231c636bd86ddb78fd8ed430d5de8d2a` (2026-10-22) | later fixes; not byte-compatible with v4 |
| Licence evidence | current commit above; hashes in `upstreams.json` | v4 terms were added after the release commit |

Classification: **external observation / evidence tier C**. Agreement can reveal regressions. It cannot determine which convention is historically correct.

## What was verified

- The release manifest contains 674,976 charts: every real Gregorian day from 1950 through 2026, 12 double-hour indexes, and two genders. Thirteen topics produce 8,774,688 topic texts.
- The 77 annual zstd files total 161,407,000 bytes; the manifest declares 56,577,041,818 raw bytes. The arithmetic and published asset sizes are internally consistent.
- `year-1991.jsonl.zst` matched the manifest SHA-256 `f9be380cd5e82d053bd031d3cca5bd708b9702a6dd5da967a5b10e0433f68384`. A full streaming audit found 8,760 unique keys, 365 real dates, balanced genders and hours, and all 13 topic fields.
- The same 1991 slice had 7,878 distinct whole-content hashes among 8,760 records. Across 113,880 topic texts, 62,588 topic-specific hashes were distinct (54.96%). Only 63,828 of 3,822,806 normalized paragraphs were distinct (1.67%). Treat random row splits as severe leakage.
- Every 1991 record contained at least one `倪师` / `倪海厦` / `《天纪》` marker; 111,037 of 113,880 topic texts contained one. Marker presence is not proof that every occurrence is an infringing quotation, but it shows that the licence exclusion is systematic rather than marginal.
- The public regression suite passed when invoked without the sandbox-incompatible `tsx` IPC wrapper. It checks useful invariants and boundaries, but most oracles are internal tables rather than independent sourced charts.

## Reproducibility limits

- The manifest names private site engine commit `c25dd495` and content version `ca268829f7a9`. Neither is present in the public repository.
- The public `lib/ziwei/db-analysis.ts` is a placeholder. The interpretation rule base and dataset generator are not published, so the 13-topic output cannot be regenerated end to end.
- v4 stores only `k/y/m/d/h/g/ms/t/c`; `ms` is the first major star in the life palace or null. It does not contain the complete twelve-palace chart, all star positions, brightness, or transformations.
- v4 directly uses an hour-branch index and has no birth minute, location, timezone, longitude, historical civil-time conversion, or true-solar-time correction.
- v4 was generated with the older `XD2` brightness default. Five days later the public engine changed its default to `QS`; brightness wording and dependent interpretations can differ.
- The public engine includes time-varying `currentAge` and current-major-period flags. Exclude them from deterministic snapshots unless an explicit evaluation date is supplied.

## Known rule differences

For `1991-06-15 15:18`, male, both engines agree on the lunar date, life/body palaces, five-element bureau, life/body rulers, 14 major stars, natal transformations, and 32 of 34 shared star positions.

| Surface | Primary `ziwei-sanhe-v1` | External `renhuai-v4-xd2-no-location` | Treatment |
|---|---|---|---|
| 辛年天魁/天钺 | 魁午、钺寅 | 魁寅、钺午 | known convention difference; never auto-correct |
| 大限四化 | re-fly by major-period palace stem | natal transformations fixed; palace activation only | incompatible school profiles |
| Star scope | 34 stars | 70 stars in the checked chart | external-only stars are coverage leads, not accepted facts |
| Brightness labels | includes `得地` / `落陷` | normalized `得` / `陷`, profile-dependent | normalize vocabulary, then compare only like-for-like profiles |

The external source adds 36 stars in the checked chart, including 三台、八座、恩光、天贵、孤辰、寡宿、龙池、凤阁、旬空 and 截空. Add them only after recording a rule ID, school, traceable source, implementation, and independent tests.

## Comparison contract

1. Pin the repository commit, dependency lock, release tag, and rule profile.
2. Normalize Gregorian date, hour branch `0..11`, gender, late-Zi rule, leap-month rule, timezone, and location before comparison.
3. Compare deterministic structure first: lunar date, life/body palaces, five-element bureau, 14 major stars, transformations, then explicitly selected auxiliary stars.
4. Classify each difference as `agreement`, `known_convention`, `local_missing_coverage`, or `unexpected_difference`.
5. Never overwrite a local rule from one external mismatch. Require a traceable source and an independent case before changing code.
6. Stratify cases across ten stems, twelve branches/hours, both genders, lunar-new-year boundaries, leap-month days 15/16, late Zi, historical daylight-saving dates, and longitude-sensitive times.
7. Do not use the interpretation text for training or evaluation. Build structural regression cases from independently sourced rules and group them by chart structure rather than random dataset rows.

## Data and rights handling

- Code: root MIT licence, subject to its notice and third-party dependency notices.
- Release data: publisher labels it CC BY 4.0, which requires attribution, a licence link, and indication of changes.
- Embedded *Tian Ji* quotations: explicitly excluded from the dataset licence. The separate corpus says the original course copyright belongs to Ni Haixia and successors; no verified rights-chain document was found in the audited repository.
- The ignored runtime checkout contains the public tree for code review. Do not persist, vendor, commit, quote, index for retrieval, or use `c`, `docs/tianji-ziwei`, `lib/nihai`, or `lib/classics` in this skill, training, evaluation, RAG, or responses. The only permitted text access is the auditor's transient, non-exporting aggregate scan described below.
- A future text release is eligible for reconsideration only if it removes third-party quotations, documents provenance and rights, publishes the generator/rule version, and passes duplication and leakage review.

## Commands

Fetch the optional public comparison source only when needed:

```bash
python3 scripts/bootstrap_upstreams.py --include-audit --install-deps
python3 scripts/doctor.py --include-audit
```

Audit a separately downloaded annual file without emitting its text. Keep it under the ignored `tmp/` tree, verify the manifest-derived hash before decompression, and retain the default resource limits:

```bash
python3 scripts/audit_ziwei_dataset.py tmp/ziwei-audit/year-1991.jsonl.zst \
  --expected-year 1991 \
  --expected-sha256 f9be380cd5e82d053bd031d3cca5bd708b9702a6dd5da967a5b10e0433f68384
```

Add `--scan-text` only for a transient aggregate duplication and rights-marker audit. It emits counts and ratios, never source text or individual text hashes; do not persist its in-memory index, commit the dataset, or create derived text.

The auditor accepts only regular files, copies bounded input into an unlinked temporary snapshot, and parses the same bytes it hashes. It rejects compressed input without a manifest-derived SHA-256 and stops before decompression on a mismatch. Defaults cap compressed input at 64 MiB, decompressed UTF-8 at 1 GiB, each JSONL record at 1 MiB, input at 10,000 lines, and retained distinct text hashes at 1,000,000. Tighten these limits for smaller slices; do not raise them merely to make an unexpected file pass.
