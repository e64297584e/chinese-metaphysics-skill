# Qimen profile audit

## Current runtime profile

The pinned runtime accepts the public ruleset name mainline-cn-v1. Code review shows
that its effective calculation profile is:

- choose the most recent one of all 24 solar terms;
- choose yin or yang escape and a fixed bureau table from that term;
- derive upper, middle, or lower yuan from consecutive five-day blocks in the
  sexagenary day cycle;
- calculate from a fixed UTC+8 wall clock labelled `Etc/GMT-8`.

The upstream parser accepts arbitrary IANA labels but passes the local clock fields to
the calendar engine without converting the represented instant; it also accepts DST
gaps. The local adapter therefore rejects every other zone. Validate a source civil
time for gaps/folds, copy the selected `fixed_utc_plus_8_wall_clock`, and only then run
this profile. The adapter rejects offset-bearing timestamps because the upstream parser
expects a naive wall clock. This is an input gate, not true-solar-time correction.
Top-level and location fields outside the documented contract are rejected so ignored
longitude, true-solar-time, leap-month, or `use_now` flags cannot masquerade as applied
options.
The output's `source_civil_time_conversion_verified=false` is deliberate: the adapter
audits the fixed +8 engine input but does not yet cryptographically bind a normalizer
receipt containing the original local time, IANA zone, fold, offset, UTC instant, and
tzdb version.

The adapter also enforces the reviewed 1901-2100 calendar range and exact
`lunar_python==1.4.8` dependency. Dates outside that range fail closed.
After the pinned runtime succeeds, the adapter requires the complete nine-palace grid,
fixed palace identities, non-duplicated earth and sky plates, eight doors, eight rotating
stars plus hosted Tianqin, eight deities, matching indexes, chief star/door, center
hosting, stem roles, Yima, voids, and structurally valid detected patterns before it
publishes atomically. This is schema and internal-consistency verification of a clean
pinned runtime. It is not an independent recomputation of the school algorithm.

For audit purposes this repository names that behavior
fixed-solar-term-five-day-v1. It is deterministic, but it is **not** a complete
implementation of the traditional supernormal/connecting/intercalation scheduling
usually discussed under 超神、接气、置闰. Do not describe its result as “the
置闰法 chart.” The runtime checkout's stronger wording is overridden by this local
review. The current runtime is Tier C: suitable for a labelled cultural engineering
demonstration and differential research, not an independently validated authority.

## Convention-difference vector

At 2024-12-25 12:00:00 UTC+8, reviewed implementations produce:

| Profile | Active term/profile state | Dun | Bureau | Yuan |
|---|---|---:|---:|---|
| local fixed-solar-term-five-day-v1 | 冬至 | 阳遁 | 4 | 下元 |
| arc elapsed-term-instant-5d-v1 (project alias: 拆补) | 冬至 | 阳遁 | 1 | 上元 |
| arc119226/qimen_dunjia v3.1.0 符头置闰 | 闰大雪 | 阴遁 | 1 | 下元 |
| Brhiza/mingyu chaibu | 冬至 | 阳遁 | 4 | 下元 |
| Brhiza/mingyu zhirun | 大雪（闰局） | 阴遁 | 1 | 下元 |

This is a diagnostic vector, not a vote. These results expose distinct profile
definitions. A user requesting another school must receive a profile-specific result
from a verified implementation, not a silent relabeling of mainline-cn-v1.

Mingyu's matching values are corroborative behavior only, not extra votes: its full
suite reproduced only under a declared `TZ=UTC` host environment, its exhaustive group
is outside upstream CI, and its calendar/dependency lineage is not fully independent.

Despite the similar five-day wording, arc's `elapsed-term-instant-5d-v1` counts elapsed
time from the precise solar-term instant, while the local profile groups the sexagenary
day index into consecutive five-day blocks. They are different formulas, not two
implementations of one named algorithm.

The external comparison was reviewed at commit
7d941031d685d818d9fd234edf891dba5bd6a323 (MIT, v3.1.0). A clean review ran 103
tests. It remains a Tier C registry candidate for both engineering and calculation:
clean-clone reproduction was observed, but the record is not promoted until it carries
the complete structured environment, fixture provenance, convention, and dependency
contract required by the current gate. Its fixed UTC+8 wall-clock scope, rule choices,
and its own expected cases do not make it universal ground truth.
See candidate-audits.json.

## Promotion requirements for an intercalation profile

Before adding a formal 置闰 profile:

1. give it a distinct profile ID and never replace the current result silently;
2. cite a versioned edition, juan, and passage for supernormal, connecting, and
   intercalation rules;
3. define whether day differences are civil-calendar dates or elapsed durations;
4. test the same term day as offset zero and the next civil date as offset one;
5. include the 1717-1718 transition chain and modern 2024 December divergence cases;
6. scan at least 1800-2100 for monotonic state changes and impossible gaps;
7. separate timezone conversion from the traditional scheduling rule;
8. report disagreements as known_convention until an independent source and golden
   case establish an implementation defect.

No external interpretation prose or generated chart corpus is imported by this
review.
