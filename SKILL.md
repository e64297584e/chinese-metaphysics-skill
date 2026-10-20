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

Use either `--solar YYYY-MM-DD` or `--lunar YYYY-MM-DD`. Add `--leap` for a leap lunar month. Do not silently choose a birth hour or sex. Treat location as descriptive unless a separate verified true-solar-time conversion is performed.

## Run Qimen

Collect the event, goal, relevant time, city, timezone, and current stage. Create the input JSON described in `references/routing.md`, then run:

```bash
python3 scripts/run_module.py qimen --input tmp/qimen-input.json --output tmp/qimen-output.json
```

Use the pinned calculator output as the chart. Do not hand-calculate a substitute if the external module is absent.

## Run Ziwei

Collect calendar type, birth date and time, sex, and the requested topic. Confirm late-Zi-hour and leap-month conventions when applicable. Create the input JSON described in `references/routing.md`, then run:

```bash
python3 scripts/run_module.py ziwei --input tmp/ziwei-input.json --output tmp/ziwei-output.json
```

Use the normalized input, warnings, twelve palaces, four transformations, and period overlays from the script. If the time is uncertain, run the plausible time branches and compare them.

## Use Feng Shui

Run the bootstrap, then obtain the pinned reference path:

```bash
python3 scripts/run_module.py fengshui-source
```

Read only the upstream files relevant to the question. For a dwelling, collect a measured orientation, construction or move-in period, a floor-plan description or image, exterior conditions, occupants, and the user's specific concern. Distinguish observable design issues—light, ventilation, circulation, moisture, noise, fire safety—from traditional symbolic interpretation. Prefer physical layout changes over claims about charms or guaranteed outcomes.

## Present the result

Use this compact structure:

1. Confirmed inputs
2. Conventions and source version
3. Computed chart summary
4. Traditional interpretation and its basis
5. Uncertainty or conflicting signals
6. Practical actions and limits

Do not claim certainty, guaranteed wealth, unavoidable misfortune, diagnosis, or supernatural causation. Do not use fear to sell remedies.
