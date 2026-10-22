# Source and license record

## Included source

- `modules/bazi` is derived from `jinchenma94/bazi-skill` at commit `112a5d84cd1a001a0038cafca3be68d93e4c0cc9`.
- That repository declares the MIT License. Preserve `modules/bazi/LICENSE` and its copyright notice.

## Runtime-fetched source

- `FANzR-arch/Numerologist_skills` is pinned at commit `53ab46e7856e8e07a8de8ea96a2d93ed6694bedf`.
- `voidforall/fengshui.skill` is pinned at commit `91762ccda4ea106260ff43f336df14adf08ae57d`.
- Neither reviewed repository contained a license file at the pinned commit. Do not copy their code, prompts, examples, or reference text into this repository without the copyright holder's permission or a later explicit license.
- `scripts/bootstrap_upstreams.py` fetches those repositories into the ignored `.upstream/` directory for local use and verifies the exact commit. This repository distributes only the adapter and source metadata.

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
- Modern calendar rules follow `GB/T 33661-2017 农历的编算和颁行`, the current national standard under the Chinese Academy of Sciences.
- Public golden cases for 1901–2100 use the Hong Kong Observatory Gregorian-Lunar conversion tables. Dates explicitly marked by the Observatory as near-midnight uncertainty cases must be reported as boundary cases rather than used to claim false exactness.

## Review rule

Before updating a pin, inspect the new tree, license, dependencies, and tests. Record the new commit in `upstreams.json`, run the upstream test suites, then run this skill's validator and integration tests. Never promote an audit-only source to a primary calculator merely because two implementations agree; check whether they share the same dependency or copied rule table.
