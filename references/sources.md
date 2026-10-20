# Source and license record

## Included source

- `modules/bazi` is derived from `jinchenma94/bazi-skill` at commit `112a5d84cd1a001a0038cafca3be68d93e4c0cc9`.
- That repository declares the MIT License. Preserve `modules/bazi/LICENSE` and its copyright notice.

## Runtime-fetched source

- `FANzR-arch/Numerologist_skills` is pinned at commit `53ab46e7856e8e07a8de8ea96a2d93ed6694bedf`.
- `voidforall/fengshui.skill` is pinned at commit `91762ccda4ea106260ff43f336df14adf08ae57d`.
- Neither reviewed repository contained a license file at the pinned commit. Do not copy their code, prompts, examples, or reference text into this repository without the copyright holder's permission or a later explicit license.
- `scripts/bootstrap_upstreams.py` fetches those repositories into the ignored `.upstream/` directory for local use and verifies the exact commit. This repository distributes only the adapter and source metadata.

## Review rule

Before updating a pin, inspect the new tree, license, dependencies, and tests. Record the new commit in `upstreams.json`, run the upstream test suites, then run this skill's validator and integration tests.
