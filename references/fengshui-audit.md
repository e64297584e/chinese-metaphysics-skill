# Feng Shui source audit and safety overlay

The pinned voidforall/fengshui.skill checkout is an unlicensed, untested reference
snapshot. It is not a calculator or authority. This local audit overrides conflicting
claims in that checkout.

## Material that must not be used

- Do not repeat its invented “江南三元派世家第七代传人” biography or role-play any
  lineage, training, or credential that has not been independently verified.
- Do not use its annual Flying Star table, its associated five-yellow/two-black
  directions, or its simplified mountain/facing flight rule.
- Do not use its Eight Mansions life-gua examples as a calculation source.
- Do not use its date-selection page as an absolute prohibition, medical timing rule,
  engineering rule, or source of objective risk.
- Do not copy or republish its text or examples. The reviewed commit has no licence.

Until a versioned local calculator and test suite are added, traditional Flying Star,
Eight Mansions, and date-selection outputs must be described as unsupported or must
come from a separately named, reviewed profile. Observable layout analysis can still
cover light, ventilation, circulation, moisture, noise, accessibility, and safety.

## Confirmed defects

### Annual Flying Star table

The upstream table is shifted by one year. Under the commonly used annual center-star
sequence, the reviewed near-term centers and derived directions are:

| Year | Center | Five yellow | Two black |
|---:|---:|---|---|
| 2022 | 5 | center | southwest |
| 2023 | 4 | northwest | east |
| 2024 | 3 | west | southeast |
| 2025 | 2 | northeast | center |
| 2026 | 1 | south | northwest |
| 2027 | 9 | north | west |
| 2028 | 8 | southwest | northeast |
| 2029 | 7 | east | south |
| 2030 | 6 | southeast | north |

These are traditional chart positions, not medical, financial, or causal facts. Do not
turn “two black” or “five yellow” into a diagnosis or a reason to delay care.

### Flying Star mountain and facing rules

The rule “yang mountain and yang facing means one fixed direction; yin means the
opposite” is an over-simplification. A Shen-style lower-chart implementation must
derive direction from each center star's original palace and matching yuan-dragon,
handle the center-five borrowing rule, cover all 24 mountains, and explicitly reject or
separately implement replacement/兼向 charts. A future validator needs 9 periods by 24
mountains, permutation invariants for all three grids, opposite bearings, center-five
cases, and bearing-boundary uncertainty.

### Eight Mansions life gua

A 1900s shortcut cannot be silently reused after 2000. A reviewed profile must state
its century formula, Li Chun or civil-year boundary, and center-five substitution. In
the common table reviewed here, male center-five substitutes Kun 2 and female
center-five substitutes Gen 8; the upstream female example reverses that convention.
Do not calculate a life gua from the snapshot until all years and boundary policies are
covered by independent fixtures.

The sex parameter in such a traditional table is only a selected calculation
convention. It must not be used to infer identity, ability, personality, or social
role, and a user may decline to provide it.

### Date selection

- 四离日 normally means the day before each equinox and solstice in the reviewed
  tradition; it is not synonymous with the 建 day of the twelve-day officer cycle.
- A monthly branch mapping for 受死日 does not mean there are only twelve matching
  civil dates in a year; the branch recurs about every twelve days.
- Terms such as 月破, 太岁, 三煞, 天医, and 受死 are profile-specific traditional
  labels. They never override weather, permits, contracts, fire protection,
  structural/electrical/gas safety, medical urgency, or professional advice.

A future date-selection response must separate objective calendar facts, a named and
versioned traditional ruleset, triggered and conflicting rules, missing inputs,
boundary uncertainty, and a cultural-use limitation.

## Evidence path

RoxyAPI/astrology-api-benchmark at
0f3d187f638011976fe48096f8c291ca53477ff8 is a promising MIT-licensed external
regression source for specific lower-chart, annual-star, and life-gua profiles. It
links expected values to named editions and excludes three internally inconsistent
source rows. It is still an external differential oracle: it does not prove that
traditional Feng Shui predicts real-world outcomes, and no code or classical text is
imported in this review.

Objective calendar boundaries should use the authority registry. Building safety
must follow current applicable law, local codes, and qualified professionals. Solar
exposure may later use a reviewed astronomical library such as pvlib, but must remain
separate from symbolic direction rules.

## Privacy

Collect only the city or climate zone, anonymized orientation, necessary dates, and a
redacted plan. Ask the user to remove names, exact addresses, unit numbers, QR codes,
security details, and photo EXIF. Do not publish a household's plan, entry paths,
birth data, or case input. Avoid detailed public descriptions that expose security
routes or occupant routines.
