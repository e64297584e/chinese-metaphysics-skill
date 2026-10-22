# Ziwei runtime profile audit

## Decision

The default Ziwei calculator is a **Tier C, named cultural/engineering profile**. It is
useful for deterministic reproduction, regression discovery, and convention-aware
comparison. It is not an authority, a consensus chart across schools, or an independently
validated implementation.

Runtime identity:

- repository: `FANzR-arch/Numerologist_skills`;
- component: `ziwei-doushu`;
- commit: `53ab46e7856e8e07a8de8ea96a2d93ed6694bedf`;
- declared ruleset: `ziwei-sanhe-v1`;
- local effective profile: `fixed-civil-date-sanhe-v1`;
- calendar dependency: exactly `lunar-python==1.4.8`;
- reviewed input range: 1901-2100.

The pinned repository did not contain an explicit licence at review time. Its code,
prompts, examples, tables, and interpretation text are therefore fetched at runtime only
and are not copied into this repository. A clean exact-commit check is required before
execution.

## What the local adapter verifies

The adapter accepts only a strict JSON contract:

- `ruleset` must be `ziwei-sanhe-v1`;
- `calendar_type` must be `solar` or `lunar`;
- `birth_time` must use the strict `YYYY-MM-DD HH:MM` grammar; its date is interpreted
  under `calendar_type`, while its clock is naive;
- `gender` must be explicitly `男` or `女`;
- `is_leap_month` must be a Boolean and must be false for solar input;
- `late_zi_rule` must be `next_day` or `same_day`;
- `leap_month_rule` must be `current`, `next`, or `split_15`;
- an optional `query_year` must also lie within 1901-2100;
- unknown fields are rejected instead of being silently ignored.

After the pinned calculator succeeds, the adapter checks that normalized inputs still
match the request, both convention choices remain explicit, the normalized civil date is
within range, and lunar calendar metadata matches a fresh conversion through the pinned
calendar dependency. It also requires all twelve palaces, 34 tracked star placements,
four natal transformations, contiguous decadal spans, a complete annual overlay when
requested, and the fourteen-major-star self-check. Only then does it attach
`profile_review` and atomically publish the result.

These checks establish input binding, calendar-field agreement, schema completeness,
and internal consistency for a clean pinned runtime. They do not independently
recompute all school rules. A coordinated but internally consistent change to a bureau,
star position, or transformation would require an independent engine or sourced golden
to detect; `profile_review.school_algorithm_recomputed_independently=false` records that
boundary explicitly.

## Time basis and precision limit

This engine does **not** convert IANA timezones, historical daylight-saving time,
longitude, equation of time, or true solar time. Solar input combines a caller-provided
civil date with a naive wall clock; lunar input combines a caller-provided lunar date
with that naive clock and converts only the calendar date. Adding a place, timezone, UTC
offset, or longitude would not make the calculation geographically corrected, so the
adapter rejects such extra fields.

Minute input does not establish minute-level star precision. It selects one traditional
two-hour branch and supports a warning near branch boundaries. For overseas, historical,
or disputed time inputs, validate the civil instant separately, retain that conversion
record, and compare adjacent branches when uncertainty can cross a boundary.

## Evidence limits

The runtime's own test suite and internal self-check support reproducibility only. The
optional `Renhuai123/ziwei-doushu` audit snapshot is also Tier C and shares important
algorithmic lineage through common libraries or tables, so agreement between the two is
not independent proof. This repository currently has no authoritative second engine and
no adequately sourced multi-profile golden set for Ziwei.

Consequently:

- report output as the result of the exact named profile;
- classify external differences by convention before calling them defects;
- never claim that this is the unique correct chart for all schools;
- do not promote interpretations, personality claims, or forecasts from deterministic
  calculation output;
- do not use unlicensed upstream prose for responses, training, RAG, or redistribution.

## Promotion requirements

Promotion above Tier C would require, at minimum, an explicit algorithm contract, legally
usable rule provenance, independent fixture producers, convention-separated boundary
goldens, exact dependency lineage, and successful differential review against an
independent implementation. Repository popularity, test count, or agreement with a
shared-lineage engine is insufficient.
