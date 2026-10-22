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

## Qimen Dunjia

Required: one concrete event, judgment goal, relevant time, country/city/timezone, and the `mainline-cn-v1` ruleset.

```json
{
  "question_type": "career",
  "question_goal": "Should I sign this week?",
  "time_input": "2026-10-19 15:30",
  "calendar_type": "solar",
  "location": {
    "country": "China",
    "city": "Shanghai",
    "timezone": "Asia/Shanghai"
  },
  "ruleset": "mainline-cn-v1"
}
```

Read `normalized_input`, `calendar`, `ganzhi`, `chart`, and `warnings`. Use the chart's indexes and detected patterns; do not reconstruct missing values from memory.

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
  "query_year": 2026
}
```

Read `normalized_input`, `calendar`, `ruleset`, `chart`, `horoscope`, and `warnings`. Keep natal, decadal, and annual transformations distinct.

When comparing another engine or dataset, read `ziwei-audit.md` first. Record both profile IDs and compare only fields supported by both sides. Report each mismatch as `known_convention`, `local_missing_coverage`, or `unexpected_difference`; never call an external implementation a gold standard solely because it has more stars or more generated rows. Exclude current-age fields unless the evaluation date is fixed.

## Feng Shui

For a layout analysis collect:

- compass-measured sitting/facing direction and measurement method;
- construction, major renovation, or move-in period;
- floor plan or a room-by-room description with doors, windows, kitchen, bathroom, beds, and desks;
- exterior roads, neighboring buildings, terrain, water, light, noise, moisture, and ventilation;
- occupants and the exact concern.

For date selection collect the event type, date range, city/timezone, and the relevant participants' birth years. Mark the result as traditional date-selection guidance, not a guarantee.

## Cross-system comparison

Run each system independently. Present a table with: system, input time, convention, computed signal, interpretation, confidence limit. Treat a conflict first as a possible input or convention mismatch; do not force consensus.
