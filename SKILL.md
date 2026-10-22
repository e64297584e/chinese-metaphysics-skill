---
name: chinese-metaphysics-skill
description: Use for Chinese traditional metaphysics requests involving Bazi/Four Pillars, Qimen Dunjia, Ziwei Doushu, Feng Shui, date selection, or a cross-system comparison. Collect missing inputs first, use deterministic scripts for chart calculation, state the selected conventions and uncertainty, keep each system's logic separate, and frame results as cultural or reflective guidance rather than factual prediction.
---

# Chinese Metaphysics Skill

Route one request through Bazi, Qimen Dunjia, Ziwei Doushu, Feng Shui, or an explicit cross-system comparison. Calculate first and interpret second. Never invent a chart when a calculator is unavailable.

## Prepare the skill

Run this once before using any calculator or the upstream Feng Shui reference:

```bash
python3 scripts/bootstrap_upstreams.py --install-deps
python3 scripts/doctor.py
```

The bootstrap pins upstream repositories to reviewed commits. It does not vendor repositories that lack an explicit redistribution license. Read `references/sources.md` before changing or republishing the source layout.

Before evaluating any public project or dataset, read references/evidence-policy.md and
its structured registries. Social posts are discovery trails only. External Ziwei
implementations and datasets are not primary authorities; read
references/ziwei-runtime-audit.md before using the default runtime and
references/ziwei-audit.md before using the optional comparison source. Read
references/qimen-profile-audit.md before describing the Qimen ruleset, and
references/fengshui-audit.md before reading the fetched Feng Shui snapshot.

## Route the request

- Use **Bazi** for four pillars, day-master strength, ten gods, luck cycles, annual influences, or a broad life-pattern reading.
- Use **Qimen** for one concrete event, decision, timing window, direction, negotiation, trip, or tactical question tied to a specific time and place.
- Use **Ziwei** for a natal twelve-palace reading, major-period structure, annual overlays, or a supplied Ziwei chart.
- Use **Feng Shui** for a dwelling, office, orientation, floor plan, exterior form, room layout, flying stars, Eight Mansions, or date selection.
- Use **cross-system mode** only when the user asks for comparison or when two systems materially clarify the same question. Keep calculations and terminology separate; report agreements, disagreements, and possible convention differences.

Read `references/routing.md` for required inputs, commands, and output contracts.

## Work in this order

1. Identify the requested system and the real-world question.
2. Ask only for missing inputs that can change the chart or conclusion.
3. State the calendar, timezone, day-boundary, leap-month, school, and other selected conventions before calculation.
4. Run the deterministic calculator when the route has one.
5. Check warnings and normalized inputs before interpretation.
6. Separate computed facts, traditional interpretation, uncertainty, and practical advice.
7. For high-stakes health, legal, financial, safety, or housing decisions, provide ordinary evidence-based next steps and never treat the reading as decisive.

## Run Bazi

Use the bundled MIT-licensed calculator:

```bash
python3 scripts/run_module.py bazi -- \
  --solar 1991-06-15 --hour 15:18 --sex 男 --place 安徽阜阳
```

Use either `--solar YYYY-MM-DD` or `--lunar YYYY-MM-DD`. Add `--leap` for a leap lunar month. Do not silently choose a birth hour or the traditional sex parameter used for luck-cycle direction. This calculator treats every input as a fixed UTC+8 standard wall clock and does **not** apply historical China DST. The place argument is descriptive and does not correct timezone, longitude, or equation of time. For overseas births, 1986-1991 China DST, pre-1949 time, or true-solar-time requests, obtain a verified conversion and report its profile; otherwise stop at a sensitivity warning rather than issuing a falsely corrected chart.

## Run Qimen

Collect the event, goal, relevant time, city, timezone, and current stage. Validate the
local civil time, convert the instant to a fixed UTC+8 wall clock, and use the explicit
`Etc/GMT-8` input profile described in `references/routing.md`, then run:

```bash
python3 scripts/run_module.py qimen --input tmp/qimen-input.json --output tmp/qimen-output.json
```

Use the pinned calculator output only as the deterministic result of the named cultural
engineering profile. It is Tier C and is **not** an independently validated or
authoritative traditional chart; do not hand-calculate a substitute or silently elevate
it when the external module is absent. If the user requires a validated school-specific
chart, state that the current repository does not yet provide one.
Read the adapter's profile_review field. mainline-cn-v1 currently means the reviewed
fixed-solar-term-five-day-v1 engineering profile; it is not a complete
supernormal/connecting/intercalation implementation and must not be labelled simply
as “置闰法”. The adapter rejects arbitrary ruleset labels and unconverted IANA local
wall clocks because the pinned engine does not perform a reliable instant conversion.

## Run Ziwei

Collect calendar type, birth date and time, sex, and the requested topic. Explicitly
confirm the late-Zi-hour and leap-month conventions. State which civil wall-clock
profile is being used before calculation; the engine does not process place, timezone,
historical DST, longitude, or true solar time. Create the strict input JSON described in
`references/routing.md`, then run:

```bash
python3 scripts/run_module.py ziwei --input tmp/ziwei-input.json --output tmp/ziwei-output.json
```

Treat the result only as the deterministic output of the named Tier C
`fixed-civil-date-sanhe-v1` cultural/engineering profile. It is not independently
validated or authoritative across Ziwei schools. Read `profile_review`, normalized
input, warnings, twelve palaces, four transformations, and period overlays. If the time
is uncertain, run the plausible time branches and compare them. Never add timezone or
longitude fields and imply they were applied: the adapter rejects such ignored fields.

For an external comparison, preserve the local result and classify differences as `agreement`, `known_convention`, `local_missing_coverage`, or `unexpected_difference`. Do not let one external output silently change the selected ruleset. The optional `Renhuai123/ziwei-doushu` snapshot is evidence tier C: use it to find regressions and coverage gaps, not as ground truth. Its v4 interpretation dataset cannot reproduce a full chart and its text must not be used for training, RAG, or responses.

## Use Feng Shui

Run the bootstrap, then obtain the pinned reference path:

```bash
python3 scripts/run_module.py fengshui-source
```

The fetched snapshot has confirmed calculation and provenance defects. Do not use its
annual Flying Star table, simplified flight rule, life-gua examples, date-selection
absolutes, or invented lineage persona; references/fengshui-audit.md is the controlling
overlay. For a dwelling, collect only the minimum anonymized orientation and layout
information. Distinguish observable design issues—light, ventilation, circulation,
moisture, noise, accessibility, and fire or building safety—from traditional symbolic
interpretation. Applicable codes and qualified professionals always outrank a
traditional rule.

## Present the result

Use this compact structure:

1. Confirmed inputs
2. Conventions and source version
3. Computed chart summary
4. Traditional interpretation and its basis
5. Uncertainty or conflicting signals
6. Practical actions and limits

Do not claim certainty, guaranteed wealth, unavoidable misfortune, diagnosis, or supernatural causation. Do not use fear to sell remedies.
