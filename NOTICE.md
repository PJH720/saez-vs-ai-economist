# Third-party notices

## salesforce/ai-economist

This harness **calls** the AI Economist reference implementation. It does not
redistribute it — `./setup.sh` clones it from the canonical source, and
`.gitignore` excludes `ai-economist/` from this repository.

| | |
|---|---|
| Project | [salesforce/ai-economist](https://github.com/salesforce/ai-economist) |
| Pinned commit | `a84d5f3fdcabb207d9fde7754d34906903b3e184` (2022-05-09) |
| License | BSD 3-Clause |
| Copyright | © 2020 Salesforce.com, Inc. |

### Why pinned rather than vendored

The central claim of this repository is that the economics — the Saez formula,
the bracket-tax arithmetic, the equality and productivity metrics, the utility
function — is computed by **the paper authors' own code, unmodified**. Vendoring
a copy would ask you to trust a diff. Pinning a commit lets you verify it:

```bash
git -C ai-economist rev-parse HEAD                             # a84d5f3fdcabb207d9fde7754d34906903b3e184
git -C ai-economist status --porcelain --untracked-files=no     # empty == unmodified
```

`setup.sh` runs the second check and refuses to proceed if the tree is dirty.

### The one compatibility shim

Upstream targets numpy 1.21. On numpy ≥ 1.24 the removed aliases `np.int` /
`np.float` break the import. `experiments/compat.py` restores them **in the
importing process only** — it does not patch any file in `ai-economist/`.
Upstream uses `np.int` in exactly three places:

- `ai_economist/foundation/scenarios/utils/layout_from_file.py:212,213`
- `tutorials/utils/plotting.py:185`

`compat.py` also stubs `GPUtil`, which the COVID-19 scenario imports at module
load and which itself imports `distutils` (removed in Python 3.12). No
COVID-19 code path is exercised by this harness.

### Functions called verbatim

| Concern | Upstream source |
|---|---|
| Saez optimal rates | `redistribution.PeriodicBracketTax.get_binned_saez_welfare_weight_and_pareto_params` → `get_saez_marginal_rates` → `bracketize_schedule` |
| Bracket tax arithmetic | `redistribution.PeriodicBracketTax.taxes_due` |
| Equality, productivity | `scenarios/utils/social_metrics.get_equality`, `get_productivity` |
| Utility | `scenarios/utils/rewards.isoelastic_coin_minus_labor`, `coin_minus_labor_cost` |
| Skill generation | `components/simple_labor.SimpleLabor` |
| Simplified economy | `scenarios/simple_economy.OneStepEconomy` |

Original code in this repository is limited to the best-response grid search,
the tax-schedule search loop, the welfare-function comparison, and plotting.

---

## Papers

Source PDFs are **not** redistributed — several are subscription content
(e.g. Saez 2001, *Review of Economic Studies*, Oxford Academic). See
[REFERENCES.md](REFERENCES.md) for DOIs and arXiv identifiers.

## Slide deck fonts

`index.html` loads Inter and JetBrains Mono from Google Fonts at view time.
Offline, it falls back to system fonts; layout and content are unaffected.
