"""E2 — Saez 베이스라인은 '넣어준 탄력성' 하나에 얼마나 흔들리는가.

검증 대상:
  - 논문은 Saez 적용 시 일정 탄력성을 가정한다 (L1262-1267,
    "Following Gruber and Saez [2002], we assume constant tax elasticity").
  - 그러면서 스스로 인정한다 (L1256): 탄력성 추정은 "highly non-trivial".

논지: AI가 Saez를 이긴 폭의 일부는 'Saez 이론이 틀려서'가 아니라
      'Saez 공식에 넣어준 입력값 선택' 때문일 수 있다. 그 민감도를 정량화한다.

대응 슬라이드: S23 (비교는 공정했나)
"""

import numpy as np

import aie_lib as L
from compat import save, setup_matplotlib, write_table

ELAS_GRID = [0.2, 0.4, 0.6, 0.8, 1.0, 1.5]
MEAN_INCOME = 150.0
N_POP = 4000
SEED = 0


def main():
    plt = setup_matplotlib()
    comp = L.make_tax_component(tax_model="saez", saez_fixed_elas=0.5)

    # 분포는 고정 — 논문 시뮬레이션과 같은 로그정규형
    incomes = L.lognormal_incomes(n=N_POP, mean=MEAN_INCOME, sigma=0.7, seed=SEED)

    schedules = {e: L.saez_schedule(comp, incomes, e) for e in ELAS_GRID}
    labels = L.bracket_labels(comp)
    x = np.arange(len(labels))

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    cmap = plt.get_cmap("viridis")

    # --- (좌) 세율표 팬 차트 ---
    ax = axes[0]
    for i, e in enumerate(ELAS_GRID):
        ax.step(
            x, schedules[e] * 100, where="mid", lw=2.2,
            color=cmap(i / max(1, len(ELAS_GRID) - 1)), label=f"e = {e}",
        )
    ax.step(
        x, L.US_FEDERAL_2018 * 100, where="mid", lw=1.5, ls="--", color="crimson",
        label="미 연방 2018 US Federal",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=8)
    ax.set_xlabel("소득 구간 Income bracket (coin)")
    ax.set_ylabel("한계세율 Marginal tax rate (%)")
    ax.set_title("① 탄력성 e만 바꿨을 때의 Saez 세율표\n(소득분포는 로그정규로 고정)")
    ax.legend(fontsize=8, ncol=2)
    ax.grid(alpha=0.3)

    # --- (우) 평균세율·최고구간세율의 민감도 ---
    ax = axes[1]
    means = np.array([schedules[e].mean() for e in ELAS_GRID]) * 100
    tops = np.array([schedules[e][-1] for e in ELAS_GRID]) * 100
    ax.plot(ELAS_GRID, means, "o-", lw=2.4, ms=7, color="#1f77b4",
            label="평균 한계세율 Mean rate")
    ax.plot(ELAS_GRID, tops, "s-", lw=2.4, ms=7, color="#d62728",
            label="최고구간 세율 Top-bracket rate")
    ax.set_xlabel("가정한 탄력성 Assumed elasticity  e")
    ax.set_ylabel("세율 Tax rate (%)")
    ax.set_title(
        "② 입력값 하나가 베이스라인을 얼마나 움직이나\n"
        f"평균세율 {means.min():.0f}% → {means.max():.0f}% ({means.max()-means.min():.0f}%p 폭)"
    )
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    ax.set_ylim(0, max(means.max(), tops.max()) * 1.25)

    fig.suptitle(
        "E2 — '비교 대상' Saez 베이스라인은 가정한 탄력성에 크게 좌우된다  "
        "| The Saez baseline hinges on one assumed elasticity",
        fontsize=12.5, y=1.03,
    )
    save(fig, "e2_saez_elasticity")

    # --- 표 ---
    rows = [
        "| 소득 구간 (coin) | " + " | ".join(f"e={e}" for e in ELAS_GRID) + " |",
        "|---|" + "---|" * len(ELAS_GRID),
    ]
    for i, lab in enumerate(labels):
        rows.append(
            f"| {lab} | "
            + " | ".join(f"{schedules[e][i]*100:.1f}%" for e in ELAS_GRID)
            + " |"
        )
    rows.append("| **평균 한계세율** | " + " | ".join(f"**{m:.1f}%**" for m in means) + " |")
    rows.append("| 최고구간 세율 | " + " | ".join(f"{t:.1f}%" for t in tops) + " |")
    table = "\n".join(rows)

    md = f"""### E2 — Saez 베이스라인의 탄력성 민감도

**설정:** 소득분포는 로그정규(σ=0.7, 평균 {MEAN_INCOME:.0f} coin, N={N_POP}, seed={SEED})로 **고정**하고
탄력성 e만 {ELAS_GRID[0]}~{ELAS_GRID[-1]}로 스윕. 저장소의 `saez_fixed_elas` 경로와 동일한 계산.

{table}

**결과:** 탄력성 가정 하나만 바꿔도 평균 한계세율이
**{means.min():.1f}% → {means.max():.1f}% ({means.max()-means.min():.1f}%p)** 범위로 움직인다.
논문은 이 값을 상수로 가정했고(L1262–1267), 스스로 그 추정이 "highly non-trivial"이라 인정했다(L1256).

**발표에서 할 말:** "AI가 Saez를 16% 이겼다"의 상당 부분이 *Saez 공식이 틀려서*가 아니라
*Saez 공식에 넣어준 입력값이 이 경제에 맞지 않아서*일 수 있다. 게다가 이 시뮬레이션의
에이전트는 조세회피를 학습하므로 탄력성은 애초에 상수가 아니다.
"""
    write_table("e2_saez_elasticity", md)

    print("\n--- E2 self-check ---")
    for e in ELAS_GRID:
        s = L.trend_summary(schedules[e])
        print(
            f"e={e}: mean={s['mean_rate']*100:5.1f}%  "
            f"top={s['top_rate']*100:5.1f}%  {s['overall']}"
        )
    print(f"평균세율 변동폭: {means.max()-means.min():.1f}%p")


if __name__ == "__main__":
    main()
