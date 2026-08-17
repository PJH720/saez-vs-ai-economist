# Saez vs. The AI Economist

**What does the "16% better than Saez" in *The AI Economist* actually depend on?**

Five experiments, built entirely from the paper authors' own code, that locate the
headline claim's load-bearing assumptions. Presented 2026-08-13 at the AI@Sogang
reinforcement-learning study group.

📊 **[Slide deck (26 slides, Korean)](https://pjh720.github.io/saez-vs-ai-economist/)**
· 📄 **[Full results](experiments/RESULTS.md)** (Korean, as-run) · **[English](docs/RESULTS.en.md)**

---

## What this is — and what it is not

**This is not a replication of the paper's 16%.** That number comes from 400M
samples of two-level PPO training in a spatial 1000-step Gather-Trade-Build
economy. Nothing here trains a policy network.

What this *is*: a **falsification harness**. The paper's claim is a comparison —
AI planner *versus* the Saez (2001) optimal-tax baseline, scored by a specific
welfare function. A comparison can fail in three places that have nothing to do
with whether the RL worked:

1. **the scoring rule** you pick,
2. **the inputs** you feed the baseline, and
3. **whether the baseline is being used inside its design domain at all.**

E1–E4 probe exactly those three. Every economic quantity — the Saez formula, the
bracket-tax arithmetic, the equality and productivity metrics, the utility
function — is computed by calling `salesforce/ai-economist` **unmodified**, pinned
at commit [`a84d5f3`](https://github.com/salesforce/ai-economist/tree/a84d5f3fdcabb207d9fde7754d34906903b3e184).

## Findings

| | Proposition tested | Result |
|---|---|---|
| **E1** | Saez rates depend on the *shape* of the income distribution | Same mean income, shape only: **ρ = −0.96 → +1.00**. Log-normal yields a **regressive** schedule (65% → 26%); Pareto yields a **progressive** one (1% → 55%). |
| **E2** | The Saez baseline is sensitive to the assumed elasticity | Sweeping *e* = 0.2→1.5 moves the mean marginal rate **67.5% → 28.6%** — a **38.9 pp** swing. Top bracket: 46.7% → 10.5%. |
| **E3** | `eq × prod` is a normative choice, not a neutral measurement | Re-scoring the same four policies under 7 welfare functions produces **3 different winners**. |
| **E4** | "Emergent" tax gaming follows from regressive brackets | Under progressive US-Federal brackets, income-smoothing wins **7/7** income levels. Under Saez's log-normal schedule, alternating wins **7/7**. It's Jensen's inequality, not learning. |
| **E5** | Does schedule optimization beat Saez in a simplified economy? | **+10.9%** on `eq × prod` — same direction as the paper, different magnitude, different economy. Supporting evidence only. |

### The sharpest one

E3 re-scores the four policies from E5 under seven social welfare functions.
The winner is not stable:

| Welfare function | Free market | US Federal 2018 | Saez | Mini AI Economist | Winner |
|---|---|---|---|---|---|
| `eq × prod` (the paper's) | 279 | 246 | 266 | **295** | Mini-AI |
| Utilitarian Σuᵢ | **226** | 213 | 225 | 222 | Free market |
| Rawlsian min uᵢ | 26.5 | 35.5 | 30.2 | 35.5 | tie — US Federal / Mini-AI |
| Atkinson ε=0.5 | **105** | 82.9 | 99 | 101 | Free market |
| Atkinson ε=1 | **98.2** | 79.9 | 92.8 | 96.6 | Free market |
| Atkinson ε=2 | 86.7 | 74.6 | 82.8 | **89.8** | Mini-AI |
| Inverse-income weighted Σuᵢ/zᵢ | 2.00 | **2.72** | 2.23 | 2.40 | **US Federal** |

Read the last row against the paper's abstract. The paper's human-subject (MTurk)
claim is *"higher inverse-income weighted social welfare"* — **that exact metric.**
Here it is the one metric where the AI-designed schedule places **third**, behind
the actual 2018 US federal brackets.

`eq × prod` is multiplicative, which treats equality and productivity as perfect
complements. That is a strong normative commitment — not utilitarian, not
Rawlsian, not Atkinson. "16% better" is a value judgement wearing the clothes of
a measurement.

*(Rawlsian is a genuine tie at reported precision; the three-distinct-winners
result rests on the free-market and US-Federal rows, which are not close.)*

## Reproducibility

The original run was on an NVIDIA GB10 (DGX Spark, **aarch64 Linux**). Re-running
the whole harness on **arm64 macOS** from a fresh clone and a fresh venv:

| | |
|---|---|
| Numeric tables (`experiments/results/*.md`) | **5 of 5 byte-identical** |
| Figures (`experiments/figures/*.png`) | Differ — font rendering only, see below |

Every headline number reproduces exactly, including E5's stochastic search
(40,000 random schedules + 30 CEM generations), which is seeded.

The figures carry bilingual Korean/English labels. On a machine without a CJK
font, matplotlib renders the Korean half as boxes. The committed PNGs are the
correctly-rendered originals; install **Noto Sans CJK KR** or **NanumGothic** to
match them. No number is affected.

```bash
./setup.sh          # clone upstream @ a84d5f3, create .venv, install deps
```

```bash
cd experiments
../.venv/bin/python e1_saez_distribution.py
../.venv/bin/python e2_saez_elasticity.py
../.venv/bin/python e4_tax_avoidance.py
../.venv/bin/python e5_mini_ai_economist.py   # must precede E3
../.venv/bin/python e3_welfare_functions.py   # reads results/e5_incomes.npz
```

```bash
git diff --stat experiments/results/    # expect empty output
```

**Verify the "unmodified upstream" claim yourself:**

```bash
git -C ai-economist rev-parse HEAD                            # a84d5f3fdcabb207d9fde7754d34906903b3e184
git -C ai-economist status --porcelain --untracked-files=no    # empty == unmodified
```

`setup.sh` runs the second check and refuses to continue if the tree is dirty.

## What was deliberately not done

State this plainly, because the paper's number and E5's number are not
comparable:

- **No RL training.** The paper's 16% is 400M samples of two-level PPO. Not
  reproducible in an afternoon, and not attempted.
- **No Gather-Trade-Build simulation.** No spatial movement, gathering, trading,
  or building. E5 runs in `OneStepEconomy`, the simplified economy shipped with
  the repo from the 2021 follow-up paper, where agents' labor choices are
  independent — so best responses are solved *exactly* by grid search rather than
  approximated.
- **E5's `labor_cost` is a corrected value, not the default.** Upstream's `1.0`
  makes optimal labor ≈1 hour on the 0–100 scale, giving income ~2 coin — below
  the first tax bracket at 9.7, so the taxation problem disappears entirely.
  Set to `0.012` so the highest-skill agent works 94 hours and incomes span 5 of
  the 7 brackets. Documented in `experiments/e5_mini_ai_economist.py`.
- **Only 4 agents.** This is itself E1's point: the Saez formula depends on the
  income distribution's Pareto tail, and four points cannot form a tail.

## Layout

```
├── index.html              # 26-slide deck (Korean) — GitHub Pages entry point
├── setup.sh                # clone upstream @ pinned SHA, build venv
├── pyproject.toml          # verified-minimal deps (uv.lock pins transitives)
├── experiments/
│   ├── compat.py           # numpy>=1.24 shim + GPUtil stub + path setup
│   ├── aie_lib.py          # thin wrappers over upstream functions
│   ├── e1..e5_*.py         # the five experiments
│   ├── RESULTS.md          # full write-up, Korean, as presented
│   ├── figures/*.png       # 5 figures
│   └── results/*.md        # per-experiment numeric tables
├── docs/RESULTS.en.md      # English translation of the results
├── NOTICE.md               # upstream attribution, pinned SHA, shim rationale
└── REFERENCES.md           # DOIs / arXiv IDs (PDFs not redistributed)
```

`ai-economist/` is intentionally absent — see [NOTICE.md](NOTICE.md) for why
pinning beats vendoring here.

---

## 한국어

### 이 저장소가 하는 일

*The AI Economist* (Zheng et al., 2020)의 헤드라인 주장인 **"Saez 대비 16% 개선"**이
무엇에 의존하는지를 **저자들 자신의 코드로** 확인한 5개 실험입니다.
2026-08-13 AI@Sogang 강화학습 스터디 발표 자료입니다.

**논문의 16%를 재현한 것이 아닙니다.** 그 숫자는 공간·채집·거래·건축이 있는 1000스텝
경제에서 4억 샘플 2단계 PPO 학습으로 얻은 값이고, 여기서는 정책망을 학습시키지 않습니다.

이 저장소가 하는 것은 **반증 하네스**입니다. 논문의 주장은 *비교*입니다 — AI 플래너 대
Saez(2001) 베이스라인, 특정 후생함수로 채점. 비교는 RL이 잘 작동했는지와 무관하게
세 곳에서 무너질 수 있습니다: **채점 규칙**, **베이스라인에 넣은 입력값**, 그리고
**베이스라인을 애초에 설계 정의역 안에서 쓴 것인지**. E1–E4가 정확히 그 셋을 겨냥합니다.

### 핵심 결과

- **E1** — 평균소득을 같게 맞추고 분포 *형태*만 바꾸면 Saez 공식의 결론이 뒤집힙니다.
  로그정규 → **역진세**(65%→26%), 파레토 → **누진세**(1%→55%). 순위상관 ρ = −0.96 ↔ +1.00
- **E2** — 탄력성 가정 하나만 0.2→1.5로 바꾸면 평균 한계세율이 **67.5% → 28.6% (38.9%p)**
  움직입니다. 논문은 이를 상수로 가정하면서도 그 추정이 "highly non-trivial"이라 인정합니다
- **E3** — 같은 네 정책을 7개 후생함수로 다시 채점하면 **1위가 3종류로 갈립니다**.
  특히 논문이 MTurk 인간실험에서 우위를 주장한 지표(`역소득가중 Σuᵢ/zᵢ`)에서는
  미니-AI가 **3위**, 1위는 실제 **미 연방 2018** 세율표입니다
- **E4** — 논문이 "창발적"이라 부른 조세회피는 학습의 산물이 아니라, 세율표에 역진 구간이
  있으면 **Jensen 부등식으로 수학적으로 따라나옵니다**. 누진(미 연방)에서는 평탄화 7/7 승,
  Saez-로그정규에서는 교대 7/7 승
- **E5** — 단순화 경제에서 세율표 최적화가 Saez 대비 `eq × prod` **+10.9%**.
  논문과 방향은 같고 크기는 다르며, 경제 구조가 달라 직접 비교할 수 없습니다 (보조 증거)

### 재현성

원 실행은 DGX Spark(aarch64 Linux), 재검증은 arm64 macOS에서 fresh clone + fresh venv로
전체 재실행했습니다 → **수치 표 5/5 완전 일치**. E5의 확률적 탐색(무작위 40,000회 + CEM
30세대)까지 seed 고정으로 동일하게 재현됩니다.

그림은 한영 병기 라벨이라 CJK 폰트가 없는 머신에서는 한글이 □로 렌더됩니다. 저장된 PNG는
정상 렌더된 원본이며, `Noto Sans CJK KR` 또는 `NanumGothic`을 설치하면 동일하게 나옵니다.
**숫자에는 영향이 없습니다.**

전체 실습 기록은 [`experiments/RESULTS.md`](experiments/RESULTS.md)에 설정값(분포 모수,
탄력성, 스킬, 탐색 횟수, seed)과 예상 질문 대비까지 그대로 있습니다.

---

## License

MIT for this harness — see [LICENSE](LICENSE).
`salesforce/ai-economist` is BSD-3-Clause, © 2020 Salesforce.com, Inc., and is
called but **not** redistributed here — see [NOTICE.md](NOTICE.md).
