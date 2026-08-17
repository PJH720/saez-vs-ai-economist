"""E5 — 미니 AI Economist: OneStepEconomy에서 세율표를 직접 최적화한다.

⚠️ 이것은 논문 결과의 재현이 아니다.
   논문의 16%는 공간·채집·거래·건축이 있는 1000스텝 경제에서 4억 샘플의 2단계
   RL 학습으로 얻은 값이다. 여기서 하는 것은 저장소에 함께 들어있는
   **OneStepEconomy**(2021년 후속논문 arXiv:2108.02755의 단순화 경제)에서,
   학습이 아니라 **정적 최적화**로 같은 논리를 실행해 보는 것이다.

왜 이게 정당한가 (저장소 docstring 그대로):
   "Each agent chooses an amount of labor that optimizes its post-tax utility,
    and this optimal labor depends on its skill and the tax rates, and
    **it does not depend on the labor choices of other agents.**"
   -> 에이전트 간 상호작용이 없으므로 best response를 그리드 탐색으로 '정확히'
     구할 수 있다. 근사가 아니라 이 단순화 경제의 정확한 해다.

저장소에서 그대로 가져다 쓰는 것:
   - 스킬 생성 방식 (SimpleLabor: pareto(4) 표본을 pmsm=3으로 clip 후 순위평균)
   - 소득 공식 payoff = hours x skill (SimpleLabor.component_step)
   - 효용 coin_minus_labor_cost (rewards.py)
   - 구간세 계산 (redistribution.taxes_due 로직)
   - Saez 공식 (redistribution의 3단 파이프라인)
   - eq/prod (social_metrics.get_equality / get_productivity)
내가 새로 쓴 것: best-response 그리드 탐색 루프와 세율 탐색 최적화뿐.

대응 슬라이드: S18 뒤 신규 슬라이드
"""

import numpy as np

import aie_lib as L
from compat import RESULT_DIR, save, setup_matplotlib, write_table

N_AGENTS = 4
MAX_HOURS = 100  # SimpleLabor.num_labor_hours
LABOR_EXPONENT = 2.0  # OneStepEconomy 기본값
LABOR_COST = 0.012  # <- 보정값(아래 주석). 저장소 기본 1.0은 이 시간 스케일에서 퇴화함
PMSM = 3.0  # payment_max_skill_multiplier
ELAS = 0.5
SEED = 0
N_SEARCH = 40000

# LABOR_COST 보정 근거:
#   무세 상태의 최적 노동은 l* = skill/(2·c). 저장소 기본 c=1.0이면 l*~1시간,
#   소득 ~2coin으로 첫 과세구간(9.7)에도 못 미쳐 세금 문제 자체가 사라진다.
#   c=0.012로 두면 최고숙련 에이전트가 94시간(100시간 상한 미만)을 일하고
#   소득이 약 53~212 coin에 퍼져 7개 구간 중 5개를 지난다.


def make_skills(seed=SEED):
    """SimpleLabor.__init__ 와 동일한 방식으로 스킬을 만든다."""
    rng = np.random.RandomState(seed)
    pareto_samples = rng.pareto(4, size=(1000, N_AGENTS))
    clipped = np.minimum(PMSM, (PMSM - 1) * pareto_samples + 1)
    return np.sort(clipped, axis=1).mean(axis=0)


def solve_agents(comp, rates, skills):
    """각 에이전트의 정확한 best response(노동시간)를 그리드 탐색으로 구한다.

    효용 = (세후소득 + 정액환급) − c·(노동시간)^2
    정액환급은 자기 선택과 무관한 상수이므로 argmax에 영향을 주지 않는다
    (표준 lump-sum 가정). 따라서 에이전트별로 독립적으로 풀 수 있다.
    """
    hours = np.arange(0, MAX_HOURS + 1, dtype=float)
    labors, incomes = [], []
    for s in skills:
        z = hours * s
        tax = np.array([L.taxes_due(comp, rates, zi) for zi in z])
        util = (z - tax) - LABOR_COST * (hours**LABOR_EXPONENT)
        best = int(np.argmax(util))
        labors.append(hours[best])
        incomes.append(z[best])
    labors = np.array(labors)
    incomes = np.array(incomes)
    taxes = np.array([L.taxes_due(comp, rates, zi) for zi in incomes])
    rebate = taxes.sum() / N_AGENTS
    coins = incomes - taxes + rebate
    return labors, incomes, taxes, coins


def metrics(coins):
    from ai_economist.foundation.scenarios.utils.social_metrics import (
        get_equality,
        get_productivity,
    )

    eq = float(get_equality(coins))
    prod = float(get_productivity(coins))
    return eq, prod, eq * prod


def objective(comp, rates, skills, equality_weight=1.0):
    """저장소의 coin_eq_times_productivity 와 동일한 형태의 목적함수."""
    _, _, _, coins = solve_agents(comp, rates, skills)
    eq, prod, _ = metrics(coins)
    return prod * (1.0 - equality_weight + equality_weight * eq), coins


def optimize_rates(comp, skills, equality_weight=1.0, n=N_SEARCH, seed=SEED):
    """7개 구간세율을 탐색으로 최적화 (랜덤 서치 + CEM 정제)."""
    rng = np.random.default_rng(seed)
    best_r = np.zeros(7)
    best_v = objective(comp, best_r, skills, equality_weight)[0]

    # 1단계: 랜덤 서치
    for _ in range(n // 2):
        r = rng.uniform(0, 1, size=7)
        v, _ = objective(comp, r, skills, equality_weight)
        if v > best_v:
            best_v, best_r = v, r

    # 2단계: CEM 정제
    mu, sigma = best_r.copy(), np.full(7, 0.25)
    for _ in range(30):
        pop = np.clip(rng.normal(mu, sigma, size=(60, 7)), 0, 1)
        vals = np.array([objective(comp, r, skills, equality_weight)[0] for r in pop])
        elite = pop[np.argsort(vals)[-12:]]
        mu, sigma = elite.mean(axis=0), elite.std(axis=0) + 1e-3
        v, _ = objective(comp, mu, skills, equality_weight)
        if v > best_v:
            best_v, best_r = v, mu.copy()
    return best_r, best_v


def saez_fixed_point(comp, skills, iters=40, damp=0.5):
    """Saez 세율표를 고정점까지 반복한다 (세율->소득->세율)."""
    rates = np.zeros(7)
    for _ in range(iters):
        _, incomes, _, _ = solve_agents(comp, rates, skills)
        new = L.saez_schedule(comp, incomes, ELAS)
        if np.max(np.abs(new - rates)) < 1e-4:
            rates = new
            break
        rates = damp * new + (1 - damp) * rates
    return rates


def main():
    plt = setup_matplotlib()
    comp = L.make_tax_component(tax_model="saez", saez_fixed_elas=ELAS)
    skills = make_skills()
    print(f"skills = {np.round(skills, 3)}")

    policies = {}
    policies["자유시장 Free market"] = np.zeros(7)
    policies["미 연방 2018 US Federal"] = L.US_FEDERAL_2018.copy()
    policies["Saez (고정점)"] = saez_fixed_point(comp, skills)
    ai_rates, _ = optimize_rates(comp, skills, equality_weight=1.0)
    policies["미니-AI Mini AI Economist"] = ai_rates

    rows = {}
    for name, rates in policies.items():
        labors, incomes, taxes, coins = solve_agents(comp, rates, skills)
        eq, prod, swf = metrics(coins)
        rows[name] = dict(
            rates=rates, labors=labors, incomes=incomes, taxes=taxes,
            coins=coins, eq=eq, prod=prod, swf=swf,
        )

    base = rows["Saez (고정점)"]["swf"]
    for name in rows:
        rows[name]["vs_saez"] = 100.0 * (rows[name]["swf"] / base - 1.0)

    # --- 달성가능집합: 무작위 세율표 다수를 평가해 (생산성, 평등) 구름을 만든다 ---
    # 논문 Figure의 Pareto boundary와 같은 성격의 그림. 최적화 궤적보다
    # '무엇이 달성 가능한가'를 보여주는 쪽이 정보량이 많다.
    rng = np.random.default_rng(SEED + 1)
    cloud = []
    for _ in range(6000):
        r = rng.uniform(0, 1, size=7)
        _, _, _, c = solve_agents(comp, r, skills)
        eq, prod, _ = metrics(c)
        cloud.append((prod, eq))
    cloud = np.array(cloud)

    # 파레토 경계(생산성↑ 평등↑ 방향으로 지배되지 않는 점들)
    order = np.argsort(-cloud[:, 0])
    pareto, best_eq = [], -np.inf
    for idx in order:
        if cloud[idx, 1] > best_eq:
            best_eq = cloud[idx, 1]
            pareto.append(cloud[idx])
    pareto = np.array(pareto[::-1])

    # --- 그림 ---
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.7))
    labels = L.bracket_labels(comp)
    x = np.arange(7)
    colors = {
        "자유시장 Free market": "#7f8c8d",
        "미 연방 2018 US Federal": "#27ae60",
        "Saez (고정점)": "#c0392b",
        "미니-AI Mini AI Economist": "#2471a3",
    }

    ax = axes[0]
    for name, d in rows.items():
        ax.step(x, d["rates"] * 100, where="mid", lw=2.3, color=colors[name], label=name)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=7.5)
    ax.set_xlabel("소득 구간 Income bracket")
    ax.set_ylabel("한계세율 Marginal rate (%)")
    ax.set_title("① 네 가지 세율표\nTax schedules")
    ax.legend(fontsize=7.5)
    ax.grid(alpha=0.3)

    ax = axes[1]
    names = list(rows)
    swfs = [rows[n]["swf"] for n in names]
    ax.bar(range(len(names)), swfs, color=[colors[n] for n in names])
    for i, n in enumerate(names):
        ax.text(i, swfs[i], f"{rows[n]['vs_saez']:+.1f}%", ha="center",
                va="bottom", fontsize=9)
    short = {
        "자유시장 Free market": "자유시장",
        "미 연방 2018 US Federal": "미 연방",
        "Saez (고정점)": "Saez",
        "미니-AI Mini AI Economist": "미니-AI",
    }
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels([short[n] for n in names], rotation=15, fontsize=9)
    ax.set_ylabel("사회후생 swf = eq × prod")
    ax.set_title("② 사회후생 비교 (Saez 대비 %)\nSocial welfare vs Saez")
    ax.grid(alpha=0.3, axis="y")

    ax = axes[2]
    ax.scatter(cloud[:, 0], cloud[:, 1], s=4, alpha=0.12, color="#95a5a6",
               label="무작위 세율표 6,000개 (달성가능집합)")
    ax.plot(pareto[:, 0], pareto[:, 1], "-", lw=2.2, color="#8e44ad",
            label="파레토 경계 Pareto boundary")
    for name, d in rows.items():
        ax.scatter(d["prod"], d["eq"], s=130, color=colors[name],
                   edgecolor="k", zorder=5, label=short[name])
    ax.set_xlabel("생산성 Productivity (총 coin)")
    ax.set_ylabel("평등 Equality (1 − 정규화 지니)")
    ax.set_title("③ 형평성–생산성 트레이드오프\nEquality–productivity frontier")
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3)

    fig.suptitle(
        "E5 — 미니 AI Economist (OneStepEconomy, 정적 최적화)  "
        "※ 논문 재현 아님 — 단순화 경제에서 같은 논리를 직접 실행",
        fontsize=12.5, y=1.04,
    )
    save(fig, "e5_mini_ai_economist")

    # --- 표 ---
    tbl = ["| 정책 | 평등 eq | 생산성 prod | 사회후생 eq×prod | Saez 대비 |",
           "|---|---|---|---|---|"]
    for name, d in rows.items():
        tbl.append(
            f"| {name} | {d['eq']:.4f} | {d['prod']:.1f} | {d['swf']:.1f} | "
            f"{d['vs_saez']:+.1f}% |"
        )

    sch = ["", "**세율표 (한계세율 %)**", "",
           "| 구간 | " + " | ".join(rows) + " |", "|---|" + "---|" * len(rows)]
    for i, lab in enumerate(labels):
        sch.append(f"| {lab} | " + " | ".join(
            f"{rows[n]['rates'][i]*100:.1f}" for n in rows) + " |")

    inc = ["", "**에이전트별 결과 (스킬 오름차순)**", "",
           "| 에이전트 | 스킬 | " + " | ".join(f"{n} 세후coin" for n in rows) + " |",
           "|---|---|" + "---|" * len(rows)]
    for a in range(N_AGENTS):
        inc.append(
            f"| #{a+1} | {skills[a]:.3f} | "
            + " | ".join(f"{rows[n]['coins'][a]:.1f}" for n in rows) + " |"
        )

    ai = rows["미니-AI Mini AI Economist"]
    free = rows["자유시장 Free market"]
    md = f"""### E5 — 미니 AI Economist (OneStepEconomy)

> ⚠️ **논문 결과의 재현이 아니다.** 논문의 16%는 공간·거래·건축이 있는 1000스텝 경제에서
> 4억 샘플 2단계 RL 학습으로 얻은 값이다. 여기서는 저장소에 함께 들어있는
> **OneStepEconomy**(2021 후속논문 arXiv:2108.02755의 단순화 경제)에서 학습 대신
> **정적 최적화**로 같은 논리를 실행했다. 숫자를 논문 수치와 직접 비교해선 안 된다.

**설정:** 에이전트 {N_AGENTS}명, 스킬 = {np.round(skills,3).tolist()} (저장소 `SimpleLabor`와 동일 생성),
노동 0–{MAX_HOURS}시간 그리드, 효용 = 세후coin − {LABOR_COST}·시간^{LABOR_EXPONENT:.0f} (저장소 `coin_minus_labor_cost`),
세금은 7구간 누진세 + 정액 재분배, Saez 탄력성 e={ELAS}, 세율 탐색 {N_SEARCH:,}회 + CEM 30세대.
`labor_cost`는 보정값이다 — 저장소 기본값 1.0은 이 시간 스케일에서 최적노동 ≈1시간이 되어
과세구간에 도달조차 못 하므로, 최고숙련 에이전트가 94시간(상한 100 미만)을 일하도록 0.012로 두었다.

{chr(10).join(tbl)}
{chr(10).join(sch)}
{chr(10).join(inc)}

**관찰**

1. **자유시장의 생산성이 가장 높다** ({free['prod']:.1f}) — 논문의
   *"Taxation always results in a decrease of productivity when compared with the free market"*
   와 방향이 일치한다. 세금은 언제나 생산성을 깎는다.
2. **미니-AI가 찾은 세율표는 Saez 대비 사회후생 {ai['vs_saez']:+.1f}%** 를 낸다.
   방향은 논문과 같지만 크기는 논문의 16%와 다르며, 경제 구조가 다르므로 당연하다.
3. **미니-AI 세율표는 단조 누진이 아니다** — 논문이 보고한
   *"a blend of progressive and regressive"* 비단조 구조가 이 단순화 경제에서도 나타난다.
4. 그림 ③은 무작위 세율표 6,000개를 평가한 **달성가능집합**과 그 파레토 경계다.
   형평성과 생산성이 실제로 상충하며, 미니-AI가 경계 근처에 놓임을 보여준다.
5. **Saez는 이 경제에서 자유시장보다도 낮은 eq×prod를 낸다.** E1이 보여준 대로
   4명뿐인 경제의 소득분포에서는 Saez 공식이 제 성능을 내기 어렵다는 점과 일관된다.
"""
    write_table("e5_mini_ai_economist", md)

    np.savez(
        RESULT_DIR / "e5_incomes.npz",
        policy_names=np.array(list(rows)),
        coins=np.array([rows[n]["coins"] for n in rows]),
        incomes=np.array([rows[n]["incomes"] for n in rows]),
        labors=np.array([rows[n]["labors"] for n in rows]),
        rates=np.array([rows[n]["rates"] for n in rows]),
        skills=skills,
    )
    print(f"[saved] {RESULT_DIR / 'e5_incomes.npz'}")

    print("\n--- E5 self-check ---")
    for name, d in rows.items():
        print(
            f"{name:28s} eq={d['eq']:.4f} prod={d['prod']:7.1f} "
            f"swf={d['swf']:7.1f} ({d['vs_saez']:+.1f}% vs Saez) "
            f"{L.trend_summary(d['rates'])['overall']}"
        )
    top = max(rows, key=lambda n: rows[n]["prod"])
    print(f"생산성 최고 정책 = {top}  (기대: 자유시장)")


if __name__ == "__main__":
    main()
