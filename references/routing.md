# Routing and calculator contracts

## Contents

1. Bazi
2. Qimen Dunjia
3. Ziwei Doushu
4. Feng Shui
5. Cross-system comparison

## Bazi

Required: solar or lunar date, sex. Strongly preferred: exact clock time and birthplace.

```bash
python3 scripts/run_module.py bazi -- \
  --solar 1991-06-15 --hour 15:18 --sex 男 --place 安徽阜阳
```

Available options are shown by:

```bash
python3 scripts/run_module.py bazi -- --help
```

Record whether the input was solar or lunar, whether a leap month was used, the birth-time precision, and the day-boundary convention shown by the calculator.

The bundled calculator interprets input as a fixed UTC+8 standard wall clock; it does
not apply 1986-1991 China DST. The place option does not perform timezone, DST,
longitude, or true-solar-time conversion. Do not pass an
overseas local wall clock through unchanged. For non-China civil time, historical DST,
pre-1949 time, or a requested solar-time correction, record the IANA zone and actual
offset, use a separately verified conversion profile, and show sensitivity when the
corrected time could cross a day, solar term, or two-hour branch boundary.

Validate a supplied local wall time before conversion:

    python3 scripts/normalize_civil_time.py --local "1990-09-16 01:30" --timezone Asia/Shanghai

The command fails closed on a nonexistent time and requires fold 0 or 1 for a repeated
time. Its `utc`, `asia_shanghai`, and `fixed_utc_plus_8` values identify an instant only;
`fixed_utc_plus_8_wall_clock` is the offset-free string accepted by the Qimen adapter.
None of these fields chooses a day-boundary school or performs true-solar-time correction.

## Qimen Dunjia

Required: one concrete event, judgment goal, relevant time, original country/city/IANA
timezone, and the `mainline-cn-v1` ruleset. First validate the original local clock with
`normalize_civil_time.py`. Then copy the selected candidate's
`fixed_utc_plus_8_wall_clock` into `time_input` and set the calculator timezone to
`Etc/GMT-8`. Do not send an
overseas IANA wall clock directly: the pinned engine attaches a zone label but does not
convert the instant before calendar calculation, so the adapter rejects it.
Do not add undocumented fields such as longitude, `true_solar_time`, `use_now`, or
`is_leap_month`; the strict adapter rejects fields that the engine would silently ignore.

`profile_review` verifies only the fixed-UTC+8 input actually received by the engine.
Until a signed/versioned normalization receipt is added, it does **not** prove that a
manually copied overseas local time, fold choice, or prior IANA conversion was correct;
retain the normalizer JSON beside any result that depends on that conversion.
The reviewed runtime range is 1901-2100. Outside dates are unsupported rather than
silently extrapolated from a calendar engine with no matching authority coverage.

```json
{
  "question_type": "career",
  "question_goal": "Should I sign this week?",
  "time_input": "2026-10-19 15:30",
  "calendar_type": "solar",
  "location": {
    "country": "China",
    "city": "Shanghai",
    "timezone": "Etc/GMT-8"
  },
  "ruleset": "mainline-cn-v1"
}
```

Read `normalized_input`, `calendar`, `ganzhi`, `chart`, and `warnings`. Use the chart's indexes and detected patterns; do not reconstruct missing values from memory.
Also read profile_review. The effective local profile is
fixed-solar-term-five-day-v1, not a full traditional 置闰 scheduler. If the user asks
for 拆补、符头置闰 or another school, use a separately named and verified profile or
state that it is unsupported; profile names alone are insufficient without the
algorithm contract.

## Ziwei Doushu

Required: calendar type, birth date and time, sex. Optional: query year. Confirm leap-month and late-Zi-hour rules when relevant.

```json
{
  "calendar_type": "solar",
  "birth_time": "1991-06-15 15:18",
  "is_leap_month": false,
  "gender": "男",
  "late_zi_rule": "next_day",
  "leap_month_rule": "split_15",
  "query_year": 2026,
  "ruleset": "ziwei-sanhe-v1"
}
```

All convention fields are mandatory; `birth_time` uses strict `YYYY-MM-DD HH:MM`
syntax, with the date interpreted under `calendar_type` and a naive wall clock. The
reviewed range is 1901-2100. The adapter rejects unknown
fields, including place, timezone, UTC offset, and longitude, because the pinned engine
would otherwise ignore them. Validate ambiguous/nonexistent historical civil times
outside the engine, state whether the supplied wall clock is local civil, fixed UTC+8,
or another explicitly chosen convention, and retain that conversion record. Do not
claim historical DST, geographic, or true-solar-time correction.

Read `profile_review`, `normalized_input`, `calendar`, `ruleset`, `chart`, `horoscope`,
and `warnings`. The local runtime is a Tier C `fixed-civil-date-sanhe-v1` engineering
profile, not an independently validated chart or a universal school standard. Keep
natal, decadal, and annual transformations distinct. Read `ziwei-runtime-audit.md`
before describing its scope.

When comparing another engine or dataset, read `ziwei-audit.md` first. Record both profile IDs and compare only fields supported by both sides. Report each mismatch as `known_convention`, `local_missing_coverage`, or `unexpected_difference`; never call an external implementation a gold standard solely because it has more stars or more generated rows. Exclude current-age fields unless the evaluation date is fixed.

## Feng Shui

For a layout analysis collect:

- compass-measured sitting/facing direction and measurement method;
- construction, major renovation, or move-in period;
- floor plan or a room-by-room description with doors, windows, kitchen, bathroom, beds, and desks;
- exterior roads, neighboring buildings, terrain, water, light, noise, moisture, and ventilation;
- occupants and the exact concern.

Minimize sensitive data: prefer city or climate region, anonymized bearings, and a
redacted plan. Ask the user to remove exact address, unit number, names, QR codes,
security details, and image EXIF. Do not publish a household case or detailed entry
routes.

For date selection collect the event type, date range, city/timezone, and the relevant participants' birth years. Mark the result as traditional date-selection guidance, not a guarantee.
The current fetched Feng Shui snapshot is not an approved calculation source; read
fengshui-audit.md for its blocked tables and known errors. Medical care, contracts,
permits, weather, and construction safety cannot be delayed by a symbolic date label.

## Cross-system comparison

Run each system independently. Present a table with: system, input time, convention, computed signal, interpretation, confidence limit. Treat a conflict first as a possible input or convention mismatch; do not force consensus.
