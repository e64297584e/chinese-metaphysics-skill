# External evidence and evaluation policy

This repository uses public projects and social posts for discovery, not as automatic
authority. Every candidate must be traced to its original repository, exact revision,
licence scope, test evidence, dependency lineage, and stated conventions before it can
affect a rule or calculator.

## Evidence tiers

| Tier | Meaning | Permitted use |
|---|---|---|
| A | A current official standard, official calendar table, or other primary authority within its stated scope | Sparse golden facts, normative calendar rules, and boundary cases with a stable citation |
| B | Strong secondary evidence within one named claim: clean-clone reproducible; for calculation claims, independently implemented with explicit conventions and independently sourced goldens | Secondary differential oracle within that claim; never overrides a Tier A fact |
| C | A community implementation, generated dataset, benchmark, or partially independent port | Regression discovery, coverage leads, hypothesis generation, or a clearly labelled non-authoritative cultural/engineering demonstration; never an authority or decision guarantee |
| D | A social post, popularity signal, anecdote, UI, prompt collection, or unverified claim | Discovery only |
| Rejected | Missing rights, broken provenance, non-reproducible tests, material algorithm defects, or unsupported claims | Record the reason so it is not rediscovered and promoted later |

An item can have different tiers for different claims. For example, a repository can be
Tier B for build reproducibility, Tier C for chart arithmetic, and unusable for
interpretation text. A Tier B engineering claim means only that the declared clean-clone
build/test procedure reproduced in its recorded environment; it does not promote that
project's calculations. A Tier B calculation claim additionally requires implementation
independence plus registry-linked authority sources and independent goldens.

## Mandatory gates

1. **Identity** — record the canonical repository, full 40-character commit, review
   date, and any release or dataset hash.
2. **Rights** — review code, data, quotations, images, and third-party source material
   separately. A root MIT or CC licence does not grant rights in competition questions,
   modern books, course transcripts, or embedded quotations owned by others. Data and
   text imports require their own approved licence plus HTTPS provenance; a rejected
   candidate or rejected claim cannot import any artifact.
3. **Reproducibility** — use a clean checkout, locked dependencies, documented commands,
   and portable fixtures. Author-local absolute paths, remote caches, or same-engine
   snapshots do not count as clean-clone reproduction.
4. **Convention contract** — state calendar, timezone, historical DST, longitude or
   true-solar-time handling, day boundary, leap-month rule, school, and profile ID.
5. **Independence** — trace dependencies and generated fixtures. Two wrappers around the
   same engine or table are one lineage, not two votes.
6. **Golden provenance** — identify who published each expected value and why that
   source is authoritative for that field. Agreement between implementations is not a
   golden case. Promotion evidence must use a declared system scope, a matching Tier A
   authority, and a matching executable hard/boundary golden; a manual uncertainty case
   cannot promote a calculator.
7. **Privacy and leakage** — do not ingest identifiable birth histories, life events,
   paid contest questions, or answer keys without a verified right and a documented
   need. Keep evaluation material out of training and retrieval corpora.
8. **Promotion** — a default rule changes only after a traceable rule source, an
   independent implementation or derivation, and targeted boundary tests agree. Record
   known convention differences instead of majority-voting them away.

The structured review record is in candidate-audits.json. Run
scripts/validate_evidence.py after every edit.

The machine registry accepts exactly the `engineering`, `calculation`, and
`interpretation` claim keys. New claim names require a schema change and tests; suffixes
must not be used to bypass the calculation gate. Candidate, authority, evidence, and
golden system tags must agree before promotion. A Tier B calculation or primary review
uses a single-system candidate record; split multi-system projects into scoped records
before promotion. Every cited golden must be executable, match its adapter and authority
system, and be directly sourced by one of the evidence authorities.

Primary promotion is intentionally disabled as a data-only operation. It requires a
reviewed validator/schema change plus an explicit coverage matrix; editing a candidate
record, filling placeholder fields, or matching one golden can never promote an engine.
Any code import also requires the same structured clean-clone reproduction record used
by Tier B engineering review.

## Separate the evaluation layers

Do not collapse these layers into one accuracy number:

1. input normalization and civil-time conversion;
2. astronomical and calendar calculation;
3. school-specific rule selection;
4. chart topology and derived fields;
5. interpretation or outcome answers;
6. safety, uncertainty disclosure, and practical usefulness.

A multiple-choice outcome score cannot validate the underlying calendar or chart
engine. A perfect port-to-port match proves compatibility with the reference port, not
historical correctness. A large generated corpus is useful for invariants and load
testing, but it is still one deterministic source.

## Benchmark reporting

For every result publish the exact code revision, dependency lock, profile, timezone,
day boundary, dataset slice, exclusions, and scoring rule. Exclude inaccessible or
incomplete questions before calculating a denominator. Separate official answer keys
from secondary transcription agreement. Do not describe a top contestant score as a
human average.

When an LLM is evaluated, freeze a held-out set, shuffle answer choices, record all
runs, and report variation rather than selecting the best run. Public benchmark
questions must be treated as contamination-prone. A future blind set is stronger only
when its rights and privacy status are clear.

## Calendar and time priorities

- Use the current Chinese lunar-calendar standard and official Purple Mountain
  Observatory publications for normative mainland-China calendar rules.
- Use Hong Kong Observatory open data as an independently published conversion source.
  Near-midnight new-moon cases are uncertainty tests, not opportunities to claim false
  precision.
- Lock IANA tzdb for post-1970 civil-time conversion. Its pre-1970 history is explicitly
  incomplete, so historical China and other uncertain zones require a warning or
  profile branches.
- Ephemerides, Earth-orientation data, and Delta-T models are inputs to a derivation;
  none is a lunar-calendar answer by itself.
- Cite versioned classical editions for rule provenance. A historical text can document
  a school rule but does not by itself prove a modern calculator implementation.

## X and other social sources

Record the post URL as the discovery trail when useful, then verify every claim at the
original repository or official source. Follower count, stars, reposts, screenshots,
and comments never raise an evidence tier. Do not copy post text into the skill.
